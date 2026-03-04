"""
Poly(A) Signal (PAS) Annotation Service

Scans genomic sequence upstream of APA cleavage sites to identify
canonical and variant poly(A) signal hexamers (e.g., AATAAA, ATTAAA).
"""

from typing import Optional, Tuple, Dict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PASAnnotator:
    """Annotates APA sites with poly(A) signal hexamers"""
    
    # Canonical PAS hexamers (strongest signals)
    CANONICAL_HEXAMERS = ['AATAAA', 'ATTAAA']
    
    # Variant PAS hexamers (weaker but functional)
    VARIANT_HEXAMERS = [
        'AGTAAA', 'TATAAA', 'CATAAA', 'GATAAA',
        'AATATA', 'AATACA', 'AATAGA', 'ACTAAA',
        'AAGAAA', 'AATGAA', 'TTTAAA', 'AAAACA',
        'GGGGCT'  # Non-canonical but observed
    ]
    
    def __init__(self, fasta_path: str):
        """
        Initialize PAS annotator with reference genome
        
        Args:
            fasta_path: Path to genome FASTA file
        """
        self.fasta_path = Path(fasta_path)
        self._sequences = {}  # Cache for loaded chromosomes
        
        if not self.fasta_path.exists():
            logger.warning(f"FASTA file not found: {fasta_path}")
    
    def _load_chromosome(self, chrom: str) -> Optional[str]:
        """
        Load chromosome sequence from FASTA file
        
        Args:
            chrom: Chromosome name (e.g., '1', 'X', 'chr1')
        
        Returns:
            Chromosome sequence as string, or None if not found
        """
        if chrom in self._sequences:
            return self._sequences[chrom]
        
        if not self.fasta_path.exists():
            return None
        
        try:
            sequence = []
            target_chrom = chrom.replace('chr', '')  # Normalize chromosome name
            current_chrom = None
            
            with open(self.fasta_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('>'):
                        # Header line
                        if sequence and current_chrom == target_chrom:
                            # Found and finished loading target chromosome
                            break
                        
                        # Parse chromosome name from header
                        # Format: >1 dna:chromosome chromosome:GRCh38:1:1:248956422:1
                        header_parts = line[1:].split()
                        current_chrom = header_parts[0]
                        
                        if current_chrom == target_chrom:
                            sequence = []
                    elif current_chrom == target_chrom:
                        sequence.append(line.upper())
            
            if sequence:
                seq_str = ''.join(sequence)
                self._sequences[chrom] = seq_str
                logger.info(f"Loaded chromosome {chrom}: {len(seq_str):,} bp")
                return seq_str
            
            logger.warning(f"Chromosome {chrom} not found in FASTA")
            return None
            
        except Exception as e:
            logger.error(f"Error loading chromosome {chrom}: {e}")
            return None
    
    def _reverse_complement(self, seq: str) -> str:
        """Return reverse complement of DNA sequence"""
        complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N'}
        return ''.join(complement.get(base, 'N') for base in reversed(seq))
    
    def find_pas_hexamer(
        self,
        chrom: str,
        position: int,
        strand: str,
        search_start: int = -50,
        search_end: int = -10
    ) -> Dict[str, any]:
        """
        Find poly(A) signal hexamer upstream of cleavage site
        
        Args:
            chrom: Chromosome (e.g., '7', 'chr7')
            position: Cleavage site position (1-based)
            strand: '+' or '-'
            search_start: Start of search window relative to cleavage site (default: -50bp)
            search_end: End of search window relative to cleavage site (default: -10bp)
        
        Returns:
            Dictionary with:
                - motif: Hexamer sequence (or None)
                - position: Distance from cleavage site (or None)
                - motif_type: 'canonical', 'variant', or None
                - confidence: 'high', 'medium', 'low', or None
        """
        # Normalize chromosome name
        chrom = chrom.replace('chr', '')
        
        # Load chromosome sequence
        seq = self._load_chromosome(chrom)
        if not seq:
            return {
                'motif': None,
                'position': None,
                'motif_type': None,
                'confidence': None
            }
        
        try:
            # Convert to 0-based indexing
            pos_0 = position - 1
            
            # Define search window
            if strand == '+':
                # For forward strand, search upstream (lower coordinates)
                window_start = max(0, pos_0 + search_start)
                window_end = max(0, pos_0 + search_end)
                search_seq = seq[window_start:window_end]
            else:
                # For reverse strand, search upstream (higher coordinates)
                # Need to reverse complement
                window_start = pos_0 - search_end
                window_end = pos_0 - search_start
                window_start = max(0, window_start)
                window_end = min(len(seq), window_end)
                search_seq = self._reverse_complement(seq[window_start:window_end])
            
            if len(search_seq) < 6:
                return {
                    'motif': None,
                    'position': None,
                    'motif_type': None,
                    'confidence': None
                }
            
            # Search for canonical hexamers first (highest priority)
            for hexamer in self.CANONICAL_HEXAMERS:
                idx = search_seq.find(hexamer)
                if idx != -1:
                    # Calculate distance from cleavage site
                    distance = search_start + idx
                    return {
                        'motif': hexamer,
                        'position': distance,
                        'motif_type': 'canonical',
                        'confidence': 'high'
                    }
            
            # Search for variant hexamers
            for hexamer in self.VARIANT_HEXAMERS:
                idx = search_seq.find(hexamer)
                if idx != -1:
                    distance = search_start + idx
                    return {
                        'motif': hexamer,
                        'position': distance,
                        'motif_type': 'variant',
                        'confidence': 'medium'
                    }
            
            # No hexamer found
            return {
                'motif': None,
                'position': None,
                'motif_type': None,
                'confidence': 'low'
            }
            
        except Exception as e:
            logger.error(f"Error finding PAS for {chrom}:{position}:{strand} - {e}")
            return {
                'motif': None,
                'position': None,
                'motif_type': None,
                'confidence': None
            }
    
    def annotate_batch(
        self,
        sites: list[Dict[str, any]]
    ) -> list[Dict[str, any]]:
        """
        Annotate multiple APA sites with PAS hexamers
        
        Args:
            sites: List of dicts with keys: chrom, position, strand
        
        Returns:
            List of annotation dicts (same as find_pas_hexamer)
        """
        results = []
        for site in sites:
            annotation = self.find_pas_hexamer(
                chrom=site['chrom'],
                position=site['position'],
                strand=site['strand']
            )
            results.append(annotation)
        return results
