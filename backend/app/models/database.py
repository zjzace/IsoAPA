from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Index,
    Text,
)
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
    sample_type = Column(String(50), nullable=False, default="cell_culture")
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
    unified_id = Column(String(300), nullable=False, index=True)
    transcript_id = Column(
        Integer, ForeignKey("transcripts.id"), nullable=False, index=True
    )
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)

    mode_site_position = Column(Integer, nullable=False, index=True)
    transcript_biotype = Column(String(50), nullable=True)

    site_count = Column(Integer, nullable=False, default=0)
    site_abundance = Column(Float, nullable=False, default=0.0)
    sample_data = Column(Text, nullable=True)

    cluster_start = Column(Integer, nullable=True)
    cluster_end = Column(Integer, nullable=True)

    sequence = deferred(Column(String(200), nullable=True))
    pas_motif = deferred(Column(String(10), nullable=True))
    pas_position = deferred(Column(Integer, nullable=True))
    pas_type = deferred(Column(String(30), nullable=True))
    search_level = deferred(Column(String(20), nullable=True))

    transcript = relationship("Transcript", back_populates="apa_sites")
    species = relationship("Species", back_populates="apa_sites")

    __table_args__ = (
        Index(
            "idx_apa_transcript_unified_id", "transcript_id", "unified_id", unique=True
        ),
    )


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.DATABASE_URL
    else {},
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
