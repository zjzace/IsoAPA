"""
Standalone annotation script — resumes Tier 1 annotation from where ETL left off.
Skips APA sites that already have pas_motif AND apa_type set.

Usage:
    python -m app.services.annotate_only
    python -m app.services.annotate_only --data-dir /path/to/data
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import (
    SessionLocal,
    Species,
    Gene,
    Transcript,
    APASite,
)
from app.services.pas_annotator import PASAnnotator
from app.services.apa_classifier import APATypeClassifier

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


def get_gtf_path(data_dir: str, species_folder: str) -> str:
    species_dir = os.path.join(data_dir, species_folder, "reference")
    if not os.path.exists(species_dir):
        return None
    for f in os.listdir(species_dir):
        if f.endswith(".gtf") or f.endswith(".gff3"):
            return os.path.join(species_dir, f)
    return None


def get_fasta_path(data_dir: str, species_folder: str) -> str:
    species_dir = os.path.join(data_dir, species_folder, "reference")
    if not os.path.exists(species_dir):
        return None
    for f in os.listdir(species_dir):
        if f.endswith(".fa") or f.endswith(".fasta") or f.endswith(".fna"):
            if not f.endswith(".fai"):
                return os.path.join(species_dir, f)
    return None


def annotate(data_dir: str):
    db = SessionLocal()
    try:
        for species_folder in os.listdir(data_dir):
            species_path = os.path.join(data_dir, species_folder)
            if not os.path.isdir(species_path) or species_folder.startswith("."):
                continue
            if species_folder == "reference":
                continue

            gtf_path = get_gtf_path(data_dir, species_folder)
            fasta_path = get_fasta_path(data_dir, species_folder)

            if not gtf_path or not fasta_path:
                print(f"Skipping {species_folder}: missing GTF or FASTA")
                continue

            print(f"\nAnnotating {species_folder}...")
            print(f"  GTF:   {os.path.basename(gtf_path)}")
            print(f"  FASTA: {os.path.basename(fasta_path)}")

            species_info = SPECIES_MAP.get(species_folder, {"name": species_folder})
            species = (
                db.query(Species).filter(Species.name == species_info["name"]).first()
            )
            if not species:
                print(f"  Species '{species_info['name']}' not found in DB — skipping")
                continue

            apa_sites = (
                db.query(APASite)
                .join(Transcript)
                .join(Gene)
                .filter(APASite.species_id == species.id)
                .filter((APASite.pas_motif == None) | (APASite.apa_type == None))
                .all()
            )

            total = db.query(APASite).filter(APASite.species_id == species.id).count()
            print(
                f"  {total - len(apa_sites)} already annotated, {len(apa_sites)} remaining"
            )

            if len(apa_sites) == 0:
                print(f"  ✓ All sites already annotated for {species_folder}")
                continue

            print(f"  Initializing annotators (this may take a minute)...")
            pas_annotator = PASAnnotator(fasta_path)
            apa_classifier = APATypeClassifier(gtf_path)

            batch_size = 200
            annotated_count = 0

            for i, apa_site in enumerate(apa_sites):
                transcript = apa_site.transcript
                gene = transcript.gene

                pas_full = pas_annotator.annotate_site(
                    chrom=gene.chromosome,
                    position=apa_site.site_position,
                    strand=gene.strand,
                )
                search_level = pas_full.get("search_level", "none")

                if search_level == "hexamer":
                    h = pas_full["hexamer"]
                    apa_site.pas_motif = h["motif"]
                    apa_site.pas_position = h["position"]
                    apa_site.pas_type = h["motif_type"]
                    apa_site.pas_confidence = h["confidence"]
                elif search_level in ("upstream", "downstream"):
                    hits = (
                        pas_full.get("upstream_motifs")
                        or pas_full.get("downstream_motifs")
                        or []
                    )
                    first = hits[0] if hits else {}
                    apa_site.pas_motif = first.get("motif")
                    apa_site.pas_position = first.get("offset")
                    apa_site.pas_type = "other"
                    apa_site.pas_confidence = "low"
                else:
                    apa_site.pas_motif = None
                    apa_site.pas_position = None
                    apa_site.pas_type = None
                    apa_site.pas_confidence = None

                apa_result = apa_classifier.classify_apa_site(
                    transcript_id=transcript.transcript_id,
                    position=apa_site.site_position,
                    strand=gene.strand,
                )
                apa_site.apa_type = apa_result["apa_type"]
                apa_site.apa_region = apa_result["region"]
                apa_site.apa_confidence = apa_result["confidence"]

                annotated_count += 1

                if (i + 1) % batch_size == 0:
                    db.commit()
                    pct = (i + 1) / len(apa_sites) * 100
                    print(
                        f"    [{pct:.1f}%] Annotated {i + 1}/{len(apa_sites)} remaining sites..."
                    )

            db.commit()
            print(f"  ✓ Annotated {annotated_count} sites for {species_folder}")

        print("\n✓ Annotation complete!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    default_data_dir = os.path.join(project_root, "data")

    parser = argparse.ArgumentParser(description="Resume Tier 1 APA site annotation")
    parser.add_argument("--data-dir", default=default_data_dir, help="Data directory")
    args = parser.parse_args()

    annotate(args.data_dir)
