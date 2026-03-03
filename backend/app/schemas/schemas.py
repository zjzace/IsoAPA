from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SpeciesBase(BaseModel):
    name: str
    latin_name: str
    assembly: Optional[str] = None


class Species(SpeciesBase):
    id: int
    
    class Config:
        from_attributes = True


class CellLineBase(BaseModel):
    name: str
    species_id: int


class CellLine(CellLineBase):
    id: int
    species: Optional[Species] = None
    
    class Config:
        from_attributes = True


class GeneBase(BaseModel):
    gene_id: str
    gene_name: str
    chromosome: str
    strand: str


class Gene(GeneBase):
    id: int
    
    class Config:
        from_attributes = True


class TranscriptBase(BaseModel):
    transcript_id: str
    gene_id: int


class Transcript(TranscriptBase):
    id: int
    gene: Optional[Gene] = None
    
    class Config:
        from_attributes = True


class APASiteBase(BaseModel):
    site_id: str
    transcript_id: int
    species_id: int
    site_position: int
    site_count: int = 0
    site_abundance: float = 0.0
    sample_data: Optional[str] = None


class APASite(APASiteBase):
    id: int
    transcript: Optional[Transcript] = None
    species: Optional[Species] = None
    
    class Config:
        from_attributes = True


class APASiteWithDetails(APASiteBase):
    id: int
    transcript: Transcript
    species: Species
    sample_details: List[dict] = []
    
    class Config:
        from_attributes = True


class TranscriptWithGene(BaseModel):
    id: int
    transcript_id: str
    gene: GeneBase
    
    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    transcript_id: str
    gene_id: str
    gene_name: str
    chromosome: str
    strand: str
    apa_site_count: int
    cell_lines: List[str]
    species: str
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_genes: int
    total_transcripts: int
    total_apa_sites: int
    total_cell_lines: int
    total_species: int
    apa_sites_by_species: List[dict]
    apa_sites_by_cell_line: List[dict]
    apa_sites_per_transcript: List[dict]


class LocusDetail(BaseModel):
    gene: Gene
    transcript: Transcript
    apa_sites: List[APASiteWithDetails]
    samples: List[str]
    chromosomes: List[str]
    
    class Config:
        from_attributes = True


class GeneDetail(BaseModel):
    gene_id: str
    gene_name: str
    chromosome: str
    strand: str
    transcripts: List[dict]
    
    class Config:
        from_attributes = True
