import json
import os
from datetime import datetime, timezone

from sqlalchemy import func, inspect

from app.models.database import (
    APASite,
    APASiteSample,
    Gene,
    Sample,
    SessionLocal,
    Species,
    Transcript,
)


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATS_CACHE_FILE = os.path.join(BACKEND_DIR, "stats_cache.json")


def _format_sample_name(name: str) -> str:
    return str(name or "").replace("_", " ")


def _format_species_name(name: str, latin_name: str | None = None) -> str:
    formal_names = {
        "Human": "Homo sapiens",
        "Mouse": "Mus musculus",
    }
    if name in formal_names:
        return formal_names[name]

    preferred = latin_name if latin_name and latin_name != name else name
    return str(preferred or "").replace("_", " ")


def _multiplicity_bucket(count: int) -> str:
    if count >= 5:
        return "5+"
    return str(max(count, 0))


def build_stats_cache(output_path: str = STATS_CACHE_FILE) -> dict:
    db = SessionLocal()
    try:
        has_sample_observations = inspect(db.bind).has_table("apa_site_samples")
        total_genes = db.query(Gene).count()
        total_transcripts = db.query(Transcript).count()
        total_apa_sites = db.query(func.count(func.distinct(APASite.unified_id))).scalar() or 0
        total_samples = db.query(Sample).count()
        total_species = db.query(Species).count()

        species_lookup = {
            s.name: s for s in db.query(Species).all()
        }
        distinct_site_count = func.count(func.distinct(APASite.unified_id))

        apa_by_species = (
            db.query(Species.name, distinct_site_count.label("count"))
            .select_from(APASite)
            .join(Species, APASite.species_id == Species.id)
            .group_by(Species.name)
            .all()
        )

        apa_by_chromosome = (
            db.query(Gene.chromosome, func.count(APASite.id).label("count"))
            .select_from(APASite)
            .join(Transcript, APASite.transcript_id == Transcript.id)
            .join(Gene, Transcript.gene_id == Gene.id)
            .filter(Gene.chromosome.isnot(None))
            .group_by(Gene.chromosome)
            .order_by(Gene.chromosome)
            .all()
        )

        apa_by_strand = (
            db.query(Gene.strand, func.count(APASite.id).label("count"))
            .select_from(APASite)
            .join(Transcript, APASite.transcript_id == Transcript.id)
            .join(Gene, Transcript.gene_id == Gene.id)
            .filter(Gene.strand.isnot(None))
            .group_by(Gene.strand)
            .all()
        )

        top_genes = (
            db.query(
                Gene.gene_name,
                Gene.gene_id,
                Species.name.label("species"),
                distinct_site_count.label("apa_count"),
                Gene.id,
            )
            .select_from(APASite)
            .join(Transcript, APASite.transcript_id == Transcript.id)
            .join(Gene, Transcript.gene_id == Gene.id)
            .join(Species, Gene.species_id == Species.id)
            .group_by(Gene.gene_name, Gene.gene_id, Species.name, Gene.id)
            .order_by(distinct_site_count.desc())
            .limit(20)
            .all()
        )

        count_per_transcript = (
            db.query(Transcript.id, func.count(func.distinct(APASite.unified_id)).label("apa_count"))
            .outerjoin(APASite, APASite.transcript_id == Transcript.id)
            .group_by(Transcript.id)
            .subquery()
        )
        avg_result = db.query(func.avg(count_per_transcript.c.apa_count)).scalar()
        avg_apa_per_transcript = float(avg_result) if avg_result else 0

        multiplicity_rows = db.query(count_per_transcript.c.apa_count).all()
        multiplicity_buckets = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5+": 0}
        multi_count = 0
        single_count = 0
        for (count,) in multiplicity_rows:
            count = int(count or 0)
            multiplicity_buckets[_multiplicity_bucket(count)] += 1
            if count == 1:
                single_count += 1
            if count >= 2:
                multi_count += 1
        multiplicity_total = len(multiplicity_rows)

        sample_counts = {}
        normalized_sample_rows = []
        if has_sample_observations:
            normalized_sample_rows = (
                db.query(Sample.name, func.count(APASiteSample.id))
                .join(APASiteSample, APASiteSample.sample_id == Sample.id)
                .group_by(Sample.name)
                .all()
            )
        if normalized_sample_rows:
            sample_counts = {
                _format_sample_name(sample_name): count
                for sample_name, count in normalized_sample_rows
            }
        else:
            for (sample_data,) in db.query(APASite.sample_data).filter(APASite.sample_data.isnot(None)).all():
                try:
                    for sd in json.loads(sample_data or "[]"):
                        sample_name = sd.get("sample_name") or "Unknown"
                        display = _format_sample_name(sample_name)
                        sample_counts[display] = sample_counts.get(display, 0) + 1
                except (TypeError, json.JSONDecodeError):
                    continue

        detailed = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_genes": total_genes,
            "total_transcripts": total_transcripts,
            "total_apa_sites": total_apa_sites,
            "total_samples": total_samples,
            "total_species": total_species,
            "avg_apa_per_transcript": round(avg_apa_per_transcript, 2),
            "avg_isoforms_per_gene": round(total_transcripts / total_genes, 2) if total_genes else 0,
            "apa_sites_by_species": [
                {
                    "name": name,
                    "display_name": _format_species_name(
                        name, species_lookup.get(name).latin_name if species_lookup.get(name) else None
                    ),
                    "count": count,
                }
                for name, count in apa_by_species
            ],
            "apa_sites_by_sample": [
                {"name": name, "count": count}
                for name, count in sorted(sample_counts.items(), key=lambda item: item[1], reverse=True)
            ],
            "apa_sites_by_chromosome": [
                {"chromosome": chromosome, "count": count}
                for chromosome, count in apa_by_chromosome
            ],
            "apa_sites_by_strand": [
                {"strand": strand, "count": count}
                for strand, count in apa_by_strand
            ],
            "top_genes_by_apa": [
                {
                    "gene_name": gene_name,
                    "gene_id": gene_id,
                    "species": species,
                    "apa_count": apa_count,
                    "gene_db_id": gene_db_id,
                }
                for gene_name, gene_id, species, apa_count, gene_db_id in top_genes
            ],
            "apa_site_multiplicity": {
                "buckets": multiplicity_buckets,
                "total": multiplicity_total,
                "single_site_count": single_count,
                "multi_site_count": multi_count,
                "pct_single_site": round((single_count / multiplicity_total) * 100, 1) if multiplicity_total else 0,
                "pct_multi_site": round((multi_count / multiplicity_total) * 100, 1) if multiplicity_total else 0,
            },
        }

        basic = {
            "total_genes": total_genes,
            "total_transcripts": total_transcripts,
            "total_apa_sites": total_apa_sites,
            "total_cell_lines": total_samples,
            "total_species": total_species,
            "apa_sites_by_species": detailed["apa_sites_by_species"],
            "apa_sites_by_cell_line": detailed["apa_sites_by_sample"],
            "apa_site_multiplicity": detailed["apa_site_multiplicity"],
            "apa_sites_per_transcript": [],
        }

        payload = {"basic": basic, "detailed": detailed}
        tmp_path = output_path + ".tmp"
        with open(tmp_path, "w") as fh:
            json.dump(payload, fh, separators=(",", ":"))
        os.replace(tmp_path, output_path)
        return payload
    finally:
        db.close()


if __name__ == "__main__":
    stats = build_stats_cache()
    detailed = stats["detailed"]
    print(
        "Stats cache ready: "
        f"{detailed['total_species']:,} species, "
        f"{detailed['total_transcripts']:,} transcripts, "
        f"{detailed['total_apa_sites']:,} PA sites"
    )
