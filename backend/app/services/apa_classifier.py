"""
APA Type Classification Service

Classifies APA sites based on their genomic location relative to gene structure:
- 3' UTR-APA: Sites in the 3' untranslated region (tandem)
- Intronic-APA: Sites within introns
- Internal Exon-APA: Sites within coding exons (premature termination)
"""

from typing import Optional, Dict, List, Tuple
import logging
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class GTFParser:
    """Parse GTF annotation file to extract gene structure"""
    
    def __init__(self, gtf_path: str):
        """
        Initialize GTF parser
        
        Args:
            gtf_path: Path to GTF annotation file
        """
        self.gtf_path = Path(gtf_path)
        self._gene_structures = {}  # Cache: transcript_id -> structure
        self._loaded = False
        
        if not self.gtf_path.exists():
            logger.warning(f"GTF file not found: {gtf_path}")
    
    def _parse_attributes(self, attr_str: str) -> Dict[str, str]:
        """Parse GTF attributes field"""
        attrs = {}
        for item in attr_str.strip().split(';'):
            item = item.strip()
            if not item:
                continue
            parts = item.split(' ', 1)
            if len(parts) == 2:
                key = parts[0]
                value = parts[1].strip('"')
                attrs[key] = value
        return attrs
    
    def load_transcript_structures(self, transcript_ids: Optional[set] = None):
        """
        Load gene structures for specified transcripts
        
        Args:
            transcript_ids: Set of transcript IDs to load (None = load all)
        """
        if not self.gtf_path.exists():
            logger.error(f"GTF file not found: {self.gtf_path}")
            return
        
        logger.info(f"Loading transcript structures from GTF...")
        
        try:
            transcript_data = defaultdict(lambda: {
                'exons': [],
                'cds': [],
                'utrs': [],
                'start_codon': None,
                'stop_codon': None,
                'chrom': None,
                'strand': None,
                'gene_id': None,
                'gene_name': None
            })
            
            with open(self.gtf_path, 'r') as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    
                    fields = line.strip().split('\t')
                    if len(fields) < 9:
                        continue
                    
                    chrom, source, feature, start, end, score, strand, frame, attributes = fields
                    attrs = self._parse_attributes(attributes)
                    
                    transcript_id = attrs.get('transcript_id')
                    if not transcript_id:
                        continue
                    
                    # Filter by transcript_ids if specified
                    if transcript_ids and transcript_id not in transcript_ids:
                        continue
                    
                    start = int(start)
                    end = int(end)
                    
                    # Store basic info
                    if not transcript_data[transcript_id]['chrom']:
                        transcript_data[transcript_id]['chrom'] = chrom
                        transcript_data[transcript_id]['strand'] = strand
                        transcript_data[transcript_id]['gene_id'] = attrs.get('gene_id')
                        transcript_data[transcript_id]['gene_name'] = attrs.get('gene_name')
                    
                    # Store features
                    if feature == 'exon':
                        transcript_data[transcript_id]['exons'].append((start, end))
                    elif feature == 'CDS':
                        transcript_data[transcript_id]['cds'].append((start, end))
                    elif feature == 'UTR' or feature == 'three_prime_utr' or feature == '3UTR':
                        transcript_data[transcript_id]['utrs'].append((start, end))
                    elif feature == 'start_codon':
                        transcript_data[transcript_id]['start_codon'] = (start, end)
                    elif feature == 'stop_codon':
                        transcript_data[transcript_id]['stop_codon'] = (start, end)
            
            # Convert to regular dict and sort intervals
            for transcript_id, data in transcript_data.items():
                data['exons'].sort()
                data['cds'].sort()
                data['utrs'].sort()
                self._gene_structures[transcript_id] = dict(data)
            
            logger.info(f"Loaded {len(self._gene_structures)} transcript structures")
            self._loaded = True
            
        except Exception as e:
            logger.error(f"Error loading GTF: {e}")
    
    def get_transcript_structure(self, transcript_id: str) -> Optional[Dict]:
        """Get gene structure for a transcript"""
        return self._gene_structures.get(transcript_id)


class APATypeClassifier:
    """Classify APA sites based on genomic location"""
    
    def __init__(self, gtf_path: str):
        """
        Initialize APA type classifier
        
        Args:
            gtf_path: Path to GTF annotation file
        """
        self.parser = GTFParser(gtf_path)
    
    def load_transcripts(self, transcript_ids: set):
        """Load gene structures for specified transcripts"""
        self.parser.load_transcript_structures(transcript_ids)
    
    def _point_in_intervals(self, position: int, intervals: List[Tuple[int, int]]) -> bool:
        """Check if a position falls within any interval"""
        for start, end in intervals:
            if start <= position <= end:
                return True
        return False
    
    def _infer_3prime_utr(
        self,
        position: int,
        structure: Dict,
        strand: str
    ) -> bool:
        """
        Infer if position is in 3' UTR based on exons and CDS
        
        For transcripts without explicit UTR annotations:
        - Forward strand: 3' UTR is after last CDS position
        - Reverse strand: 3' UTR is before first CDS position
        """
        if not structure['exons'] or not structure['cds']:
            return False
        
        # Check if position is in any exon
        in_exon = self._point_in_intervals(position, structure['exons'])
        if not in_exon:
            return False
        
        # Check if position is NOT in CDS
        in_cds = self._point_in_intervals(position, structure['cds'])
        if in_cds:
            return False
        
        # For forward strand, 3' UTR is downstream of last CDS
        if strand == '+':
            last_cds_end = max(end for start, end in structure['cds'])
            if position > last_cds_end:
                return True
        # For reverse strand, 3' UTR is upstream of first CDS
        else:
            first_cds_start = min(start for start, end in structure['cds'])
            if position < first_cds_start:
                return True
        
        return False
    
    def classify_apa_site(
        self,
        transcript_id: str,
        position: int,
        strand: str
    ) -> Dict[str, any]:
        """
        Classify an APA site by its genomic location
        
        Args:
            transcript_id: Transcript identifier
            position: APA site genomic position (1-based)
            strand: '+' or '-'
        
        Returns:
            Dictionary with:
                - apa_type: '3UTR-APA', 'Intronic-APA', 'Exonic-APA', or 'Unknown'
                - region: Detailed region description
                - confidence: 'high', 'medium', 'low'
        """
        structure = self.parser.get_transcript_structure(transcript_id)
        
        if not structure:
            return {
                'apa_type': 'Unknown',
                'region': 'No annotation',
                'confidence': 'low'
            }
        
        # Check explicit UTR annotations first
        if structure['utrs']:
            if self._point_in_intervals(position, structure['utrs']):
                return {
                    'apa_type': '3UTR-APA',
                    'region': "3' UTR",
                    'confidence': 'high'
                }
        
        # Check if in CDS (coding sequence)
        if structure['cds']:
            if self._point_in_intervals(position, structure['cds']):
                return {
                    'apa_type': 'Exonic-APA',
                    'region': 'Coding exon',
                    'confidence': 'high'
                }
        
        # Check if in exon (but not CDS) - could be UTR
        if structure['exons']:
            if self._point_in_intervals(position, structure['exons']):
                # Infer 3' UTR
                if self._infer_3prime_utr(position, structure, strand):
                    return {
                        'apa_type': '3UTR-APA',
                        'region': "3' UTR (inferred)",
                        'confidence': 'medium'
                    }
                else:
                    # In exon but not CDS and not 3' UTR - possibly 5' UTR or non-coding
                    return {
                        'apa_type': 'Exonic-APA',
                        'region': 'Non-coding exon',
                        'confidence': 'medium'
                    }
        
        # Not in any exon - must be intronic
        return {
            'apa_type': 'Intronic-APA',
            'region': 'Intron',
            'confidence': 'medium'
        }
    
    def classify_batch(
        self,
        sites: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        Classify multiple APA sites
        
        Args:
            sites: List of dicts with keys: transcript_id, position, strand
        
        Returns:
            List of classification dicts
        """
        # Load all needed transcript structures
        transcript_ids = {site['transcript_id'] for site in sites}
        self.load_transcripts(transcript_ids)
        
        # Classify each site
        results = []
        for site in sites:
            classification = self.classify_apa_site(
                transcript_id=site['transcript_id'],
                position=site['position'],
                strand=site['strand']
            )
            results.append(classification)
        
        return results
