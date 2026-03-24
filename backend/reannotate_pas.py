import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from app.models.database import SessionLocal, Species, Gene, Transcript, APASite
from app.services.pas_annotator import PASAnnotator

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

SPECIES_FASTA = {
    'homo_sapiens' : ('Human', 'Homo_sapiens.GRCh38.dna_sm.primary_assembly.fa'),
    'mus_musculus' : ('Mouse', 'Mus_musculus.GRCm39.dna_sm.primary_assembly.fa'),
}

db = SessionLocal()
try:
    for species_folder, (species_name, fasta_name) in SPECIES_FASTA.items():
        fasta_path = os.path.join(DATA_DIR, species_folder, 'reference', fasta_name)
        if not os.path.exists(fasta_path):
            print(f"  SKIP {species_folder}: FASTA not found")
            continue

        species = db.query(Species).filter(Species.name == species_name).first()
        if not species:
            print(f"  SKIP {species_folder}: species not in DB")
            continue

        sites = db.query(APASite).filter(APASite.species_id == species.id).all()
        print(f"\n{species_folder}: {len(sites)} sites")
        annotator = PASAnnotator(fasta_path)

        for i, site in enumerate(sites):
            gene = site.transcript.gene
            result = annotator.annotate_site(gene.chromosome, site.site_position, gene.strand)
            level = result.get('search_level', 'none')

            if level == 'hexamer':
                h = result['hexamer']
                site.pas_motif      = h['motif']
                site.pas_position   = h['position']
                site.pas_type       = h['motif_type']
                site.pas_confidence = h['confidence']
            elif level in ('upstream', 'downstream'):
                hits = result['upstream_motifs'] or result['downstream_motifs']
                first = hits[0] if hits else {}
                site.pas_motif      = first.get('motif')
                site.pas_position   = first.get('offset')
                site.pas_type       = 'other'
                site.pas_confidence = 'low'
            else:
                site.pas_motif      = None
                site.pas_position   = None
                site.pas_type       = None
                site.pas_confidence = None

            if (i + 1) % 200 == 0:
                db.commit()
                print(f"  {i+1}/{len(sites)} done")

        db.commit()
        print(f"  Done {species_folder}")

    print("\nAll done.")
finally:
    db.close()
