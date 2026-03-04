from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List, Optional
import os
import json
import csv
import io
from app.models.database import get_db, Gene, Transcript, APASite, Species, Sample
from app.schemas.schemas import (
    SearchResult, DashboardStats, LocusDetail, 
    APASiteWithDetails, GeneDetail
)

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")

SPECIES_FOLDER_MAP = {
    'Human': 'homo_sapiens',
    'Mouse': 'mus_musculus',
    'Rat': 'rattus_norvegicus',
    'Zebrafish': 'danio_rerio',
}


def get_species_ref_path(species_name: str, file_type: str = 'gtf') -> str:
    """Get reference file path for a species."""
    species_folder = SPECIES_FOLDER_MAP.get(species_name)
    if not species_folder:
        return None
    
    ref_dir = os.path.join(DATA_DIR, species_folder, 'reference')
    if not os.path.exists(ref_dir):
        return None
    
    for f in os.listdir(ref_dir):
        if file_type == 'gtf' and (f.endswith('.gtf') or f.endswith('.gff3')):
            return os.path.join(ref_dir, f)
        elif file_type == 'fasta' and (f.endswith('.fa') or f.endswith('.fasta')):
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
    
    apa_by_species = db.query(
        Species.name,
        func.count(APASite.id).label('count')
    ).join(APASite, APASite.species_id == Species.id).group_by(Species.name).all()
    
    apa_per_transcript = db.query(
        Transcript.transcript_id,
        func.count(APASite.id).label('count')
    ).join(APASite, APASite.transcript_id == Transcript.id).group_by(Transcript.transcript_id).all()
    
    return DashboardStats(
        total_genes=total_genes,
        total_transcripts=total_transcripts,
        total_apa_sites=total_apa_sites,
        total_cell_lines=total_samples,
        total_species=total_species,
        apa_sites_by_species=[{"name": s[0], "count": s[1]} for s in apa_by_species],
        apa_sites_by_cell_line=[],
        apa_sites_per_transcript=[{"transcript_id": t[0], "count": t[1]} for t in apa_per_transcript]
    )


@router.get("/search", response_model=List[SearchResult])
def search_transcripts(
    gene_name: Optional[str] = None,
    transcript_id: Optional[str] = None,
    gene_id: Optional[str] = None,
    sample: Optional[str] = None,
    species: Optional[str] = None,
    chromosome: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search for transcripts with filters."""
    query = db.query(
        Transcript.transcript_id,
        Gene.gene_id,
        Gene.gene_name,
        Gene.chromosome,
        Gene.strand,
        func.count(APASite.id).label('apa_site_count'),
        Species.name.label('species')
    ).join(Gene).join(APASite).join(Species)
    
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
    
    results = query.group_by(
        Transcript.transcript_id,
        Gene.gene_id,
        Gene.gene_name,
        Gene.chromosome,
        Gene.strand,
        Species.name
    ).offset((page - 1) * limit).limit(limit).all()
    
    search_results = []
    for r in results:
        apa_sites = db.query(APASite).filter(APASite.transcript_id == db.query(Transcript).filter(Transcript.transcript_id == r[0]).first().id).all()
        sample_names = set()
        for asite in apa_sites:
            if asite.sample_data:
                try:
                    import json
                    sample_details = json.loads(asite.sample_data)
                    for sd in sample_details:
                        sample_names.add(sd.get('sample_name', ''))
                except:
                    pass
        search_results.append(SearchResult(
            transcript_id=r[0],
            gene_id=r[1],
            gene_name=r[2],
            chromosome=r[3],
            strand=r[4],
            apa_site_count=r[5],
            cell_lines=list(sample_names),
            species=r[6]
        ))
    
    return search_results


@router.get("/gene/{gene_id}", response_model=GeneDetail)
def get_gene_detail(gene_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a gene and all its transcripts with APA sites."""
    gene = db.query(Gene).filter(Gene.gene_id == gene_id).first()
    if not gene:
        raise HTTPException(status_code=404, detail="Gene not found")
    
    transcripts = db.query(Transcript).filter(Transcript.gene_id == gene.id).all()
    
    transcript_data = []
    for transcript in transcripts:
        apa_sites = db.query(APASite).filter(APASite.transcript_id == transcript.id).all()
        
        sample_names = set()
        transcript_apa_sites = []
        for asite in apa_sites:
            sample_details = []
            if asite.sample_data:
                try:
                    sample_details = json.loads(asite.sample_data)
                    for sd in sample_details:
                        sample_names.add(sd.get('sample_name', ''))
                except:
                    sample_details = []
            
            transcript_apa_sites.append({
                'site_id': asite.site_id,
                'site_position': asite.site_position,
                'site_abundance': asite.site_abundance,
                'site_count': asite.site_count,
                'sample_details': sample_details
            })
        
        transcript_data.append({
            'transcript_id': transcript.transcript_id,
            'apa_site_count': len(apa_sites),
            'samples': list(sample_names),
            'apa_sites': transcript_apa_sites
        })
    
    return GeneDetail(
        gene_id=gene.gene_id,
        gene_name=gene.gene_name,
        chromosome=gene.chromosome,
        strand=gene.strand,
        transcripts=transcript_data
    )


@router.get("/autocomplete")
def autocomplete(
    q: str = Query(..., min_length=1),
    field: str = Query("gene_name"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Autocomplete search suggestions."""
    if field == "gene_name":
        results = db.query(Gene.gene_name).distinct().filter(
            Gene.gene_name.ilike(f"%{q}%")
        ).limit(limit).all()
        return [{"value": r[0], "type": "gene_name"} for r in results]
    elif field == "gene_id":
        results = db.query(Gene.gene_id).distinct().filter(
            Gene.gene_id.ilike(f"%{q}%")
        ).limit(limit).all()
        return [{"value": r[0], "type": "gene_id"} for r in results]
    elif field == "transcript_id":
        results = db.query(Transcript.transcript_id).distinct().filter(
            Transcript.transcript_id.ilike(f"%{q}%")
        ).limit(limit).all()
        return [{"value": r[0], "type": "transcript_id"} for r in results]
    elif field == "sample":
        results = db.query(Sample.name).distinct().filter(
            Sample.name.ilike(f"%{q}%")
        ).limit(limit).all()
        return [{"value": r[0], "type": "sample"} for r in results]
    elif field == "species":
        results = db.query(Species.name).distinct().filter(
            Species.name.ilike(f"%{q}%")
        ).limit(limit).all()
        return [{"value": r[0], "type": "species"} for r in results]
    return []


import json

@router.get("/transcript/{transcript_id}", response_model=LocusDetail)
def get_locus_detail(transcript_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a transcript and its APA sites."""
    transcript = db.query(Transcript).filter(Transcript.transcript_id == transcript_id).first()
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
                    sample_names.add(sd.get('sample_name', ''))
            except:
                sample_details = []
        
        apa_sites_with_details.append(APASiteWithDetails(
            site_id=str(asite.site_id),
            transcript_id=int(asite.transcript_id),
            species_id=int(asite.species_id),
            site_position=int(asite.site_position),
            site_count=int(asite.site_count),
            site_abundance=float(asite.site_abundance),
            sample_data=asite.sample_data,
            id=int(asite.id),
            transcript=transcript,
            species=species,
            sample_details=sample_details
        ))
    
    samples = list(sample_names)
    chromosomes = [gene.chromosome] if gene.chromosome else []
    
    return LocusDetail(
        gene=gene,
        transcript=transcript,
        apa_sites=apa_sites_with_details,
        samples=samples,
        chromosomes=chromosomes
    )


@router.get("/species")
def get_species(db: Session = Depends(get_db)):
    """Get all species."""
    species = db.query(Species).all()
    return [{"id": s.id, "name": s.name, "latin_name": s.latin_name, "assembly": s.assembly} for s in species]


@router.get("/samples")
def get_samples(species: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all samples (cell lines/tissues), optionally filtered by species."""
    query = db.query(Sample).join(Species)
    if species:
        query = query.filter(Species.name == species)
    samples = query.distinct().all()
    return [{"id": s.id, "name": s.name, "species": s.species.name} for s in samples]


@router.get("/genes")
def get_genes(page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    """Get featured/interesting genes."""
    genes = db.query(Gene).offset((page - 1) * limit).limit(limit).all()
    return [{"id": g.id, "gene_id": g.gene_id, "gene_name": g.gene_name, "chromosome": g.chromosome, "strand": g.strand} for g in genes]


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
    apa_by_species = db.query(
        Species.name,
        func.count(APASite.id).label('count')
    ).select_from(APASite).join(Species, APASite.species_id == Species.id).group_by(Species.name).all()
    
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
                        sample_name = sd.get('sample_name', 'Unknown')
                        sample_counts[sample_name] = sample_counts.get(sample_name, 0) + 1
                except:
                    pass
        apa_by_sample = [{"name": k, "count": v} for k, v in sample_counts.items()]
    except:
        pass
    
    # APA sites by chromosome
    apa_by_chromosome = db.query(
        Gene.chromosome,
        func.count(APASite.id).label('count')
    ).select_from(APASite).join(Transcript, APASite.transcript_id == Transcript.id).join(Gene, Transcript.gene_id == Gene.id).filter(
        Gene.chromosome.isnot(None)
    ).group_by(Gene.chromosome).order_by(Gene.chromosome).all()
    
    # Top genes by APA sites
    top_genes = db.query(
        Gene.gene_name,
        Gene.gene_id,
        func.count(APASite.id).label('apa_count')
    ).select_from(APASite).join(Transcript, APASite.transcript_id == Transcript.id).join(Gene, Transcript.gene_id == Gene.id).group_by(
        Gene.gene_name, Gene.gene_id
    ).order_by(func.count(APASite.id).desc()).limit(20).all()
    
    # Average APA sites per transcript - use subquery
    from sqlalchemy import case
    count_per_transcript = db.query(
        Transcript.id,
        func.count(APASite.id).label('apa_count')
    ).outerjoin(APASite, APASite.transcript_id == Transcript.id).group_by(Transcript.id).subquery()
    
    avg_result = db.query(func.avg(count_per_transcript.c.apa_count)).scalar()
    avg_apa_per_transcript = float(avg_result) if avg_result else 0
    
    # APA sites by strand
    apa_by_strand = db.query(
        Gene.strand,
        func.count(APASite.id).label('count')
    ).select_from(APASite).join(Transcript, APASite.transcript_id == Transcript.id).join(Gene, Transcript.gene_id == Gene.id).filter(
        Gene.strand.isnot(None)
    ).group_by(Gene.strand).all()
    
    return {
        "total_genes": total_genes,
        "total_transcripts": total_transcripts,
        "total_apa_sites": total_apa_sites,
        "total_samples": total_samples,
        "total_species": total_species,
        "avg_apa_per_transcript": round(avg_apa_per_transcript, 2),
        "apa_sites_by_species": [{"name": s[0], "count": s[1]} for s in apa_by_species],
        "apa_sites_by_sample": apa_by_sample,
        "apa_sites_by_chromosome": [{"chromosome": c[0], "count": c[1]} for c in apa_by_chromosome],
        "apa_sites_by_strand": [{"strand": s[0], "count": s[1]} for s in apa_by_strand],
        "top_genes_by_apa": [{"gene_name": g[0], "gene_id": g[1], "apa_count": g[2]} for g in top_genes]
    }


@router.get("/download/apa-sites")
def download_apa_sites(
    species: Optional[str] = None,
    sample: Optional[str] = None,
    gene_name: Optional[str] = None,
    format: str = Query("csv", regex="^(csv|tsv|txt)$"),
    db: Session = Depends(get_db)
):
    """Download APA sites data in various formats."""
    query = db.query(
        Gene.gene_name,
        Gene.gene_id,
        Transcript.transcript_id,
        APASite.site_id,
        APASite.site_position,
        APASite.site_count,
        APASite.site_abundance,
        Species.name.label('species'),
        Sample.name.label('sample')
    ).join(Transcript).join(APASite).join(Species).outerjoin(Sample)
    
    if species:
        query = query.filter(Species.name.ilike(f"%{species}%"))
    if gene_name:
        query = query.filter(Gene.gene_name.ilike(f"%{gene_name}%"))
    
    results = query.all()
    
    # Create CSV/TSV
    delimiter = ',' if format == 'csv' else '\t'
    output = io.StringIO()
    
    headers = ['gene_name', 'gene_id', 'transcript_id', 'site_id', 'site_position', 
               'site_count', 'site_abundance', 'species', 'sample']
    writer = csv.DictWriter(output, fieldnames=headers, delimiter=delimiter)
    writer.writeheader()
    
    for row in results:
        writer.writerow({
            'gene_name': row.gene_name or '',
            'gene_id': row.gene_id or '',
            'transcript_id': row.transcript_id or '',
            'site_id': row.site_id or '',
            'site_position': row.site_position or '',
            'site_count': row.site_count or '',
            'site_abundance': row.site_abundance or '',
            'species': row.species or '',
            'sample': row.sample or ''
        })
    
    output.seek(0)
    
    media_type = 'text/csv' if format == 'csv' else 'text/tab-separated-values'
    filename = f'apa_sites.{format}'
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type=media_type,
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@router.get("/download/genes")
def download_genes(
    species: Optional[str] = None,
    format: str = Query("csv", regex="^(csv|tsv|txt)$"),
    db: Session = Depends(get_db)
):
    """Download genes data."""
    query = db.query(
        Gene.gene_name,
        Gene.gene_id,
        Gene.chromosome,
        Gene.strand,
        Species.name.label('species'),
        func.count(Transcript.id).label('transcript_count'),
        func.count(APASite.id).label('apa_site_count')
    ).join(Species).outerjoin(Transcript).outerjoin(APASite).group_by(
        Gene.gene_name, Gene.gene_id, Gene.chromosome, Gene.strand, Species.name
    )
    
    if species:
        query = query.filter(Species.name.ilike(f"%{species}%"))
    
    results = query.all()
    
    delimiter = ',' if format == 'csv' else '\t'
    output = io.StringIO()
    
    headers = ['gene_name', 'gene_id', 'chromosome', 'strand', 'species', 'transcript_count', 'apa_site_count']
    writer = csv.DictWriter(output, fieldnames=headers, delimiter=delimiter)
    writer.writeheader()
    
    for row in results:
        writer.writerow({
            'gene_name': row.gene_name or '',
            'gene_id': row.gene_id or '',
            'chromosome': row.chromosome or '',
            'strand': row.strand or '',
            'species': row.species or '',
            'transcript_count': row.transcript_count or 0,
            'apa_site_count': row.apa_site_count or 0
        })
    
    output.seek(0)
    
    media_type = 'text/csv' if format == 'csv' else 'text/tab-separated-values'
    filename = f'genes.{format}'
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type=media_type,
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@router.get("/download/transcripts")
def download_transcripts(
    species: Optional[str] = None,
    format: str = Query("csv", regex="^(csv|tsv|txt)$"),
    db: Session = Depends(get_db)
):
    """Download transcripts data."""
    query = db.query(
        Gene.gene_name,
        Gene.gene_id,
        Transcript.transcript_id,
        Gene.chromosome,
        Gene.strand,
        Species.name.label('species'),
        func.count(APASite.id).label('apa_site_count')
    ).join(Gene).join(Species).outerjoin(APASite).group_by(
        Gene.gene_name, Gene.gene_id, Transcript.transcript_id, Gene.chromosome, Gene.strand, Species.name
    )
    
    if species:
        query = query.filter(Species.name.ilike(f"%{species}%"))
    
    results = query.all()
    
    delimiter = ',' if format == 'csv' else '\t'
    output = io.StringIO()
    
    headers = ['gene_name', 'gene_id', 'transcript_id', 'chromosome', 'strand', 'species', 'apa_site_count']
    writer = csv.DictWriter(output, fieldnames=headers, delimiter=delimiter)
    writer.writeheader()
    
    for row in results:
        writer.writerow({
            'gene_name': row.gene_name or '',
            'gene_id': row.gene_id or '',
            'transcript_id': row.transcript_id or '',
            'chromosome': row.chromosome or '',
            'strand': row.strand or '',
            'species': row.species or '',
            'apa_site_count': row.apa_site_count or 0
        })
    
    output.seek(0)
    
    media_type = 'text/csv' if format == 'csv' else 'text/tab-separated-values'
    filename = f'transcripts.{format}'
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type=media_type,
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
