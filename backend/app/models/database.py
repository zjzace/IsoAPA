from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Index, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, deferred
from app.config import settings

Base = declarative_base()


class Species(Base):
    __tablename__ = "species"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    latin_name = Column(String(100), nullable=False)
    assembly = Column(String(100), nullable=True)
    
    samples = relationship("Sample", back_populates="species")
    apa_sites = relationship("APASite", back_populates="species")


class Sample(Base):
    __tablename__ = "samples"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    sample_type = Column(String(50), nullable=False, default="cell_line")
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)
    
    species = relationship("Species", back_populates="samples")
    
    __table_args__ = (Index("idx_sample_species", "name", "species_id", unique=True),)


class Gene(Base):
    __tablename__ = "genes"
    
    id = Column(Integer, primary_key=True, index=True)
    gene_id = Column(String(100), unique=True, nullable=False, index=True)
    gene_name = Column(String(100), nullable=False, index=True)
    chromosome = Column(String(50), nullable=False, index=True)
    strand = Column(String(1), nullable=False)
    
    transcripts = relationship("Transcript", back_populates="gene")
    
    __table_args__ = (Index("idx_gene_name", "gene_name"),)


class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(String(100), unique=True, nullable=False, index=True)
    gene_id = Column(Integer, ForeignKey("genes.id"), nullable=False)
    
    gene = relationship("Gene", back_populates="transcripts")
    apa_sites = relationship("APASite", back_populates="transcript")


class APASite(Base):
    __tablename__ = "apa_sites"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(200), nullable=False, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), nullable=False, index=True)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)
    
    site_position = Column(Integer, nullable=False, index=True)
    site_count = Column(Integer, nullable=False, default=0)
    site_abundance = Column(Float, nullable=False, default=0.0)
    sample_data = Column(Text, nullable=True)
    
    # Tier 1 enhancements: PAS annotation and APA type classification
    # Deferred loading to avoid errors if columns don't exist in DB yet
    pas_motif = deferred(Column(String(10), nullable=True))  # Hexamer sequence (e.g., 'AATAAA')
    pas_position = deferred(Column(Integer, nullable=True))  # Distance from cleavage site (e.g., -18)
    pas_type = deferred(Column(String(20), nullable=True))  # 'canonical' or 'variant'
    pas_confidence = deferred(Column(String(20), nullable=True))  # 'high', 'medium', 'low'
    apa_type = deferred(Column(String(30), nullable=True))  # '3UTR-APA', 'Intronic-APA', 'Exonic-APA'
    apa_region = deferred(Column(String(50), nullable=True))  # Detailed region description
    apa_confidence = deferred(Column(String(20), nullable=True))  # Classification confidence
    
    transcript = relationship("Transcript", back_populates="apa_sites")
    species = relationship("Species", back_populates="apa_sites")
    
    __table_args__ = (
        Index("idx_apa_transcript_position", "transcript_id", "site_position", unique=True),
    )


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
