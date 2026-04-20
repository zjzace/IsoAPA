"""
APA Type Classification Service

Classifies APA sites based on their genomic location relative to gene structure:
- 3' UTR-APA: Sites in the 3' untranslated region (tandem)
- Intronic-APA: Sites within introns
- Internal Exon-APA: Sites within coding exons (premature termination)
"""

from typing import Optional, Dict, List, Tuple
import logging
import json
import os
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class BED12Parser:
    """Parse BED12 annotation file to extract gene structure"""

    def __init__(self, bed12_path: str):
        """
        Initialize BED12 parser

        Args:
            bed12_path: Path to BED12 annotation file (.bed)
        """
        self.bed12_path = Path(bed12_path)
        self._index: dict = {}           # transcript_id -> [offset, length]
        self._index_loaded = False
        self._gene_structures: dict = {} # transcript_id -> structure dict

        if not self.bed12_path.exists():
            logger.warning(f"BED12 file not found: {bed12_path}")

    def _load_index(self):
        if self._index_loaded:
            return
        idx_path = str(self.bed12_path) + ".bidx"
        if not os.path.exists(idx_path):
            logger.error(f"BED12 index not found: {idx_path}")
            self._index_loaded = True
            return
        with open(idx_path, "r") as f:
            self._index = json.load(f)
        self._index_loaded = True

    def _fetch_record(self, transcript_id: str) -> Optional[dict]:
        """Fetch and parse a single BED12 record by transcript_id."""
        self._load_index()
        span = self._index.get(transcript_id)
        if not span:
            return None
        offset, length = span
        with open(self.bed12_path, "rb") as f:
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

    def _parse_structure(self, rec: dict) -> dict:
        """Convert a BED12 record into exons/cds/utrs (1-based inclusive)."""
        chrom_start = rec["chrom_start"]
        thick_start = rec["thick_start"]
        thick_end = rec["thick_end"]
        has_cds = thick_start < thick_end

        exons, cds, utrs = [], [], []

        for size, rel_start in zip(rec["block_sizes"], rec["block_starts"]):
            abs_start = chrom_start + rel_start          # 0-based
            abs_end = abs_start + size                   # 0-based exclusive

            exon_s = abs_start + 1                       # 1-based inclusive
            exon_e = abs_end                             # 1-based inclusive
            exons.append((exon_s, exon_e))

            if has_cds:
                cds_s_0 = max(abs_start, thick_start)
                cds_e_0 = min(abs_end, thick_end)
                if cds_s_0 < cds_e_0:
                    cds.append((cds_s_0 + 1, cds_e_0))
                # UTR portions within this block
                if abs_start < thick_start:
                    utrs.append((exon_s, min(thick_start, abs_end)))
                if abs_end > thick_end:
                    utrs.append((max(thick_end + 1, abs_start + 1), exon_e))
            else:
                utrs.append((exon_s, exon_e))

        return {
            "chrom": rec["chrom"],
            "strand": rec["strand"],
            "exons": sorted(exons),
            "cds": sorted(cds),
            "utrs": sorted(utrs),
        }

    def load_transcript_structures(self, transcript_ids: Optional[set] = None):
        """
        Load gene structures for specified transcripts.

        Args:
            transcript_ids: Set of transcript IDs to load (None = load all indexed)
        """
        if not self.bed12_path.exists():
            logger.error(f"BED12 file not found: {self.bed12_path}")
            return

        self._load_index()

        ids_to_load = transcript_ids if transcript_ids else set(self._index.keys())
        loaded = 0
        for tid in ids_to_load:
            rec = self._fetch_record(tid)
            if rec is None:
                continue
            self._gene_structures[tid] = self._parse_structure(rec)
            loaded += 1

        logger.info(f"Loaded {loaded} transcript structures from BED12")

    def get_transcript_structure(self, transcript_id: str) -> Optional[Dict]:
        """Get gene structure for a transcript."""
        return self._gene_structures.get(transcript_id)


class APATypeClassifier:
    """Classify APA sites based on genomic location"""

    def __init__(self, bed12_path: str):
        """
        Initialize APA type classifier

        Args:
            bed12_path: Path to BED12 annotation file
        """
        self.parser = BED12Parser(bed12_path)

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

        in_exon = self._point_in_intervals(position, structure['exons'])
        if not in_exon:
            return False

        in_cds = self._point_in_intervals(position, structure['cds'])
        if in_cds:
            return False

        if strand == '+':
            last_cds_end = max(end for start, end in structure['cds'])
            if position > last_cds_end:
                return True
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

        if structure['utrs']:
            if self._point_in_intervals(position, structure['utrs']):
                return {
                    'apa_type': '3UTR-APA',
                    'region': "3' UTR",
                    'confidence': 'high'
                }

        if structure['cds']:
            if self._point_in_intervals(position, structure['cds']):
                return {
                    'apa_type': 'Exonic-APA',
                    'region': 'Coding exon',
                    'confidence': 'high'
                }

        if structure['exons']:
            if self._point_in_intervals(position, structure['exons']):
                if self._infer_3prime_utr(position, structure, strand):
                    return {
                        'apa_type': '3UTR-APA',
                        'region': "3' UTR (inferred)",
                        'confidence': 'medium'
                    }
                else:
                    return {
                        'apa_type': 'Exonic-APA',
                        'region': 'Non-coding exon',
                        'confidence': 'medium'
                    }

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
        transcript_ids = {site['transcript_id'] for site in sites}
        self.load_transcripts(transcript_ids)

        results = []
        for site in sites:
            classification = self.classify_apa_site(
                transcript_id=site['transcript_id'],
                position=site['position'],
                strand=site['strand']
            )
            results.append(classification)

        return results
