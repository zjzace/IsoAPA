#!/usr/bin/env python3
"""
annotate_apa.py — Standalone APA cluster annotation script.

For each unique PA cluster (cluster_key) in a unified APA sites file:
  1. Determines the cluster genomic range: min/max of original_site_position
  2. Extracts ±50 bp sequence around mode_site_position (5'→3' gene-strand)
  3. Searches for PAS signals using a 3-level priority cascade
  4. Writes one annotation row per cluster to an output TSV

Usage:
    python annotate_apa.py \\
        --unified-file data/homo_sapiens/Homo_sapiens_unified_apa_sites.txt \\
        --fasta data/homo_sapiens/reference/GCF_000001405.40_GRCh38.p14_genomic.fna \\
        --output data/homo_sapiens/Homo_sapiens_apa_annotation.tsv

Output TSV columns:
    cluster_key         – unique gene-level cluster identifier
    unified_ID          – coordinate label from the unifier
    chromosome          – RefSeq chromosome (e.g. NC_000001.11)
    strand              – '+' or '-'
    mode_site_position  – representative cleavage position (1-based)
    cluster_start       – min(original_site_position) across all rows
    cluster_end         – max(original_site_position) across all rows
    sequence            – 101 bp window (±50 bp) centred on mode_site_position, 5'→3' on gene strand
    pas_motif           – best motif found (hexamer or 4-mer), or '' if none
    pas_position        – distance from cleavage site to motif start, or ''
    pas_type            – 'canonical' | 'variant' | 'upstream' | 'downstream' | ''
    search_level        – 'hexamer' | 'upstream' | 'downstream' | 'none'
    apa_level           – APA-L1..APA-L5 confidence label from PAS type and support

Notes:
  - A .fidx JSON index is built automatically alongside the FASTA on first run
    (or when the FASTA is newer than the index). Subsequent runs reuse it.
  - Resume: clusters already present in the output file are skipped automatically
    by cluster_key.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

_INDEX_CACHE: Dict[str, dict] = {}


def _build_fasta_index(fasta_path: str) -> None:
    idx_path = fasta_path + ".fidx"
    if os.path.exists(idx_path) and os.path.getmtime(idx_path) >= os.path.getmtime(
        fasta_path
    ):
        return
    log.info(f"Building FASTA index for {fasta_path} ...")
    t0 = time.time()
    index: Dict[str, dict] = {}
    current_chrom: Optional[str] = None
    first_base_offset: Optional[int] = None
    line_len: Optional[int] = None
    line_bytes: Optional[int] = None
    accumulated_len = 0
    with open(fasta_path, "rb") as fh:
        while True:
            pos = fh.tell()
            raw = fh.readline()
            if not raw:
                break
            line = raw.decode("ascii", errors="replace")
            if line.startswith(">"):
                if current_chrom is not None:
                    index[current_chrom] = {
                        "offset": first_base_offset,
                        "length": accumulated_len,
                        "line_len": line_len,
                        "line_bytes": line_bytes,
                    }
                current_chrom = line[1:].split()[0]
                first_base_offset = None
                line_len = None
                line_bytes = None
                accumulated_len = 0
            else:
                bases = raw.rstrip(b"\r\n")
                if not bases:
                    continue
                if first_base_offset is None:
                    first_base_offset = pos
                    line_len = len(bases)
                    line_bytes = len(raw)
                accumulated_len += len(bases)
    if current_chrom is not None:
        index[current_chrom] = {
            "offset": first_base_offset,
            "length": accumulated_len,
            "line_len": line_len,
            "line_bytes": line_bytes,
        }
    with open(idx_path, "w") as fh:
        json.dump(index, fh)
    log.info(
        f"Index built: {len(index):,} sequences in {time.time() - t0:.1f}s → {idx_path}"
    )


def _load_fasta_index(fasta_path: str) -> dict:
    if fasta_path not in _INDEX_CACHE:
        with open(fasta_path + ".fidx") as fh:
            _INDEX_CACHE[fasta_path] = json.load(fh)
        log.info(f"Loaded FASTA index ({len(_INDEX_CACHE[fasta_path]):,} chroms)")
    return _INDEX_CACHE[fasta_path]


def _fetch_seq(fasta_path: str, chrom: str, start: int, end: int) -> str:
    idx = _load_fasta_index(fasta_path)
    entry = idx.get(chrom) or idx.get(chrom.lstrip("chr")) or idx.get("chr" + chrom)
    if not entry:
        return ""
    chrom_len = int(entry.get("length") or 0)
    start = max(0, int(start))
    end = min(chrom_len, int(end))
    if end <= start:
        return ""
    start = max(0, start)
    offset, line_len, line_bytes = (
        entry["offset"],
        entry["line_len"],
        entry["line_bytes"],
    )
    if not line_len or not line_bytes:
        return ""
    byte_start = offset + (start // line_len) * line_bytes + (start % line_len)
    byte_end = (
        offset + ((end - 1) // line_len) * line_bytes + ((end - 1) % line_len) + 1
    )
    with open(fasta_path, "rb") as fh:
        fh.seek(byte_start)
        raw = fh.read(byte_end - byte_start)
    return (
        raw.replace(b"\n", b"")
        .replace(b"\r", b"")
        .decode("ascii", errors="replace")
        .upper()[: end - start]
    )


_CHROM_CACHE: Dict[str, str] = {}


def _get_chrom_seq(fasta_path: str, chrom: str) -> str:
    if chrom not in _CHROM_CACHE:
        _CHROM_CACHE[chrom] = _fetch_seq(fasta_path, chrom, 0, 10**9)
    return _CHROM_CACHE[chrom]


def _rev_comp(seq: str) -> str:
    return seq.translate(str.maketrans("ACGTNacgtn", "TGCANtgcan"))[::-1]


FLANK = 50


def _extract_sequence(chrom_seq: str, pos_1: int, strand: str) -> str:
    if not chrom_seq:
        return ""
    pos_0 = pos_1 - 1
    seq = chrom_seq[max(0, pos_0 - FLANK) : min(len(chrom_seq), pos_0 + FLANK + 1)]
    return _rev_comp(seq) if strand == "-" else seq


def _fetch_sequence(fasta_path: str, chrom: str, pos_1: int, strand: str) -> str:
    pos_0 = pos_1 - 1
    seq = _fetch_seq(fasta_path, chrom, pos_0 - FLANK, pos_0 + FLANK + 1)
    return _rev_comp(seq) if strand == "-" else seq


def _extract_window(
    chrom_seq: str, pos_0: int, rel_start: int, rel_end: int, strand: str
) -> str:
    if strand == "+":
        return chrom_seq[max(0, pos_0 + rel_start) : max(0, pos_0 + rel_end)]
    else:
        return _rev_comp(
            chrom_seq[max(0, pos_0 - rel_end) : min(len(chrom_seq), pos_0 - rel_start)]
        )


def _fetch_window(
    fasta_path: str,
    chrom: str,
    pos_0: int,
    rel_start: int,
    rel_end: int,
    strand: str,
) -> str:
    if strand == "+":
        return _fetch_seq(fasta_path, chrom, pos_0 + rel_start, pos_0 + rel_end)
    return _rev_comp(_fetch_seq(fasta_path, chrom, pos_0 - rel_end, pos_0 - rel_start))


CANONICAL_HEXAMERS: List[str] = ["AATAAA", "ATTAAA"]

VARIANT_HEXAMERS: List[str] = [
    "AGTAAA",
    "TATAAA",
    "CATAAA",
    "GATAAA",
    "AATATA",
    "AATACA",
    "AATAGA",
    "ACTAAA",
    "AAGAAA",
    "AATGAA",
    "TTTAAA",
    "AAAACA",
    "GGGGCT",
    "AAAAAG",
    "AAAAAA",
]

UPSTREAM_4MER: List[str] = ["TGTA", "TATA", "ATAT", "TTTT"]
DOWNSTREAM_4MER: List[str] = ["TGTG", "GTGT", "TTTT", "GGGG"]

HEXAMER_START = -40
HEXAMER_END = -1
AUX_UP_START = -40
AUX_UP_END = -1
AUX_DOWN_START = +1
AUX_DOWN_END = +40


def _first_hit(window: str, motifs: List[str]) -> Optional[str]:
    for motif in motifs:
        if window.find(motif) != -1:
            return motif
    return None


def annotate_site(chrom_seq: str, pos_1: int, strand: str) -> Dict:
    empty = {
        "motif": None,
        "position": None,
        "motif_type": None,
        "search_level": "none",
    }
    if not chrom_seq:
        return empty

    pos_0 = pos_1 - 1

    up = _extract_window(chrom_seq, pos_0, HEXAMER_START, HEXAMER_END, strand)
    if len(up) >= 6:
        hit = _first_hit(up, CANONICAL_HEXAMERS)
        if hit:
            return {
                "motif": hit,
                "position": HEXAMER_START + up.find(hit),
                "motif_type": "canonical",
                "search_level": "hexamer",
            }
        hit = _first_hit(up, VARIANT_HEXAMERS)
        if hit:
            return {
                "motif": hit,
                "position": HEXAMER_START + up.find(hit),
                "motif_type": "variant",
                "search_level": "hexamer",
            }

    aux_up = _extract_window(chrom_seq, pos_0, AUX_UP_START, AUX_UP_END, strand)
    hit = _first_hit(aux_up, UPSTREAM_4MER)
    if hit:
        return {
            "motif": hit,
            "position": AUX_UP_START + aux_up.find(hit),
            "motif_type": "upstream",
            "search_level": "upstream",
        }

    aux_down = _extract_window(chrom_seq, pos_0, AUX_DOWN_START, AUX_DOWN_END, strand)
    hit = _first_hit(aux_down, DOWNSTREAM_4MER)
    if hit:
        return {
            "motif": hit,
            "position": AUX_DOWN_START + aux_down.find(hit),
            "motif_type": "downstream",
            "search_level": "downstream",
        }

    return empty


def annotate_site_from_fasta(fasta_path: str, chrom: str, pos_1: int, strand: str) -> Dict:
    empty = {
        "motif": None,
        "position": None,
        "motif_type": None,
        "search_level": "none",
    }

    pos_0 = pos_1 - 1

    up = _fetch_window(fasta_path, chrom, pos_0, HEXAMER_START, HEXAMER_END, strand)
    if len(up) >= 6:
        hit = _first_hit(up, CANONICAL_HEXAMERS)
        if hit:
            return {
                "motif": hit,
                "position": HEXAMER_START + up.find(hit),
                "motif_type": "canonical",
                "search_level": "hexamer",
            }
        hit = _first_hit(up, VARIANT_HEXAMERS)
        if hit:
            return {
                "motif": hit,
                "position": HEXAMER_START + up.find(hit),
                "motif_type": "variant",
                "search_level": "hexamer",
            }

    aux_up = _fetch_window(fasta_path, chrom, pos_0, AUX_UP_START, AUX_UP_END, strand)
    hit = _first_hit(aux_up, UPSTREAM_4MER)
    if hit:
        return {
            "motif": hit,
            "position": AUX_UP_START + aux_up.find(hit),
            "motif_type": "upstream",
            "search_level": "upstream",
        }

    aux_down = _fetch_window(
        fasta_path, chrom, pos_0, AUX_DOWN_START, AUX_DOWN_END, strand
    )
    hit = _first_hit(aux_down, DOWNSTREAM_4MER)
    if hit:
        return {
            "motif": hit,
            "position": AUX_DOWN_START + aux_down.find(hit),
            "motif_type": "downstream",
            "search_level": "downstream",
        }

    return empty


OUTPUT_COLUMNS = [
    "cluster_key",
    "unified_ID",
    "chromosome",
    "strand",
    "mode_site_position",
    "cluster_start",
    "cluster_end",
    "sequence",
    "pas_motif",
    "pas_position",
    "pas_type",
    "search_level",
    "n_samples",
    "n_transcripts",
    "total_site_count",
    "supported_observations",
    "max_observation_count",
    "max_cluster_relative_abundance",
    "apa_level",
    "apa_level_reason",
]


def _to_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _support_tier(info: dict) -> str:
    if (
        info["n_samples"] >= 2
        and info["supported_observations"] >= 3
        and info["total_site_count"] >= 30
    ):
        return "strong"
    if info["supported_observations"] >= 2 and info["total_site_count"] >= 10:
        return "moderate"
    if (
        info["supported_observations"] < 2
        and info["max_observation_count"] >= 20
        and info["max_cluster_relative_abundance"] >= 0.25
    ):
        return "single_rescue"
    return "weak"


def assign_apa_level(pas_type: str, info: dict) -> Tuple[str, str]:
    pas_type = pas_type or "none"
    support = _support_tier(info)

    if pas_type == "canonical" and support == "strong":
        return "APA-L1", "canonical_pas_with_strong_support"
    if (pas_type == "canonical" and support == "moderate") or (
        pas_type == "variant" and support == "strong"
    ):
        return "APA-L2", f"{pas_type}_pas_with_{support}_support"
    if (
        (pas_type == "variant" and support == "moderate")
        or (pas_type in {"upstream", "downstream"} and support == "strong")
        or (pas_type == "none" and support == "strong")
    ):
        return "APA-L3", f"{pas_type}_pas_with_{support}_support"
    if pas_type in {"upstream", "downstream", "none"} and support == "moderate":
        return "APA-L4", f"{pas_type}_pas_with_moderate_support"
    if support == "single_rescue":
        return "APA-L5", "single_observation_rescue_support"
    return "APA-L5", f"{pas_type}_pas_with_weak_support"


def load_existing_results(output_path: str) -> set:
    done: set = set()
    if not os.path.exists(output_path):
        return done
    with open(output_path) as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if reader.fieldnames and "cluster_key" not in reader.fieldnames:
            raise ValueError(
                f"Existing output lacks cluster_key and cannot be resumed safely: "
                f"{output_path}. Use a new output path or remove the old file."
            )
        if reader.fieldnames:
            missing = set(OUTPUT_COLUMNS) - set(reader.fieldnames)
            if missing:
                raise ValueError(
                    f"Existing output lacks new columns and cannot be resumed safely: "
                    f"{', '.join(sorted(missing))}. Use a new output path or remove "
                    f"the old file: {output_path}"
                )
        for row in reader:
            cluster_key = row.get("cluster_key", "").strip()
            if cluster_key:
                done.add(cluster_key)
    log.info(f"Resume: {len(done):,} clusters already in output — will skip")
    return done


def aggregate_clusters(unified_path: str) -> Dict[str, dict]:
    log.info(f"Reading unified file: {unified_path}")
    clusters: Dict[str, dict] = {}
    observation_counts: Dict[str, defaultdict] = {}
    observation_abundances: Dict[str, defaultdict] = {}
    row_count = 0
    with open(unified_path) as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if reader.fieldnames and "cluster_key" not in reader.fieldnames:
            raise ValueError(
                f"Unified file lacks required cluster_key column: {unified_path}"
            )
        for row in reader:
            row_count += 1
            cluster_key = row["cluster_key"].strip()
            if not cluster_key:
                raise ValueError(
                    f"Empty cluster_key at unified-file data row {row_count}"
                )
            orig_pos = int(row["original_site_position"])
            mode_pos = int(row["mode_site_position"])
            transcript_id = row.get("transcript_id", "")
            sample = row.get("sample", "")
            observation_key = (transcript_id, sample)
            site_count = _to_float(row.get("site_count"))
            cluster_relative_abundance = _to_float(
                row.get("cluster_relative_abundance")
            )
            if cluster_key not in clusters:
                clusters[cluster_key] = {
                    "cluster_key": cluster_key,
                    "unified_ID": row.get("unified_ID", ""),
                    "chromosome": row["chromosome"],
                    "strand": row["strand"],
                    "mode_site_position": mode_pos,
                    "cluster_start": orig_pos,
                    "cluster_end": orig_pos,
                    "samples": set(),
                    "transcripts": set(),
                    "total_site_count": 0.0,
                }
                observation_counts[cluster_key] = defaultdict(float)
                observation_abundances[cluster_key] = defaultdict(float)
            else:
                c = clusters[cluster_key]
                c["cluster_start"] = min(c["cluster_start"], orig_pos)
                c["cluster_end"] = max(c["cluster_end"], orig_pos)
            c = clusters[cluster_key]
            if sample:
                c["samples"].add(sample)
            if transcript_id:
                c["transcripts"].add(transcript_id)
            c["total_site_count"] += site_count
            observation_counts[cluster_key][observation_key] += site_count
            observation_abundances[cluster_key][observation_key] = max(
                observation_abundances[cluster_key][observation_key],
                cluster_relative_abundance,
            )

    for cluster_key, c in clusters.items():
        counts = observation_counts[cluster_key]
        abundances = observation_abundances[cluster_key]
        c["n_samples"] = len(c.pop("samples"))
        c["n_transcripts"] = len(c.pop("transcripts"))
        c["supported_observations"] = sum(1 for count in counts.values() if count >= 5)
        c["max_observation_count"] = max(counts.values(), default=0.0)
        c["max_cluster_relative_abundance"] = max(abundances.values(), default=0.0)

    log.info(f"  Rows: {row_count:,} | Unique clusters: {len(clusters):,}")
    return clusters


def annotate_clusters(
    clusters: Dict[str, dict],
    fasta_path: str,
    output_path: str,
    already_done: set,
    progress_every: int = 1000,
) -> None:
    _build_fasta_index(fasta_path)

    to_annotate = [
        (cluster_key, info)
        for cluster_key, info in clusters.items()
        if cluster_key not in already_done
    ]
    total = len(to_annotate)
    log.info(f"Clusters to annotate: {total:,}")
    if total == 0:
        log.info("Nothing to do.")
        return

    write_header = not os.path.exists(output_path) or os.path.getsize(output_path) == 0
    out_fh = open(output_path, "a", newline="")
    writer = csv.DictWriter(
        out_fh, fieldnames=OUTPUT_COLUMNS, delimiter="\t", lineterminator="\n"
    )
    if write_header:
        writer.writeheader()

    try:
        for i, (cluster_key, info) in enumerate(to_annotate, 1):
            chrom = info["chromosome"]
            strand = info["strand"]
            mode_pos = info["mode_site_position"]

            pas = annotate_site_from_fasta(fasta_path, chrom, mode_pos, strand)
            seq = _fetch_sequence(fasta_path, chrom, mode_pos, strand)
            pas_type = pas["motif_type"] or "none"
            apa_level, apa_level_reason = assign_apa_level(pas_type, info)

            writer.writerow(
                {
                    "cluster_key": cluster_key,
                    "unified_ID": info["unified_ID"],
                    "chromosome": chrom,
                    "strand": strand,
                    "mode_site_position": mode_pos,
                    "cluster_start": info["cluster_start"],
                    "cluster_end": info["cluster_end"],
                    "sequence": seq,
                    "pas_motif": pas["motif"] or "",
                    "pas_position": pas["position"]
                    if pas["position"] is not None
                    else "",
                    "pas_type": pas["motif_type"] or "",
                    "search_level": pas["search_level"],
                    "n_samples": info["n_samples"],
                    "n_transcripts": info["n_transcripts"],
                    "total_site_count": _format_number(info["total_site_count"]),
                    "supported_observations": info["supported_observations"],
                    "max_observation_count": _format_number(
                        info["max_observation_count"]
                    ),
                    "max_cluster_relative_abundance": _format_number(
                        info["max_cluster_relative_abundance"]
                    ),
                    "apa_level": apa_level,
                    "apa_level_reason": apa_level_reason,
                }
            )

            if i % progress_every == 0 or i == total:
                log.info(f"  {i:,} / {total:,}  ({100 * i / total:.1f}%)")
    finally:
        out_fh.flush()
        out_fh.close()

    log.info(f"Annotation complete. Output: {output_path}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Annotate APA clusters with PAS signals and ±50 bp sequence context.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--unified-file",
        required=True,
        metavar="PATH",
        help="Path to *_unified_apa_sites.txt (TSV with header)",
    )
    parser.add_argument(
        "--fasta",
        required=True,
        metavar="PATH",
        help="Path to reference genome FASTA (.fna / .fa / .fasta)",
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="PATH",
        help="Output TSV path (e.g. Homo_sapiens_apa_annotation.tsv)",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=1000,
        metavar="N",
        help="Log progress every N clusters (default: 1000)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if not os.path.exists(args.unified_file):
        log.error(f"Unified file not found: {args.unified_file}")
        sys.exit(1)
    if not os.path.exists(args.fasta):
        log.error(f"FASTA file not found: {args.fasta}")
        sys.exit(1)

    already_done = load_existing_results(args.output)
    clusters = aggregate_clusters(args.unified_file)
    annotate_clusters(
        clusters=clusters,
        fasta_path=args.fasta,
        output_path=args.output,
        already_done=already_done,
        progress_every=args.progress_every,
    )


if __name__ == "__main__":
    main()
