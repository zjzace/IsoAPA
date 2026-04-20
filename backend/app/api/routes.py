from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List, Optional
import os
import json
import csv
import io
import re
from app.models.database import get_db, Gene, Transcript, APASite, Species, Sample
from app.schemas.schemas import (
    SearchResult,
    SearchResponse,
    DashboardStats,
    LocusDetail,
    APASiteWithDetails,
    GeneDetail,
)

router = APIRouter()

_BED12_INDEX_CACHE: dict = {}


def _load_bed12_index(bed12_path: str) -> dict:
    if bed12_path in _BED12_INDEX_CACHE:
        return _BED12_INDEX_CACHE[bed12_path]
    idx_path = bed12_path + ".bidx"
    if not os.path.exists(idx_path):
        return {}
    with open(idx_path, "r") as f:
        idx = json.load(f)
    _BED12_INDEX_CACHE[bed12_path] = idx
    return idx


def _fetch_bed12_record(bed12_path: str, transcript_id: str) -> dict | None:
    idx = _load_bed12_index(bed12_path)
    span = idx.get(transcript_id)
    if not span:
        return None
    offset, length = span
    with open(bed12_path, "rb") as f:
        f.seek(offset)
        line = f.read(length).decode("utf-8", errors="replace").strip()
    fields = line.split("\t")
    if len(fields) < 12:
        return None
    chrom_start = int(fields[1])
    thick_start = int(fields[6])
    thick_end = int(fields[7])
    block_sizes = [int(x) for x in fields[10].rstrip(",").split(",") if x]
    block_starts = [int(x) for x in fields[11].rstrip(",").split(",") if x]
    return {
        "chrom": fields[0],
        "chrom_start": chrom_start,
        "strand": fields[5],
        "thick_start": thick_start,
        "thick_end": thick_end,
        "block_sizes": block_sizes,
        "block_starts": block_starts,
    }


def _parse_bed12_structure(rec: dict) -> dict:
    cs = rec["chrom_start"]
    ts, te = rec["thick_start"], rec["thick_end"]
    has_cds = ts < te
    exons, cds, utrs = [], [], []

    for bstart_rel, bsize in zip(rec["block_starts"], rec["block_sizes"]):
        b_start = cs + bstart_rel
        b_end = b_start + bsize
        ex_s, ex_e = b_start + 1, b_end

        exons.append((ex_s, ex_e))

        if not has_cds:
            utrs.append((ex_s, ex_e))
            continue

        cds_s0 = max(b_start, ts)
        cds_e0 = min(b_end, te)

        if cds_s0 < cds_e0:
            cds.append((cds_s0 + 1, cds_e0))
            if b_start < ts:
                utrs.append((ex_s, ts))
            if b_end > te:
                utrs.append((te + 1, ex_e))
        else:
            utrs.append((ex_s, ex_e))

    return {
        "chrom": rec["chrom"],
        "strand": rec["strand"],
        "exons": exons,
        "cds": cds,
        "utrs": utrs,
    }


DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data"
)

SPECIES_FOLDER_MAP = {
    "Human": "homo_sapiens",
    "Mouse": "mus_musculus",
    "Rat": "rattus_norvegicus",
    "Zebrafish": "danio_rerio",
}


def get_species_ref_path(species_name: str, file_type: str = "bed12") -> str:
    """Get reference file path for a species."""
    species_folder = SPECIES_FOLDER_MAP.get(species_name)
    if not species_folder:
        return None

    ref_dir = os.path.join(DATA_DIR, species_folder, "reference")
    if not os.path.exists(ref_dir):
        return None

    for f in os.listdir(ref_dir):
        if file_type == "fasta" and (
            f.endswith(".fa") or f.endswith(".fasta") or f.endswith(".fna")
        ):
            return os.path.join(ref_dir, f)
        elif file_type == "bed12" and f.endswith(".bed") and not f.endswith(".bidx"):
            return os.path.join(ref_dir, f)

    return None


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    total_genes = db.query(Gene).count()
    total_transcripts = db.query(Transcript).count()
    total_apa_sites = db.query(APASite).count()
    total_samples = db.query(Sample).count()
    total_species = db.query(Species).count()

    apa_by_species = (
        db.query(Species.name, func.count(APASite.id).label("count"))
        .join(APASite, APASite.species_id == Species.id)
        .group_by(Species.name)
        .all()
    )

    apa_per_transcript = (
        db.query(Transcript.transcript_id, func.count(APASite.id).label("count"))
        .join(APASite, APASite.transcript_id == Transcript.id)
        .group_by(Transcript.transcript_id)
        .all()
    )

    return DashboardStats(
        total_genes=total_genes,
        total_transcripts=total_transcripts,
        total_apa_sites=total_apa_sites,
        total_cell_lines=total_samples,
        total_species=total_species,
        apa_sites_by_species=[{"name": s[0], "count": s[1]} for s in apa_by_species],
        apa_sites_by_cell_line=[],
        apa_sites_per_transcript=[
            {"transcript_id": t[0], "count": t[1]} for t in apa_per_transcript
        ],
    )


@router.get("/search", response_model=SearchResponse)
def search_transcripts(
    gene_name: Optional[str] = None,
    transcript_id: Optional[str] = None,
    gene_id: Optional[str] = None,
    sample: Optional[str] = None,
    species: Optional[str] = None,
    chromosome: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search for transcripts with filters."""
    query = (
        db.query(
            Transcript.transcript_id,
            Gene.gene_id,
            Gene.gene_name,
            Gene.chromosome,
            Gene.strand,
            func.count(APASite.id).label("apa_site_count"),
            Species.name.label("species"),
            Gene.id.label("gene_db_id"),
        )
        .join(Gene)
        .join(APASite)
        .join(Species)
    )

    if gene_name:
        query = query.filter(Gene.gene_name.ilike(f"%{gene_name}%"))
    if transcript_id:
        query = query.filter(Transcript.transcript_id.ilike(f"%{transcript_id}%"))
    if gene_id:
        query = query.filter(Gene.gene_id.ilike(f"%{gene_id}%"))
    if sample:
        query = query.filter(APASite.sample_data.ilike(f"%{sample}%"))
    if species:
        query = query.filter(Species.name.ilike(f"%{species}%"))
    if chromosome:
        query = query.filter(Gene.chromosome.ilike(f"%{chromosome}%"))

    _count_subq = query.group_by(
        Transcript.transcript_id,
        Gene.id,
        Gene.gene_id,
        Gene.gene_name,
        Gene.chromosome,
        Gene.strand,
        Species.name,
    ).subquery()
    total_count = db.query(func.count()).select_from(_count_subq).scalar() or 0

    results = (
        query.group_by(
            Transcript.transcript_id,
            Gene.id,
            Gene.gene_id,
            Gene.gene_name,
            Gene.chromosome,
            Gene.strand,
            Species.name,
        )
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    search_results = []
    for r in results:
        apa_sites = (
            db.query(APASite)
            .filter(
                APASite.transcript_id
                == db.query(Transcript)
                .filter(Transcript.transcript_id == r[0])
                .first()
                .id
            )
            .all()
        )
        sample_names = set()
        for asite in apa_sites:
            if asite.sample_data:
                try:
                    import json

                    sample_details = json.loads(asite.sample_data)
                    for sd in sample_details:
                        sample_names.add(sd.get("sample_name", ""))
                except:
                    pass
        search_results.append(
            SearchResult(
                transcript_id=r[0],
                gene_id=r[1],
                gene_name=r[2],
                chromosome=r[3],
                strand=r[4],
                apa_site_count=r[5],
                cell_lines=list(sample_names),
                species=r[6],
                gene_db_id=r[7],
            )
        )

    return SearchResponse(items=search_results, total=total_count)


@router.get("/gene/{gene_db_id}", response_model=GeneDetail)
def get_gene_detail(gene_db_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a gene and all its transcripts with APA sites."""
    gene = db.query(Gene).filter(Gene.id == gene_db_id).first()
    if not gene:
        raise HTTPException(status_code=404, detail="Gene not found")

    transcripts = db.query(Transcript).filter(Transcript.gene_id == gene.id).all()

    species_name = None
    for transcript in transcripts:
        asite = db.query(APASite).filter(APASite.transcript_id == transcript.id).first()
        if asite and asite.species_id:
            sp = db.query(Species).filter(Species.id == asite.species_id).first()
            if sp:
                species_name = sp.name
                break

    transcript_data = []
    for transcript in transcripts:
        apa_sites = (
            db.query(APASite).filter(APASite.transcript_id == transcript.id).all()
        )

        sample_names = set()
        transcript_apa_sites = []
        for asite in apa_sites:
            sample_details = []
            if asite.sample_data:
                try:
                    sample_details = json.loads(asite.sample_data)
                    for sd in sample_details:
                        sample_names.add(sd.get("sample_name", ""))
                except:
                    sample_details = []

            transcript_apa_sites.append(
                {
                    "unified_id": asite.unified_id,
                    "mode_site_position": asite.mode_site_position,
                    "site_abundance": asite.site_abundance,
                    "site_count": asite.site_count,
                    "transcript_biotype": asite.transcript_biotype,
                    "sample_details": sample_details,
                }
            )

        transcript_data.append(
            {
                "transcript_id": transcript.transcript_id,
                "apa_site_count": len(apa_sites),
                "samples": list(sample_names),
                "apa_sites": transcript_apa_sites,
            }
        )

    return GeneDetail(
        id=gene.id,
        gene_id=gene.gene_id,
        gene_name=gene.gene_name,
        chromosome=gene.chromosome,
        strand=gene.strand,
        species=species_name,
        transcripts=transcript_data,
    )


@router.get("/autocomplete")
def autocomplete(
    q: str = Query(..., min_length=1),
    field: str = Query("gene_name"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Autocomplete search suggestions."""
    if field == "gene_name":
        results = (
            db.query(Gene.gene_name)
            .distinct()
            .filter(Gene.gene_name.ilike(f"%{q}%"))
            .limit(limit)
            .all()
        )
        return [{"value": r[0], "type": "gene_name"} for r in results]
    elif field == "gene_id":
        results = (
            db.query(Gene.gene_id)
            .distinct()
            .filter(Gene.gene_id.ilike(f"%{q}%"))
            .limit(limit)
            .all()
        )
        return [{"value": r[0], "type": "gene_id"} for r in results]
    elif field == "transcript_id":
        results = (
            db.query(Transcript.transcript_id)
            .distinct()
            .filter(Transcript.transcript_id.ilike(f"%{q}%"))
            .limit(limit)
            .all()
        )
        return [{"value": r[0], "type": "transcript_id"} for r in results]
    elif field == "sample":
        results = (
            db.query(Sample.name)
            .distinct()
            .filter(Sample.name.ilike(f"%{q}%"))
            .limit(limit)
            .all()
        )
        return [{"value": r[0], "type": "sample"} for r in results]
    elif field == "species":
        results = (
            db.query(Species.name)
            .distinct()
            .filter(Species.name.ilike(f"%{q}%"))
            .limit(limit)
            .all()
        )
        return [{"value": r[0], "type": "species"} for r in results]
    return []


import json
import sys
import os as _os

# Make backend root importable so we can use build_fasta_index helpers
_BACKEND_ROOT = _os.path.dirname(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


@router.get("/transcript/{transcript_id}/structure")
def get_transcript_structure(transcript_id: str, db: Session = Depends(get_db)):
    transcript = (
        db.query(Transcript).filter(Transcript.transcript_id == transcript_id).first()
    )
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    gene = db.query(Gene).filter(Gene.id == transcript.gene_id).first()
    if not gene:
        raise HTTPException(status_code=404, detail="Gene not found")

    apa_site_species = (
        db.query(APASite.species_id)
        .filter(APASite.transcript_id == transcript.id)
        .first()
    )
    if apa_site_species:
        species_obj = (
            db.query(Species).filter(Species.id == apa_site_species[0]).first()
        )
    else:
        species_obj = db.query(Species).filter(Species.name == "Human").first()

    if not species_obj:
        raise HTTPException(status_code=404, detail="Species not found")

    bed12_path = get_species_ref_path(species_obj.name, "bed12")
    if not bed12_path:
        raise HTTPException(
            status_code=404, detail="BED12 file not available for this species"
        )

    try:
        rec = _fetch_bed12_record(bed12_path, transcript_id)
        if not rec:
            raise HTTPException(
                status_code=404, detail="Transcript not found in BED12 index"
            )
        structure = _parse_bed12_structure(rec)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse BED12: {str(e)}")

    return {
        "transcript_id": transcript_id,
        "gene_name": gene.gene_name,
        "gene_id": gene.gene_id,
        "chromosome": structure["chrom"] or gene.chromosome,
        "strand": structure["strand"] or gene.strand,
        "exons": [{"start": s, "end": e} for s, e in structure["exons"]],
        "cds": [{"start": s, "end": e} for s, e in structure["cds"]],
        "utrs": [{"start": s, "end": e} for s, e in structure["utrs"]],
    }


@router.get("/transcript/{transcript_id}", response_model=LocusDetail)
def get_locus_detail(transcript_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a transcript and its APA sites."""
    transcript = (
        db.query(Transcript).filter(Transcript.transcript_id == transcript_id).first()
    )
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    gene = db.query(Gene).filter(Gene.id == transcript.gene_id).first()
    if not gene:
        raise HTTPException(status_code=404, detail="Gene not found")

    apa_sites = db.query(APASite).filter(APASite.transcript_id == transcript.id).all()

    sample_names = set()
    apa_sites_with_details = []
    for asite in apa_sites:
        species = db.query(Species).filter(Species.id == asite.species_id).first()

        sample_details = []
        if asite.sample_data:
            try:
                sample_details = json.loads(asite.sample_data)
                for sd in sample_details:
                    sample_names.add(sd.get("sample_name", ""))
            except:
                sample_details = []

        apa_sites_with_details.append(
            APASiteWithDetails(
                unified_id=str(asite.unified_id),
                transcript_id=int(asite.transcript_id),
                species_id=int(asite.species_id),
                mode_site_position=int(asite.mode_site_position),
                transcript_biotype=asite.transcript_biotype,
                site_count=int(asite.site_count),
                site_abundance=float(asite.site_abundance),
                sample_data=asite.sample_data,
                sequence=asite.sequence,
                pas_motif=asite.pas_motif,
                pas_position=asite.pas_position,
                pas_type=asite.pas_type,
                search_level=asite.search_level,
                id=int(asite.id),
                transcript=transcript,
                species=species,
                sample_details=sample_details,
            )
        )

    samples = list(sample_names)
    chromosomes = [gene.chromosome] if gene.chromosome else []

    return LocusDetail(
        gene=gene,
        transcript=transcript,
        apa_sites=apa_sites_with_details,
        samples=samples,
        chromosomes=chromosomes,
    )


@router.get("/species")
def get_species(db: Session = Depends(get_db)):
    """Get all species."""
    species = db.query(Species).all()
    return [
        {"id": s.id, "name": s.name, "latin_name": s.latin_name, "assembly": s.assembly}
        for s in species
    ]


@router.get("/samples")
def get_samples(species: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all samples (cell lines/tissues), optionally filtered by species."""
    query = db.query(Sample).join(Species)
    if species:
        query = query.filter(Species.name == species)
    samples = query.distinct().all()
    return [{"id": s.id, "name": s.name, "species": s.species.name} for s in samples]


@router.get("/genes")
def get_genes(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get featured/interesting genes."""
    genes = db.query(Gene).offset((page - 1) * limit).limit(limit).all()
    return [
        {
            "id": g.id,
            "gene_id": g.gene_id,
            "gene_name": g.gene_name,
            "chromosome": g.chromosome,
            "strand": g.strand,
        }
        for g in genes
    ]


@router.get("/stats/detailed")
def get_detailed_stats(db: Session = Depends(get_db)):
    """Get detailed database statistics."""
    # Basic counts
    total_genes = db.query(Gene).count()
    total_transcripts = db.query(Transcript).count()
    total_apa_sites = db.query(APASite).count()
    total_samples = db.query(Sample).count()
    total_species = db.query(Species).count()

    # APA sites by species
    apa_by_species = (
        db.query(Species.name, func.count(APASite.id).label("count"))
        .select_from(APASite)
        .join(Species, APASite.species_id == Species.id)
        .group_by(Species.name)
        .all()
    )

    # APA sites by sample - need to parse from sample_data JSON
    # Since Sample table might not have direct relation with APASite, we'll skip this for now
    apa_by_sample = []
    try:
        all_apa_sites = db.query(APASite).all()
        sample_counts = {}
        for site in all_apa_sites:
            if site.sample_data:
                import json

                try:
                    sample_details = json.loads(site.sample_data)
                    for sd in sample_details:
                        sample_name = sd.get("sample_name", "Unknown")
                        sample_counts[sample_name] = (
                            sample_counts.get(sample_name, 0) + 1
                        )
                except:
                    pass
        apa_by_sample = [{"name": k, "count": v} for k, v in sample_counts.items()]
    except:
        pass

    # APA sites by chromosome
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

    # Top genes by APA sites
    top_genes = (
        db.query(
            Gene.gene_name, Gene.gene_id, func.count(APASite.id).label("apa_count"), Gene.id
        )
        .select_from(APASite)
        .join(Transcript, APASite.transcript_id == Transcript.id)
        .join(Gene, Transcript.gene_id == Gene.id)
        .group_by(Gene.gene_name, Gene.gene_id, Gene.id)
        .order_by(func.count(APASite.id).desc())
        .limit(20)
        .all()
    )

    # Average APA sites per transcript - use subquery
    from sqlalchemy import case

    count_per_transcript = (
        db.query(Transcript.id, func.count(APASite.id).label("apa_count"))
        .outerjoin(APASite, APASite.transcript_id == Transcript.id)
        .group_by(Transcript.id)
        .subquery()
    )

    avg_result = db.query(func.avg(count_per_transcript.c.apa_count)).scalar()
    avg_apa_per_transcript = float(avg_result) if avg_result else 0

    # APA sites by strand
    apa_by_strand = (
        db.query(Gene.strand, func.count(APASite.id).label("count"))
        .select_from(APASite)
        .join(Transcript, APASite.transcript_id == Transcript.id)
        .join(Gene, Transcript.gene_id == Gene.id)
        .filter(Gene.strand.isnot(None))
        .group_by(Gene.strand)
        .all()
    )

    return {
        "total_genes": total_genes,
        "total_transcripts": total_transcripts,
        "total_apa_sites": total_apa_sites,
        "total_samples": total_samples,
        "total_species": total_species,
        "avg_apa_per_transcript": round(avg_apa_per_transcript, 2),
        "apa_sites_by_species": [{"name": s[0], "count": s[1]} for s in apa_by_species],
        "apa_sites_by_sample": apa_by_sample,
        "apa_sites_by_chromosome": [
            {"chromosome": c[0], "count": c[1]} for c in apa_by_chromosome
        ],
        "apa_sites_by_strand": [{"strand": s[0], "count": s[1]} for s in apa_by_strand],
        "top_genes_by_apa": [
            {"gene_name": g[0], "gene_id": g[1], "apa_count": g[2], "gene_db_id": g[3]} for g in top_genes
        ],
    }


@router.get("/download/apa-sites")
def download_apa_sites(
    species: Optional[str] = None,
    sample: Optional[str] = None,
    gene_name: Optional[str] = None,
    format: str = Query("csv", pattern="^(csv|tsv|txt)$"),
    db: Session = Depends(get_db),
):
    """Download APA sites data in various formats."""
    query = (
        db.query(
            Gene.gene_name,
            Gene.gene_id,
            Transcript.transcript_id,
            APASite.unified_id,
            APASite.mode_site_position,
            APASite.site_count,
            APASite.site_abundance,
            Species.name.label("species"),
            Sample.name.label("sample"),
        )
        .join(Transcript)
        .join(APASite)
        .join(Species)
        .outerjoin(Sample)
    )

    if species:
        query = query.filter(Species.name.ilike(f"%{species}%"))
    if gene_name:
        query = query.filter(Gene.gene_name.ilike(f"%{gene_name}%"))

    results = query.all()

    delimiter = "," if format == "csv" else "\t"
    output = io.StringIO()

    headers = [
        "gene_name",
        "gene_id",
        "transcript_id",
        "unified_id",
        "mode_site_position",
        "site_count",
        "site_abundance",
        "species",
        "sample",
    ]
    writer = csv.DictWriter(output, fieldnames=headers, delimiter=delimiter)
    writer.writeheader()

    for row in results:
        writer.writerow(
            {
                "gene_name": row.gene_name or "",
                "gene_id": row.gene_id or "",
                "transcript_id": row.transcript_id or "",
                "unified_id": row.unified_id or "",
                "mode_site_position": row.mode_site_position or "",
                "site_count": row.site_count or "",
                "site_abundance": row.site_abundance or "",
                "species": row.species or "",
                "sample": row.sample or "",
            }
        )

    output.seek(0)

    media_type = "text/csv" if format == "csv" else "text/tab-separated-values"
    filename = f"apa_sites.{format}"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/download/genes")
def download_genes(
    species: Optional[str] = None,
    format: str = Query("csv", pattern="^(csv|tsv|txt)$"),
    db: Session = Depends(get_db),
):
    """Download genes data."""
    query = (
        db.query(
            Gene.gene_name,
            Gene.gene_id,
            Gene.chromosome,
            Gene.strand,
            Species.name.label("species"),
            func.count(Transcript.id).label("transcript_count"),
            func.count(APASite.id).label("apa_site_count"),
        )
        .join(Species)
        .outerjoin(Transcript)
        .outerjoin(APASite)
        .group_by(
            Gene.gene_name, Gene.gene_id, Gene.chromosome, Gene.strand, Species.name
        )
    )

    if species:
        query = query.filter(Species.name.ilike(f"%{species}%"))

    results = query.all()

    delimiter = "," if format == "csv" else "\t"
    output = io.StringIO()

    headers = [
        "gene_name",
        "gene_id",
        "chromosome",
        "strand",
        "species",
        "transcript_count",
        "apa_site_count",
    ]
    writer = csv.DictWriter(output, fieldnames=headers, delimiter=delimiter)
    writer.writeheader()

    for row in results:
        writer.writerow(
            {
                "gene_name": row.gene_name or "",
                "gene_id": row.gene_id or "",
                "chromosome": row.chromosome or "",
                "strand": row.strand or "",
                "species": row.species or "",
                "transcript_count": row.transcript_count or 0,
                "apa_site_count": row.apa_site_count or 0,
            }
        )

    output.seek(0)

    media_type = "text/csv" if format == "csv" else "text/tab-separated-values"
    filename = f"genes.{format}"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/download/transcripts")
def download_transcripts(
    species: Optional[str] = None,
    format: str = Query("csv", pattern="^(csv|tsv|txt)$"),
    db: Session = Depends(get_db),
):
    """Download transcripts data."""
    query = (
        db.query(
            Gene.gene_name,
            Gene.gene_id,
            Transcript.transcript_id,
            Gene.chromosome,
            Gene.strand,
            Species.name.label("species"),
            func.count(APASite.id).label("apa_site_count"),
        )
        .join(Gene)
        .join(Species)
        .outerjoin(APASite)
        .group_by(
            Gene.gene_name,
            Gene.gene_id,
            Transcript.transcript_id,
            Gene.chromosome,
            Gene.strand,
            Species.name,
        )
    )

    if species:
        query = query.filter(Species.name.ilike(f"%{species}%"))

    results = query.all()

    delimiter = "," if format == "csv" else "\t"
    output = io.StringIO()

    headers = [
        "gene_name",
        "gene_id",
        "transcript_id",
        "chromosome",
        "strand",
        "species",
        "apa_site_count",
    ]
    writer = csv.DictWriter(output, fieldnames=headers, delimiter=delimiter)
    writer.writeheader()

    for row in results:
        writer.writerow(
            {
                "gene_name": row.gene_name or "",
                "gene_id": row.gene_id or "",
                "transcript_id": row.transcript_id or "",
                "chromosome": row.chromosome or "",
                "strand": row.strand or "",
                "species": row.species or "",
                "apa_site_count": row.apa_site_count or 0,
            }
        )

    output.seek(0)

    media_type = "text/csv" if format == "csv" else "text/tab-separated-values"
    filename = f"transcripts.{format}"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/download/bed")
def download_bed(
    species: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Download PA sites as BED6 format for genome browser visualization (IGV, UCSC, JBrowse)."""
    query = (
        db.query(
            Gene.chromosome,
            APASite.mode_site_position,
            APASite.unified_id,
            APASite.site_count,
            Gene.strand,
            Gene.gene_name,
            Transcript.transcript_id,
        )
        .select_from(APASite)
        .join(Transcript, APASite.transcript_id == Transcript.id)
        .join(Gene, Transcript.gene_id == Gene.id)
        .join(Species, APASite.species_id == Species.id)
    )

    if species:
        query = query.filter(Species.name.ilike(f"%{species}%"))

    results = query.all()

    output = io.StringIO()
    output.write(
        'track name="ApaAtlas_PA_Sites" description="ApaAtlas Polyadenylation Sites" useScore=1\n'
    )

    for row in results:
        chrom = row.chromosome or "chrUnknown"
        if not chrom.lower().startswith("chr"):
            chrom = f"chr{chrom}"
        site_pos = int(row.mode_site_position) if row.mode_site_position else 0
        chrom_start = max(0, site_pos - 1)  # BED is 0-based
        chrom_end = site_pos               # half-open end
        name = f"{row.gene_name}|{row.transcript_id}|{row.unified_id}"
        score = min(int(row.site_count) if row.site_count else 0, 1000)
        strand = row.strand if row.strand in ("+", "-") else "."
        output.write(f"{chrom}\t{chrom_start}\t{chrom_end}\t{name}\t{score}\t{strand}\n")

    output.seek(0)
    sp_suffix = f"_{species.lower().replace(' ', '_')}" if species else ""
    filename = f"apaatlas_pa_sites{sp_suffix}.bed"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/download/abundance-matrix")
def download_abundance_matrix(
    species: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Download PA site × sample abundance matrix (TSV) for differential APA analysis."""
    sample_query = db.query(Sample.name).join(Species)
    if species:
        sample_query = sample_query.filter(Species.name.ilike(f"%{species}%"))
    sample_names = sorted({row[0] for row in sample_query.all()})

    query = (
        db.query(
            APASite.unified_id,
            Transcript.transcript_id,
            Gene.gene_name,
            Gene.chromosome,
            Gene.strand,
            APASite.mode_site_position,
            APASite.sample_data,
            Species.name.label("species"),
        )
        .select_from(APASite)
        .join(Transcript, APASite.transcript_id == Transcript.id)
        .join(Gene, Transcript.gene_id == Gene.id)
        .join(Species, APASite.species_id == Species.id)
    )

    if species:
        query = query.filter(Species.name.ilike(f"%{species}%"))

    results = query.all()

    output = io.StringIO()
    header_cols = [
        "site_id", "transcript_id", "gene_name",
        "chromosome", "strand", "position", "species",
    ] + sample_names
    output.write("\t".join(header_cols) + "\n")

    for row in results:
        sample_counts: dict = {s: 0 for s in sample_names}
        if row.sample_data:
            try:
                for sd in json.loads(row.sample_data):
                    sname = sd.get("sample_name", "")
                    if sname in sample_counts:
                        sample_counts[sname] = int(sd.get("site_count", 0) or 0)
            except Exception:
                pass

        row_vals = [
            row.unified_id or "",
            row.transcript_id or "",
            row.gene_name or "",
            row.chromosome or "",
            row.strand or "",
            str(row.mode_site_position or ""),
            row.species or "",
        ] + [str(sample_counts[s]) for s in sample_names]
        output.write("\t".join(row_vals) + "\n")

    output.seek(0)
    sp_suffix = f"_{species.lower().replace(' ', '_')}" if species else ""
    filename = f"apaatlas_abundance_matrix{sp_suffix}.tsv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/tab-separated-values",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# FASTA index cache
# ---------------------------------------------------------------------------
_FASTA_INDEX_CACHE: dict = {}  # fasta_path -> dict of chrom entries


def _load_fasta_index(fasta_path: str) -> dict:
    if fasta_path in _FASTA_INDEX_CACHE:
        return _FASTA_INDEX_CACHE[fasta_path]
    idx_path = fasta_path + ".fidx"
    if not os.path.exists(idx_path):
        return {}
    with open(idx_path) as fh:
        idx = json.load(fh)
    _FASTA_INDEX_CACHE[fasta_path] = idx
    return idx


def _fetch_fasta_seq(fasta_path: str, chrom: str, start: int, end: int) -> str:
    """Return sequence [start, end) (0-based half-open) for chrom. Returns '' on failure."""
    idx = _load_fasta_index(fasta_path)
    # Accept both 'chr1' and '1' style chroms
    entry = idx.get(chrom) or idx.get(chrom.lstrip("chr")) or idx.get("chr" + chrom)
    if not entry:
        return ""
    offset = entry["offset"]
    line_len = entry["line_len"]
    line_bytes = entry["line_bytes"]

    if start < 0:
        start = 0
    if end <= start:
        return ""

    lines_before_start = start // line_len
    byte_start = offset + lines_before_start * line_bytes + (start % line_len)

    lines_before_end = (end - 1) // line_len
    byte_end = offset + lines_before_end * line_bytes + ((end - 1) % line_len) + 1

    with open(fasta_path, "rb") as fh:
        fh.seek(byte_start)
        raw = fh.read(byte_end - byte_start)

    seq = (
        raw.replace(b"\n", b"")
        .replace(b"\r", b"")
        .decode("ascii", errors="replace")
        .upper()
    )
    return seq[: end - start]


def _rev_comp(seq: str) -> str:
    comp = str.maketrans("ACGTNacgtn", "TGCANtgcan")
    return seq.translate(comp)[::-1]


def _derive_cds_end(transcript_id: str, strand: str, bed12_path: str):
    rec = _fetch_bed12_record(bed12_path, transcript_id)
    if not rec:
        return None
    ts, te = rec["thick_start"], rec["thick_end"]
    if ts >= te:
        return None
    return ts + 1 if strand == "-" else te


def _utr_genomic_coords(site_pos: int, cds_end_pos, strand: str):
    """Return (genomic_start, genomic_end) of the UTR region (1-based inclusive)."""
    if cds_end_pos is None:
        if strand == "-":
            return site_pos, site_pos + 500
        else:
            return max(1, site_pos - 500), site_pos
    return min(site_pos, cds_end_pos), max(site_pos, cds_end_pos)


@router.get("/transcript/{transcript_id}/utr-sequence/{site_id}")
def get_utr_sequence(transcript_id: str, site_id: str, db: Session = Depends(get_db)):
    """
    Return the 3' UTR sequence from the CDS end to the APA cleavage site as FASTA.
    """
    transcript = (
        db.query(Transcript).filter(Transcript.transcript_id == transcript_id).first()
    )
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    gene = db.query(Gene).filter(Gene.id == transcript.gene_id).first()
    if not gene:
        raise HTTPException(status_code=404, detail="Gene not found")

    apa_site = (
        db.query(APASite)
        .filter(APASite.transcript_id == transcript.id, APASite.unified_id == site_id)
        .first()
    )
    if not apa_site:
        raise HTTPException(status_code=404, detail="APA site not found")

    species_obj = db.query(Species).filter(Species.id == apa_site.species_id).first()
    if not species_obj:
        raise HTTPException(status_code=404, detail="Species not found")

    fasta_path = get_species_ref_path(str(species_obj.name), "fasta")
    if not fasta_path:
        raise HTTPException(
            status_code=404, detail="FASTA file not available for this species"
        )

    strand = str(gene.strand)
    chrom = str(gene.chromosome)

    bed12_path = get_species_ref_path(str(species_obj.name), "bed12")
    cds_end_pos = _derive_cds_end(transcript_id, strand, bed12_path) if bed12_path else None

    site_pos = int(apa_site.mode_site_position)
    g_start, g_end = _utr_genomic_coords(site_pos, cds_end_pos, strand)

    seq = _fetch_fasta_seq(fasta_path, chrom, g_start - 1, g_end)
    if not seq:
        raise HTTPException(
            status_code=500, detail="Could not retrieve sequence from genome FASTA"
        )

    if strand == "-":
        seq = _rev_comp(seq)

    utr_len = len(seq)
    header = (
        f">{site_id} | {transcript_id} | "
        f"chr{chrom}:{g_start}-{g_end}({strand}) | "
        f"3UTR_length={utr_len}nt"
    )
    wrapped = "\n".join(seq[i : i + 60] for i in range(0, len(seq), 60))
    fasta_text = header + "\n" + wrapped + "\n"

    filename = f"{site_id}_3utr.fa"
    return PlainTextResponse(
        content=fasta_text,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/transcript/{transcript_id}/utr-composition")
def get_utr_composition(transcript_id: str, db: Session = Depends(get_db)):
    """
    Return sequence composition metrics for each APA site's 3'UTR region.
    """
    ARE_CORE = "ATTTA"

    transcript = (
        db.query(Transcript).filter(Transcript.transcript_id == transcript_id).first()
    )
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    gene = db.query(Gene).filter(Gene.id == transcript.gene_id).first()
    if not gene:
        raise HTTPException(status_code=404, detail="Gene not found")

    apa_sites = db.query(APASite).filter(APASite.transcript_id == transcript.id).all()
    if not apa_sites:
        return []

    apa_site_0 = apa_sites[0]
    species_obj = db.query(Species).filter(Species.id == apa_site_0.species_id).first()
    fasta_path = (
        get_species_ref_path(str(species_obj.name), "fasta") if species_obj else None
    )

    strand = str(gene.strand)
    chrom = str(gene.chromosome)

    bed12_path = (
        get_species_ref_path(str(species_obj.name), "bed12") if species_obj else None
    )
    cds_end_pos = _derive_cds_end(transcript_id, strand, bed12_path) if bed12_path else None

    DINUCS = [
        "AA",
        "AC",
        "AG",
        "AT",
        "CA",
        "CC",
        "CG",
        "CT",
        "GA",
        "GC",
        "GG",
        "GT",
        "TA",
        "TC",
        "TG",
        "TT",
    ]

    result = []
    for site in apa_sites:
        site_pos = int(site.mode_site_position)
        g_start, g_end = _utr_genomic_coords(site_pos, cds_end_pos, strand)

        seq = ""
        if fasta_path:
            seq = _fetch_fasta_seq(fasta_path, chrom, g_start - 1, g_end)
            if seq and strand == "-":
                seq = _rev_comp(seq)

        utr_len = len(seq)
        if utr_len == 0:
            result.append(
                {
                    "unified_id": site.unified_id,
                    "mode_site_position": site_pos,
                    "utr_length": 0,
                    "gc_pct": None,
                    "au_pct": None,
                    "are_density": None,
                    "are_count": None,
                    "dinuc_counts": {},
                    "sequence_available": False,
                }
            )
            continue

        gc = seq.count("G") + seq.count("C")
        gc_pct = round(gc / utr_len * 100, 1)

        au = seq.count("A") + seq.count("T")
        au_pct = round(au / utr_len * 100, 1)

        are_count = sum(1 for i in range(len(seq) - 4) if seq[i : i + 5] == ARE_CORE)
        are_density = round(are_count / utr_len * 100, 2)

        total_di = utr_len - 1 if utr_len > 1 else 1
        dinuc_counts = {
            dn: round(
                sum(1 for i in range(utr_len - 1) if seq[i : i + 2] == dn)
                / total_di
                * 100,
                1,
            )
            for dn in DINUCS
        }

        result.append(
            {
                "unified_id": site.unified_id,
                "mode_site_position": site_pos,
                "utr_length": utr_len,
                "gc_pct": gc_pct,
                "au_pct": au_pct,
                "are_density": are_density,
                "are_count": are_count,
                "dinuc_counts": dinuc_counts,
                "sequence_available": True,
            }
        )

    return result


# ---------------------------------------------------------------------------
# RBP binding motif scanner
# ---------------------------------------------------------------------------

# Curated RBP motif table.
# Each entry: name, consensus regex (DNA/RNA-style T=U), colour for the UI,
# and a brief function blurb shown in the tooltip.
# Sources: Ray et al. 2013 (Nature), Gerstberger et al. 2014 (Nat Rev MCB),
#          RBPDB, ATtRACT database.
_RBP_MOTIFS = [
    {
        "rbp": "HuR (ELAVL1)",
        "motif": r"AUUUA|UUUUU|UUAUUU",  # ARED/ARE pentamers
        "dna": r"ATTTA|TTTTT|TTATTTT",
        "color": "#E53935",
        "function": "Stabilises mRNA by competing with TTP for AU-rich elements; elevated in many cancers",
        "category": "Stability",
    },
    {
        "rbp": "TTP (ZFP36)",
        "motif": r"UAUUUAU|AUUUAU",
        "dna": r"TATTTTAT|TATTTAT",
        "color": "#FB8C00",
        "function": "Promotes mRNA decay via ARE binding; tumour suppressor in several contexts",
        "category": "Decay",
    },
    {
        "rbp": "PUM1/2 (Pumilio)",
        "motif": r"UGUAAAUA",
        "dna": r"TGTAAATA",
        "color": "#8E24AA",
        "function": "Translational repressor; binds Pumilio Response Element (PRE) in 3′ UTR",
        "category": "Translation",
    },
    {
        "rbp": "CPEB1",
        "motif": r"UUUUAU|UUUUUAU",
        "dna": r"TTTTAT|TTTTTAT",
        "color": "#1E88E5",
        "function": "Cytoplasmic polyadenylation; regulates poly-A tail length and translation activation",
        "category": "Polyadenylation",
    },
    {
        "rbp": "miR-7 seed",
        "motif": r"UCUUCC",  # reverse complement of miR-7-5p seed UGGAAGA
        "dna": r"TCTTCC",
        "color": "#00897B",
        "function": "miR-7 target seed (positions 2–7 of miR-7-5p); silences via RISC in many tumour types",
        "category": "miRNA",
    },
    {
        "rbp": "miR-155 seed",
        "motif": r"UAAUGCU",
        "dna": r"TAATGCT",
        "color": "#43A047",
        "function": "miR-155 target seed; oncomiR upregulated in lymphomas and breast cancer",
        "category": "miRNA",
    },
    {
        "rbp": "hnRNPC",
        "motif": r"UUUUU",
        "dna": r"TTTTT",
        "color": "#F4511E",
        "function": "Binds poly-U tracts; competes with U2AF2 at poly-pyrimidine tracts; affects splicing & stability",
        "category": "Stability",
    },
    {
        "rbp": "YTHDF2 (m6A reader)",
        "motif": r"GGACU|GGACT",
        "dna": r"GGACT",
        "color": "#6D4C41",
        "function": "Recognises m6A-modified GGAC motifs; recruits CCR4-NOT deadenylase complex for decay",
        "category": "Decay",
    },
    {
        "rbp": "FMR1 (FMRP)",
        "motif": r"ACUK",  # approximate; K = G/T
        "dna": r"ACT[GT]",
        "color": "#546E7A",
        "function": "Translational silencer; loss-of-function causes Fragile X syndrome",
        "category": "Translation",
    },
    {
        "rbp": "PABPC1",
        "motif": r"AAAAAAA",
        "dna": r"AAAAAAA",
        "color": "#00ACC1",
        "function": "Poly-A binding protein; protects poly-A tail from deadenylases, stimulates translation",
        "category": "Stability",
    },
]

# Pre-compile DNA-space patterns (we scan DNA sequences from the FASTA)
for _m in _RBP_MOTIFS:
    _m["_compiled"] = re.compile(_m["dna"], re.IGNORECASE)


@router.get("/transcript/{transcript_id}/rbp-motifs")
def get_rbp_motifs(transcript_id: str, db: Session = Depends(get_db)):
    """
    Scan each APA site's 3′ UTR sequence for known RBP binding motifs.
    Returns per-site hit counts and per-RBP match positions.
    """
    transcript = (
        db.query(Transcript).filter(Transcript.transcript_id == transcript_id).first()
    )
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    gene = db.query(Gene).filter(Gene.id == transcript.gene_id).first()
    if not gene:
        raise HTTPException(status_code=404, detail="Gene not found")

    apa_sites = db.query(APASite).filter(APASite.transcript_id == transcript.id).all()
    if not apa_sites:
        return []

    apa_site_0 = apa_sites[0]
    species_obj = db.query(Species).filter(Species.id == apa_site_0.species_id).first()
    fasta_path = (
        get_species_ref_path(str(species_obj.name), "fasta") if species_obj else None
    )
    bed12_path = (
        get_species_ref_path(str(species_obj.name), "bed12") if species_obj else None
    )

    strand = str(gene.strand)
    chrom = str(gene.chromosome)
    cds_end_pos = _derive_cds_end(transcript_id, strand, bed12_path) if bed12_path else None

    result = []
    for site in apa_sites:
        site_pos = int(site.mode_site_position)
        g_start, g_end = _utr_genomic_coords(site_pos, cds_end_pos, strand)

        seq = ""
        if fasta_path:
            seq = _fetch_fasta_seq(fasta_path, chrom, g_start - 1, g_end)
            if seq and strand == "-":
                seq = _rev_comp(seq)

        utr_len = len(seq)

        rbp_hits = []
        for rbp in _RBP_MOTIFS:
            if not utr_len:
                hits = []
            else:
                hits = [
                    {"start": m.start(), "end": m.end(), "match": m.group()}
                    for m in rbp["_compiled"].finditer(seq)
                ]
            rbp_hits.append(
                {
                    "rbp": rbp["rbp"],
                    "category": rbp["category"],
                    "color": rbp["color"],
                    "function": rbp["function"],
                    "count": len(hits),
                    "density": round(len(hits) / utr_len * 100, 2) if utr_len else 0,
                    "positions": [h["start"] for h in hits[:60]],
                }
            )

        result.append(
            {
                "unified_id": site.unified_id,
                "mode_site_position": site_pos,
                "utr_length": utr_len,
                "sequence_available": utr_len > 0,
                "rbp_hits": rbp_hits,
            }
        )

    return result


# ---------------------------------------------------------------------------
# ±50 bp sequence context around a PA site cleavage position
# ---------------------------------------------------------------------------


@router.get("/transcript/{transcript_id}/site-sequence/{site_id}")
def get_site_sequence_context(
    transcript_id: str, site_id: str, db: Session = Depends(get_db)
):
    transcript = (
        db.query(Transcript).filter(Transcript.transcript_id == transcript_id).first()
    )
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    gene = db.query(Gene).filter(Gene.id == transcript.gene_id).first()
    if not gene:
        raise HTTPException(status_code=404, detail="Gene not found")

    apa_site = (
        db.query(APASite)
        .filter(APASite.transcript_id == transcript.id, APASite.unified_id == site_id)
        .first()
    )
    if not apa_site:
        raise HTTPException(status_code=404, detail="APA site not found")

    seq = apa_site.sequence or ""
    cleavage_index = len(seq) // 2 if seq else 50

    return {
        "unified_id": site_id,
        "mode_site_position": int(apa_site.mode_site_position),
        "chromosome": str(gene.chromosome),
        "strand": str(gene.strand),
        "flank": (len(seq) - 1) // 2 if seq else 50,
        "sequence": seq,
        "cleavage_index": cleavage_index,
        "pas_motif": apa_site.pas_motif,
        "pas_position": apa_site.pas_position,
        "pas_type": apa_site.pas_type,
    }
