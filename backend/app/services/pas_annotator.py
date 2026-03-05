"""
Poly(A) Signal (PAS) Annotation Service

Annotation priority (stop at first hit):
  1. Hexamer PAS motifs       — upstream  -40 to -1 nt
  2. Upstream auxiliary 4-mers— upstream  -40 to -1 nt  (only if no hexamer found)
  3. Downstream auxiliary 4-mers— downstream +1 to +40 nt (only if no upstream hit)

Search windows (relative to cleavage site):
  Hexamer / upstream 4-mers : -40 to -1
    The hexamer sits 10–35 nt upstream; ending at -1 (not -10) catches sites
    positioned close to the cleavage point. Starting upstream at -40 covers
    the full observed range (Beaudoing et al. 2000).
  Downstream 4-mers         : +1 to +40
    DSEs appear immediately after the cleavage site; starting at +1 is correct.

Hexamer catalogue (18 motifs):
  Canonical (2) : AATAAA, ATTAAA
  Variant  (16) : AGTAAA, TATAAA, CATAAA, GATAAA, AATATA, AATACA, AATAGA,
                  ACTAAA, AAGAAA, AATGAA, TTTAAA, AAAACA, GGGGCT,
                  AAAAAG, AAAAAA

Upstream 4-mer auxiliary motifs:
                  TGTA, TATA, ATAT, TTTT

Downstream 4-mer auxiliary motifs (DSEs):
                  TGTG, GTGT, TTTT, GGGG

References:
  Beaudoing et al. 2000 (Genome Research) — hexamer catalogue & window
  Tian & Manley 2017 (Nature Reviews Genetics) — auxiliary upstream/downstream elements
"""

from typing import Optional, Dict, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PASAnnotator:
    """Annotates APA sites with poly(A) signal hexamers and auxiliary motifs."""

    # ------------------------------------------------------------------ #
    # Hexamer catalogue                                                    #
    # ------------------------------------------------------------------ #

    # Strongest signals — searched first
    CANONICAL_HEXAMERS: List[str] = ['AATAAA', 'ATTAAA']

    # Weaker but functional single-nucleotide variants + others
    VARIANT_HEXAMERS: List[str] = [
        'AGTAAA', 'TATAAA', 'CATAAA', 'GATAAA',
        'AATATA', 'AATACA', 'AATAGA', 'ACTAAA',
        'AAGAAA', 'AATGAA', 'TTTAAA', 'AAAACA',
        'GGGGCT',   # non-canonical but observed
        'AAAAAG',   # from Beaudoing et al. [41]
        'AAAAAA',   # A-rich, from Beaudoing et al. [41]
    ]

    # ------------------------------------------------------------------ #
    # Auxiliary 4-mer motifs                                               #
    # ------------------------------------------------------------------ #

    # Found in the region UPSTREAM of the cleavage site (-40 to -10 nt)
    UPSTREAM_4MER: List[str] = ['TGTA', 'TATA', 'ATAT', 'TTTT']

    # Found in the region DOWNSTREAM of the cleavage site (+1 to +40 nt)
    DOWNSTREAM_4MER: List[str] = ['TGTG', 'GTGT', 'TTTT', 'GGGG']

    # ------------------------------------------------------------------ #
    # Search windows (relative to cleavage site, 1-based)                 #
    # Hexamer sits 10-35 nt upstream; end at -1 (not -10) to catch        #
    # edge cases close to the cleavage point.                              #
    # ------------------------------------------------------------------ #
    HEXAMER_UPSTREAM_START: int = -40
    HEXAMER_UPSTREAM_END: int   =  -1
    AUX_UPSTREAM_START: int     = -40
    AUX_UPSTREAM_END: int       =  -1
    AUX_DOWNSTREAM_START: int   =  +1
    AUX_DOWNSTREAM_END: int     = +40

    # ------------------------------------------------------------------ #

    def __init__(self, fasta_path: str) -> None:
        """
        Args:
            fasta_path: Path to reference genome FASTA file.
        """
        self.fasta_path = Path(fasta_path)
        self._sequences: Dict[str, str] = {}   # chromosome sequence cache

        if not self.fasta_path.exists():
            logger.warning(f"FASTA file not found: {fasta_path}")

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _load_chromosome(self, chrom: str) -> Optional[str]:
        """Load (and cache) a chromosome sequence from the FASTA file."""
        if chrom in self._sequences:
            return self._sequences[chrom]

        if not self.fasta_path.exists():
            return None

        try:
            sequence: List[str] = []
            target = chrom.replace('chr', '')
            current: Optional[str] = None

            with open(self.fasta_path, 'r') as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith('>'):
                        if sequence and current == target:
                            break
                        # Header format: >1 dna:chromosome chromosome:GRCh38:1:…
                        current = line[1:].split()[0]
                        if current == target:
                            sequence = []
                    elif current == target:
                        sequence.append(line.upper())

            if sequence:
                seq_str = ''.join(sequence)
                self._sequences[chrom] = seq_str
                logger.info(f"Loaded chromosome {chrom}: {len(seq_str):,} bp")
                return seq_str

            logger.warning(f"Chromosome {chrom} not found in FASTA")
            return None

        except Exception as exc:
            logger.error(f"Error loading chromosome {chrom}: {exc}")
            return None

    @staticmethod
    def _reverse_complement(seq: str) -> str:
        """Return the reverse complement of a DNA sequence."""
        table = str.maketrans('ACGTN', 'TGCAN')
        return seq.translate(table)[::-1]

    def _extract_window(
        self,
        seq: str,
        pos_0: int,
        rel_start: int,
        rel_end: int,
        strand: str,
    ) -> str:
        """
        Extract a subsequence window relative to a cleavage site.

        For '+' strand  : window = seq[pos_0 + rel_start : pos_0 + rel_end]
        For '-' strand  : mirror coordinates, then reverse-complement.

        Args:
            seq      : Full chromosome sequence (0-based).
            pos_0    : Cleavage site position (0-based).
            rel_start: Window start relative to cleavage site (may be negative).
            rel_end  : Window end relative to cleavage site (may be negative).
            strand   : '+' or '-'.

        Returns:
            Extracted sequence (forward-strand orientation).
        """
        if strand == '+':
            start = max(0, pos_0 + rel_start)
            end   = max(0, pos_0 + rel_end)
            return seq[start:end]
        else:
            # On '-' strand, "upstream" means higher genomic coordinates
            # Mirror: upstream (-40..-10) → pos_0 + 10 .. pos_0 + 40
            start = max(0, pos_0 - rel_end)
            end   = min(len(seq), pos_0 - rel_start)
            return self._reverse_complement(seq[start:end])

    def _search_motifs(
        self,
        window_seq: str,
        motifs: List[str],
    ) -> List[Dict]:
        """
        Find ALL occurrences of each motif in window_seq.

        Returns a list of dicts with keys: motif, offset (0-based within window).
        """
        hits = []
        for motif in motifs:
            start = 0
            while True:
                idx = window_seq.find(motif, start)
                if idx == -1:
                    break
                hits.append({'motif': motif, 'offset': idx})
                start = idx + 1
        return hits

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def find_pas_hexamer(
        self,
        chrom: str,
        position: int,
        strand: str,
        search_start: int = -40,
        search_end: int   = -1,
    ) -> Dict:
        """
        Find the highest-priority PAS hexamer upstream of a cleavage site.

        Args:
            chrom       : Chromosome (e.g. '7', 'chr7').
            position    : Cleavage site (1-based).
            strand      : '+' or '-'.
            search_start: Upstream window start relative to site (default -40).
            search_end  : Upstream window end relative to site (default -10).

        Returns:
            Dict with keys: motif, position (distance), motif_type, confidence.
        """
        chrom = chrom.replace('chr', '')
        seq   = self._load_chromosome(chrom)
        empty = {'motif': None, 'position': None, 'motif_type': None, 'confidence': None}

        if not seq:
            return empty

        try:
            pos_0      = position - 1
            window_seq = self._extract_window(seq, pos_0, search_start, search_end, strand)

            if len(window_seq) < 6:
                return empty

            for hexamer in self.CANONICAL_HEXAMERS:
                idx = window_seq.find(hexamer)
                if idx != -1:
                    return {
                        'motif'     : hexamer,
                        'position'  : search_start + idx,
                        'motif_type': 'canonical',
                        'confidence': 'high',
                    }

            for hexamer in self.VARIANT_HEXAMERS:
                idx = window_seq.find(hexamer)
                if idx != -1:
                    return {
                        'motif'     : hexamer,
                        'position'  : search_start + idx,
                        'motif_type': 'variant',
                        'confidence': 'medium',
                    }

            return {'motif': None, 'position': None, 'motif_type': None, 'confidence': 'low'}

        except Exception as exc:
            logger.error(f"Error finding PAS hexamer for {chrom}:{position}:{strand} — {exc}")
            return empty

    def find_auxiliary_motifs(
        self,
        chrom: str,
        position: int,
        strand: str,
    ) -> Dict:
        """
        Find auxiliary 4-mer motifs in the upstream and downstream regions.

        Args:
            chrom   : Chromosome.
            position: Cleavage site (1-based).
            strand  : '+' or '-'.

        Returns:
            Dict with keys:
                upstream_motifs  : list of {motif, offset} found upstream
                downstream_motifs: list of {motif, offset} found downstream
        """
        chrom = chrom.replace('chr', '')
        seq   = self._load_chromosome(chrom)

        if not seq:
            return {'upstream_motifs': [], 'downstream_motifs': []}

        try:
            pos_0 = position - 1

            up_window   = self._extract_window(
                seq, pos_0, self.AUX_UPSTREAM_START, self.AUX_UPSTREAM_END, strand)
            down_window = self._extract_window(
                seq, pos_0, self.AUX_DOWNSTREAM_START, self.AUX_DOWNSTREAM_END, strand)

            return {
                'upstream_motifs'  : self._search_motifs(up_window,   self.UPSTREAM_4MER),
                'downstream_motifs': self._search_motifs(down_window, self.DOWNSTREAM_4MER),
            }

        except Exception as exc:
            logger.error(f"Error finding auxiliary motifs for {chrom}:{position}:{strand} — {exc}")
            return {'upstream_motifs': [], 'downstream_motifs': []}

    def annotate_site(
        self,
        chrom: str,
        position: int,
        strand: str,
    ) -> Dict:
        """
        Full annotation for a single APA site using priority-based search:
          1. Hexamer found          → return immediately, skip aux motifs
          2. No hexamer, upstream found  → return upstream hits, skip downstream
          3. No hexamer or upstream → return downstream hits
          4. Nothing found          → return all empty

        Returns:
            {
                hexamer           : {motif, position, motif_type, confidence},
                upstream_motifs   : [{motif, offset}, ...],
                downstream_motifs : [{motif, offset}, ...],
                search_level      : 'hexamer' | 'upstream' | 'downstream' | 'none'
            }
        """
        empty_result = {
            'hexamer'          : {'motif': None, 'position': None, 'motif_type': None, 'confidence': None},
            'upstream_motifs'  : [],
            'downstream_motifs': [],
            'search_level'     : 'none',
        }

        chrom_norm = chrom.replace('chr', '')
        seq = self._load_chromosome(chrom_norm)
        if not seq:
            return empty_result

        pos_0 = position - 1

        # --- Level 1: hexamer ---
        hexamer = self.find_pas_hexamer(chrom, position, strand)
        if hexamer['motif'] is not None:
            return {
                'hexamer'          : hexamer,
                'upstream_motifs'  : [],
                'downstream_motifs': [],
                'search_level'     : 'hexamer',
            }

        # --- Level 2: upstream 4-mers ---
        up_window = self._extract_window(
            seq, pos_0, self.AUX_UPSTREAM_START, self.AUX_UPSTREAM_END, strand)
        upstream_hits = self._search_motifs(up_window, self.UPSTREAM_4MER)
        if upstream_hits:
            return {
                'hexamer'          : hexamer,
                'upstream_motifs'  : upstream_hits,
                'downstream_motifs': [],
                'search_level'     : 'upstream',
            }

        # --- Level 3: downstream 4-mers ---
        down_window = self._extract_window(
            seq, pos_0, self.AUX_DOWNSTREAM_START, self.AUX_DOWNSTREAM_END, strand)
        downstream_hits = self._search_motifs(down_window, self.DOWNSTREAM_4MER)
        if downstream_hits:
            return {
                'hexamer'          : hexamer,
                'upstream_motifs'  : [],
                'downstream_motifs': downstream_hits,
                'search_level'     : 'downstream',
            }

        return empty_result

    def annotate_batch(
        self,
        sites: List[Dict],
    ) -> List[Dict]:
        """
        Annotate multiple APA sites (backward-compatible with old API).

        Args:
            sites: List of dicts with keys: chrom, position, strand.

        Returns:
            List of hexamer annotation dicts (same shape as find_pas_hexamer).
        """
        return [
            self.find_pas_hexamer(
                chrom    = s['chrom'],
                position = s['position'],
                strand   = s['strand'],
            )
            for s in sites
        ]

    def annotate_batch_full(
        self,
        sites: List[Dict],
    ) -> List[Dict]:
        """
        Full annotation for a batch of APA sites (hexamer + auxiliary motifs).

        Args:
            sites: List of dicts with keys: chrom, position, strand.

        Returns:
            List of full annotation dicts (same shape as annotate_site).
        """
        return [
            self.annotate_site(
                chrom    = s['chrom'],
                position = s['position'],
                strand   = s['strand'],
            )
            for s in sites
        ]
