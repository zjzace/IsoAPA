import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
from app.models.database import (
    SessionLocal,
    Species,
    Sample,
    Gene,
    Transcript,
    APASite,
    init_db,
)

SPECIES_MAP = {
    "homo_sapiens": {
        "name": "Human",
        "latin_name": "Homo sapiens",
        "assembly": "GRCh38",
    },
    "mus_musculus": {
        "name": "Mouse",
        "latin_name": "Mus musculus",
        "assembly": "GRCm39",
    },
    "rattus_norvegicus": {
        "name": "Rat",
        "latin_name": "Rattus norvegicus",
        "assembly": "rn6",
    },
    "danio_rerio": {
        "name": "Zebrafish",
        "latin_name": "Danio rerio",
        "assembly": "GRCz11",
    },
}

DATA_DIR = None

BATCH_SIZE = 5000


def _unified_file_path(species_folder: str) -> str | None:
    species_dir = os.path.join(DATA_DIR, species_folder)
    for fname in os.listdir(species_dir):
        if fname.endswith("_unified_apa_sites.txt") or fname.endswith(
            "_unified_apa_sites.tsv"
        ):
            return os.path.join(species_dir, fname)
    return None


def _get_or_create_species(db, species_folder: str):
    info = SPECIES_MAP.get(
        species_folder,
        {
            "name": species_folder,
            "latin_name": species_folder,
            "assembly": None,
        },
    )
    obj = db.query(Species).filter(Species.name == info["name"]).first()
    if not obj:
        obj = Species(
            name=info["name"],
            latin_name=info["latin_name"],
            assembly=info.get("assembly"),
        )
        db.add(obj)
        db.flush()
    return obj


def _anno_file_path(species_path: str) -> str | None:
    for fname in os.listdir(species_path):
        if fname.endswith("_unified_apa.anno.txt"):
            return os.path.join(species_path, fname)
    return None


def _load_anno_index(species_path: str, species_folder: str) -> dict:
    ann_path = _anno_file_path(species_path)
    if not ann_path:
        print(
            f"  No .anno.txt file found for {species_folder} — annotation columns will be NULL"
        )
        return {}
    print(f"  Loading annotation index: {os.path.basename(ann_path)}")
    index: dict = {}
    with open(ann_path) as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            uid = row["unified_ID"].strip()
            pas_pos = row.get("pas_position", "").strip()
            c_start = row.get("cluster_start", "").strip()
            c_end = row.get("cluster_end", "").strip()
            index[uid] = {
                "sequence": row.get("sequence", "").strip() or None,
                "pas_motif": row.get("pas_motif", "").strip() or None,
                "pas_position": int(pas_pos) if pas_pos else None,
                "pas_type": row.get("pas_type", "").strip() or None,
                "search_level": row.get("search_level", "").strip() or None,
                "cluster_start": int(c_start) if c_start else None,
                "cluster_end": int(c_end) if c_end else None,
            }
    print(f"  Annotation index: {len(index):,} entries")
    return index


def ingest_data(data_dir: str = None):
    global DATA_DIR
    DATA_DIR = data_dir or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data",
    )

    db = SessionLocal()
    try:
        print("Initializing database...")
        init_db()

        total_species = total_samples = total_genes = total_transcripts = (
            total_apa_sites
        ) = 0

        for species_folder in sorted(os.listdir(DATA_DIR)):
            species_path = os.path.join(DATA_DIR, species_folder)
            if not os.path.isdir(species_path) or species_folder.startswith("."):
                continue

            unified_path = _unified_file_path(species_folder)
            if not unified_path:
                print(f"  Skipping {species_folder}: no unified APA sites file found")
                continue

            print(f"\nProcessing species: {species_folder}")
            print(f"  File: {os.path.basename(unified_path)}")

            species_obj = _get_or_create_species(db, species_folder)
            species_id = species_obj.id
            total_species += 1

            clusters: dict = {}
            sample_map: dict[str, str] = {}

            print("  Pass 1: reading file and aggregating clusters...")
            row_count = 0
            with open(unified_path, "r") as fh:
                reader = csv.DictReader(fh, delimiter="\t")
                for row in reader:
                    row_count += 1
                    if row_count % 500_000 == 0:
                        print(f"    ... {row_count:,} rows read")

                    transcript_id = row["transcript_id"]
                    unified_id = row["unified_ID"]
                    cluster_key = (transcript_id, unified_id)

                    entry = {
                        "sample_name": row["sample"],
                        "sample_type": row["sample_attribute"],
                        "original_site_position": int(row["original_site_position"]),
                        "site_count": int(row["site_count"]),
                        "site_abundance": float(row["site_abundance"]),
                    }

                    if cluster_key not in clusters:
                        clusters[cluster_key] = {
                            "row": row,
                            "sample_entries": [entry],
                        }
                    else:
                        clusters[cluster_key]["sample_entries"].append(entry)

                    sample_map[row["sample"]] = row["sample_attribute"]

            print(
                f"  Rows: {row_count:,} | Clusters: {len(clusters):,} | "
                f"Samples: {len(sample_map)}"
            )

            print("  Pass 2: inserting samples...")
            sample_id_cache: dict[str, int] = {}
            for sname, stype in sample_map.items():
                obj = (
                    db.query(Sample)
                    .filter(Sample.name == sname, Sample.species_id == species_id)
                    .first()
                )
                if not obj:
                    obj = Sample(name=sname, sample_type=stype, species_id=species_id)
                    db.add(obj)
                    db.flush()
                sample_id_cache[sname] = obj.id
            db.commit()
            total_samples += len(sample_id_cache)

            print("  Pass 3: inserting genes and transcripts...")
            gene_id_cache: dict[str, int] = {}
            transcript_id_cache: dict[str, int] = {}

            for (transcript_id_str, unified_id), cluster in clusters.items():
                row = cluster["row"]
                gene_id_str = row["gene_id"]

                if gene_id_str not in gene_id_cache:
                    obj = db.query(Gene).filter(Gene.gene_id == gene_id_str).first()
                    if not obj:
                        obj = Gene(
                            gene_id=gene_id_str,
                            gene_name=row["gene_name"],
                            chromosome=row["chromosome"],
                            strand=row["strand"],
                        )
                        db.add(obj)
                        db.flush()
                    gene_id_cache[gene_id_str] = obj.id

                gene_db_id = gene_id_cache[gene_id_str]

                if transcript_id_str not in transcript_id_cache:
                    obj = (
                        db.query(Transcript)
                        .filter(Transcript.transcript_id == transcript_id_str)
                        .first()
                    )
                    if not obj:
                        obj = Transcript(
                            transcript_id=transcript_id_str, gene_id=gene_db_id
                        )
                        db.add(obj)
                        db.flush()
                    transcript_id_cache[transcript_id_str] = obj.id

            db.commit()
            total_genes += len(gene_id_cache)
            total_transcripts += len(transcript_id_cache)
            print(
                f"  Genes: {len(gene_id_cache):,} | Transcripts: {len(transcript_id_cache):,}"
            )

            print("  Pass 4: inserting APA sites in batches...")
            anno_index = _load_anno_index(species_path, species_folder)
            batch = []
            inserted = 0

            for (transcript_id_str, unified_id), cluster in clusters.items():
                row = cluster["row"]
                sample_entries = cluster["sample_entries"]
                transcript_db_id = transcript_id_cache[transcript_id_str]

                total_count = sum(e["site_count"] for e in sample_entries)
                mean_abundance = (
                    sum(e["site_abundance"] for e in sample_entries)
                    / len(sample_entries)
                    if sample_entries
                    else 0.0
                )

                ann = anno_index.get(unified_id, {})
                batch.append(
                    {
                        "unified_id": unified_id,
                        "transcript_id": transcript_db_id,
                        "species_id": species_id,
                        "mode_site_position": int(row["mode_site_position"]),
                        "transcript_biotype": row.get("transcript_biotype") or None,
                        "site_count": total_count,
                        "site_abundance": mean_abundance,
                        "sample_data": json.dumps(sample_entries),
                        "sequence": ann.get("sequence"),
                        "pas_motif": ann.get("pas_motif"),
                        "pas_position": ann.get("pas_position"),
                        "pas_type": ann.get("pas_type"),
                        "search_level": ann.get("search_level"),
                        "cluster_start": ann.get("cluster_start"),
                        "cluster_end": ann.get("cluster_end"),
                    }
                )

                if len(batch) >= BATCH_SIZE:
                    db.bulk_insert_mappings(APASite, batch)
                    db.commit()
                    inserted += len(batch)
                    batch = []
                    print(f"    ... {inserted:,} APA sites inserted")

            if batch:
                db.bulk_insert_mappings(APASite, batch)
                db.commit()
                inserted += len(batch)

            total_apa_sites += inserted
            print(f"  APA sites inserted: {inserted:,}")

        print(f"\n=== Summary ===")
        print(f"Species:     {total_species}")
        print(f"Samples:     {total_samples}")
        print(f"Genes:       {total_genes}")
        print(f"Transcripts: {total_transcripts}")
        print(f"APA Sites:   {total_apa_sites}")
        print("Done.")

    except Exception as exc:
        db.rollback()
        import traceback

        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    default_data_dir = os.path.join(project_root, "data")

    parser = argparse.ArgumentParser(
        description="Ingest APA sites data (unified format)"
    )
    parser.add_argument("--data-dir", default=default_data_dir, help="Data directory")
    args = parser.parse_args()

    ingest_data(args.data_dir)
