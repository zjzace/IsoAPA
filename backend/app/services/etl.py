import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
from app.models.database import SessionLocal, Species, Sample, Gene, Transcript, APASite, init_db
from app.services.pas_annotator import PASAnnotator
from app.services.apa_classifier import APATypeClassifier

SPECIES_MAP = {
    'homo_sapiens': {'name': 'Human', 'latin_name': 'Homo sapiens', 'assembly': 'GRCh38'},
    'mus_musculus': {'name': 'Mouse', 'latin_name': 'Mus musculus', 'assembly': 'GRCm39'},
    'rattus_norvegicus': {'name': 'Rat', 'latin_name': 'Rattus norvegicus', 'assembly': 'rn6'},
    'danio_rerio': {'name': 'Zebrafish', 'latin_name': 'Danio rerio', 'assembly': 'GRCz11'},
}

DATA_DIR = None


def get_gtf_path(species_folder: str) -> str:
    """Get the GTF file path for a species."""
    species_dir = os.path.join(DATA_DIR, species_folder, 'reference')
    if not os.path.exists(species_dir):
        return None
    for f in os.listdir(species_dir):
        if f.endswith('.gtf') or f.endswith('.gff3'):
            return os.path.join(species_dir, f)
    return None


def get_fasta_path(species_folder: str) -> str:
    """Get the FASTA file path for a species."""
    species_dir = os.path.join(DATA_DIR, species_folder, 'reference')
    if not os.path.exists(species_dir):
        return None
    for f in os.listdir(species_dir):
        if f.endswith('.fa') or f.endswith('.fasta'):
            return os.path.join(species_dir, f)
    return None


def get_apa_files(species_folder: str) -> list:
    """Get all APA data files for a species."""
    species_dir = os.path.join(DATA_DIR, species_folder)
    apa_files = []
    
    if not os.path.exists(species_dir):
        return apa_files
    
    for item in os.listdir(species_dir):
        item_path = os.path.join(species_dir, item)
        if os.path.isdir(item_path) and item != 'reference':
            for f in os.listdir(item_path):
                if f.endswith('.txt') or f.endswith('.tsv'):
                    apa_files.append({
                        'sample_name': item,
                        'file_path': os.path.join(item_path, f)
                    })
    
    return apa_files


def ingest_data(data_dir: str = None):
    """Ingest APA sites data from the new folder structure."""
    global DATA_DIR
    DATA_DIR = data_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data')
    
    db = SessionLocal()
    
    try:
        print("Initializing database...")
        init_db()
        
        species_count = 0
        sample_count = 0
        gene_count = 0
        transcript_count = 0
        apa_site_count = 0
        
        species_map = {}
        sample_map = {}
        gene_map = {}
        transcript_map = {}
        apa_site_map = {}
        
        for species_folder in os.listdir(DATA_DIR):
            species_path = os.path.join(DATA_DIR, species_folder)
            if not os.path.isdir(species_path) or species_folder.startswith('.'):
                continue
            
            species_info = SPECIES_MAP.get(species_folder, {'name': species_folder, 'latin_name': species_folder, 'assembly': None})
            
            print(f"\nProcessing species: {species_folder}")
            
            if species_folder not in species_map:
                species = db.query(Species).filter(Species.name == species_info['name']).first()
                if not species:
                    species = Species(
                        name=species_info['name'],
                        latin_name=species_info['latin_name'],
                        assembly=species_info.get('assembly')
                    )
                    db.add(species)
                    db.flush()
                species_map[species_folder] = species.id
                species_count += 1
            
            species_id = species_map[species_folder]
            
            apa_files = get_apa_files(species_folder)
            print(f"  Found {len(apa_files)} sample folders")
            
            for apa_file_info in apa_files:
                sample_name = apa_file_info['sample_name']
                apa_file_path = apa_file_info['file_path']
                
                if sample_name not in sample_map:
                    sample = db.query(Sample).filter(
                        Sample.name == sample_name,
                        Sample.species_id == species_id
                    ).first()
                    if not sample:
                        sample = Sample(name=sample_name, species_id=species_id)
                        db.add(sample)
                        db.flush()
                    sample_map[sample_name] = sample.id
                    sample_count += 1
                
                sample_id = sample_map[sample_name]
                
                print(f"  Loading {sample_name}: {os.path.basename(apa_file_path)}")
                
                with open(apa_file_path, 'r') as f:
                    reader = csv.DictReader(f, delimiter='\t')
                    
                    for row in reader:
                        gene_id = row['gene_id']
                        gene_name = row['gene_name']
                        transcript_id = row['transcript_id']
                        chromosome = row['chromosome']
                        strand = row['strand']
                        site_id = row['ID']
                        site_position = int(row['site_position'])
                        site_count = int(row['site_count'])
                        site_abundance = float(row['site_abundance'])
                        
                        if gene_id not in gene_map:
                            gene = db.query(Gene).filter(Gene.gene_id == gene_id).first()
                            if not gene:
                                gene = Gene(
                                    gene_id=gene_id,
                                    gene_name=gene_name,
                                    chromosome=chromosome,
                                    strand=strand
                                )
                                db.add(gene)
                                db.flush()
                            gene_map[gene_id] = gene.id
                            gene_count += 1
                        
                        if transcript_id not in transcript_map:
                            transcript = db.query(Transcript).filter(Transcript.transcript_id == transcript_id).first()
                            if not transcript:
                                transcript = Transcript(
                                    transcript_id=transcript_id,
                                    gene_id=gene_map[gene_id]
                                )
                                db.add(transcript)
                                db.flush()
                            transcript_map[transcript_id] = transcript.id
                            transcript_count += 1
                        
                        transcript_db_id = transcript_map[transcript_id]
                        apa_site_key = f"{transcript_db_id}_{site_position}"
                        
                        existing_site = db.query(APASite).filter(
                            APASite.transcript_id == transcript_db_id,
                            APASite.site_position == site_position
                        ).first()
                        
                        if not existing_site:
                            apa_site = APASite(
                                site_id=site_id,
                                transcript_id=transcript_db_id,
                                species_id=species_id,
                                site_position=site_position,
                                sample_data=json.dumps([{
                                    'sample_name': sample_name,
                                    'site_count': site_count,
                                    'site_abundance': site_abundance
                                }])
                            )
                            db.add(apa_site)
                            db.flush()
                            apa_site_map[apa_site_key] = apa_site.id
                            apa_site_count += 1
                        else:
                            if existing_site and existing_site.sample_data:
                                sample_data_list = json.loads(existing_site.sample_data)
                            else:
                                sample_data_list = []
                            
                            sample_data_list.append({
                                'sample_name': sample_name,
                                'site_count': site_count,
                                'site_abundance': site_abundance
                            })
                            existing_site.sample_data = json.dumps(sample_data_list)
                
                db.commit()
                print(f"    Loaded {apa_site_count} unique APA sites so far...")
        
        print(f"\n=== Summary ===")
        print(f"Species: {species_count}")
        print(f"Samples: {sample_count}")
        print(f"Genes: {gene_count}")
        print(f"Transcripts: {transcript_count}")
        print(f"APA Sites (unique by position): {apa_site_count}")
        
        # Tier 1 Enhancement: Annotate APA sites with PAS motifs and APA types
        print(f"\n=== Tier 1 Annotations ===")
        for species_folder in os.listdir(DATA_DIR):
            species_path = os.path.join(DATA_DIR, species_folder)
            if not os.path.isdir(species_path) or species_folder.startswith('.'):
                continue
            
            # Get reference files
            gtf_path = get_gtf_path(species_folder)
            fasta_path = get_fasta_path(species_folder)
            
            if not gtf_path or not fasta_path:
                print(f"Skipping {species_folder}: missing GTF or FASTA files")
                continue
            
            print(f"\nAnnotating {species_folder}...")
            print(f"  GTF: {os.path.basename(gtf_path)}")
            print(f"  FASTA: {os.path.basename(fasta_path)}")
            
            # Initialize annotators
            pas_annotator = PASAnnotator(fasta_path)
            apa_classifier = APATypeClassifier(gtf_path)
            
            # Get species ID
            species_info = SPECIES_MAP.get(species_folder, {'name': species_folder})
            species = db.query(Species).filter(Species.name == species_info['name']).first()
            if not species:
                continue
            
            # Get all APA sites for this species
            apa_sites = db.query(APASite).join(Transcript).join(Gene).filter(
                APASite.species_id == species.id
            ).all()
            
            print(f"  Processing {len(apa_sites)} APA sites...")
            annotated_count = 0
            batch_size = 100
            
            for i, apa_site in enumerate(apa_sites):
                # Get transcript and gene info
                transcript = apa_site.transcript
                gene = transcript.gene
                
                pas_full = pas_annotator.annotate_site(
                    chrom=gene.chromosome,
                    position=apa_site.site_position,
                    strand=gene.strand
                )
                search_level = pas_full.get('search_level', 'none')

                if search_level == 'hexamer':
                    h = pas_full['hexamer']
                    apa_site.pas_motif      = h['motif']
                    apa_site.pas_position   = h['position']
                    apa_site.pas_type       = h['motif_type']
                    apa_site.pas_confidence = h['confidence']
                elif search_level in ('upstream', 'downstream'):
                    hits = pas_full['upstream_motifs'] or pas_full['downstream_motifs']
                    first = hits[0] if hits else {}
                    apa_site.pas_motif      = first.get('motif')
                    apa_site.pas_position   = first.get('offset')
                    apa_site.pas_type       = 'other'
                    apa_site.pas_confidence = 'low'
                else:
                    apa_site.pas_motif      = None
                    apa_site.pas_position   = None
                    apa_site.pas_type       = None
                    apa_site.pas_confidence = None
                
                # Classify APA type
                apa_result = apa_classifier.classify_apa_site(
                    transcript_id=transcript.transcript_id,
                    position=apa_site.site_position,
                    strand=gene.strand
                )
                apa_site.apa_type = apa_result['apa_type']
                apa_site.apa_region = apa_result['region']
                apa_site.apa_confidence = apa_result['confidence']
                
                annotated_count += 1
                
                # Commit in batches
                if (i + 1) % batch_size == 0:
                    db.commit()
                    print(f"    Annotated {i + 1}/{len(apa_sites)} sites...")
            
            # Final commit
            db.commit()
            print(f"  ✓ Annotated {annotated_count} sites for {species_folder}")
        
        print(f"\n✓ Annotation complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    data_dir = os.path.join(project_root, 'data')
    
    parser = argparse.ArgumentParser(description='Ingest APA sites data')
    parser.add_argument('--data-dir', default=data_dir, help='Data directory')
    args = parser.parse_args()
    
    ingest_data(args.data_dir)
