#!/usr/bin/env python3
"""
unify_apa_sites_dp_segment.py - APA unification with dynamic-programming clustering.

This script keeps the same input cleaning, transcript-sample observation filtering,
relative-abundance recalculation, and summary tables as
unify_apa_sites_biological.py, but replaces the greedy mode-seeded cluster builder
with a global one-dimensional dynamic-programming segmenter for each
chromosome/gene/strand group.

The DP model partitions sorted observed cleavage positions into valid segments.
Each segment must satisfy:
  - cluster span <= --max-cluster-width
  - adjacent observed-position gaps <= --max-internal-gap

The objective minimizes:
  sum(weighted coordinate dispersion per segment) + N_segments * penalty

So compact nearby positions are merged, while separated high-support modes split
when the dispersion cost is larger than the cost of an extra cluster.
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from unify_apa_sites_biological import (
    DEFAULT_BIOTYPES,
    GENE_KEY,
    assign_clusters,
    discover_apa_files,
    read_and_filter,
    recalculate_cluster_relative_abundance,
    sort_detailed,
    summarize_clusters,
    warn_duplicate_coordinate_ids,
    _choose_mode,
    _normalize_weights,
    _parse_biotypes,
    _position_evidence,
)


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def _position_dp_weights(
    positions: Sequence[int],
    sample_sets: Dict[int, set],
    total_counts: Dict[int, float],
    sample_weight: float,
    count_weight: float,
) -> Dict[int, float]:
    """Build evidence weights for coordinate dispersion.

    Counts are log-scaled so one very deep sample does not dominate the
    coordinate fit as strongly as raw read counts would.
    """
    max_samples = max((len(sample_sets[pos]) for pos in positions), default=1) or 1
    max_log_count = (
        max((math.log1p(total_counts[pos]) for pos in positions), default=1.0) or 1.0
    )

    weights: Dict[int, float] = {}
    for pos in positions:
        sample_score = len(sample_sets[pos]) / max_samples
        count_score = math.log1p(total_counts[pos]) / max_log_count
        weight = sample_weight * sample_score + count_weight * count_score
        weights[pos] = max(weight, 1e-6)
    return weights


def _segment_dispersion_cost(
    segment_positions: Sequence[int],
    dp_weights: Dict[int, float],
    compactness_weight: float,
) -> float:
    if len(segment_positions) <= 1 or compactness_weight <= 0:
        return 0.0

    values = np.array(segment_positions, dtype=float)
    weights = np.array([dp_weights[pos] for pos in segment_positions], dtype=float)
    center = float(np.average(values, weights=weights))
    variance = float(np.average((values - center) ** 2, weights=weights))
    return compactness_weight * variance


def _observation_counts_for_positions(
    group: pd.DataFrame,
    positions: Sequence[int],
) -> pd.Series:
    sub = group[group["site_position"].isin(positions)]
    if sub.empty:
        return pd.Series(dtype=float)
    return (
        sub.groupby(["transcript_id", "sample"], dropna=False)["site_count"]
        .sum()
        .sort_values(ascending=False)
    )


def _cluster_support_stats(
    group: pd.DataFrame,
    positions: Sequence[int],
    transcript_sample_totals: pd.Series,
    min_observation_count: int,
    strong_single_observation_count: int,
    strong_single_min_relative_abundance: float,
) -> dict:
    observation_counts = _observation_counts_for_positions(group, positions)
    if observation_counts.empty:
        return {
            "supported_observations": 0,
            "max_observation_count": 0.0,
            "total_count": 0.0,
            "is_strong": False,
            "is_weak_singleton": len(positions) == 1,
        }

    max_observation = float(observation_counts.iloc[0])
    total_count = float(observation_counts.sum())
    supported = int((observation_counts >= min_observation_count).sum())
    observation_relative = (
        observation_counts
        / transcript_sample_totals.reindex(observation_counts.index).replace(0, np.nan)
    ).fillna(0.0)
    count_eligible_relative = observation_relative[
        observation_counts >= strong_single_observation_count
    ]
    strong_single = (
        strong_single_observation_count > 0
        and max_observation >= strong_single_observation_count
        and not count_eligible_relative.empty
        and float(count_eligible_relative.max()) >= strong_single_min_relative_abundance
    )

    return {
        "supported_observations": supported,
        "max_observation_count": max_observation,
        "total_count": total_count,
        "is_strong": supported >= 2 or strong_single,
        "is_weak_singleton": (
            len(positions) == 1
            and supported < 1
            and max_observation < min_observation_count
        ),
    }


def _valid_positions(
    positions: Sequence[int],
    max_cluster_width: int,
    max_internal_gap: int,
) -> bool:
    if not positions:
        return False
    if positions[-1] - positions[0] + 1 > max_cluster_width:
        return False
    if len(positions) == 1:
        return True
    return all(
        right - left <= max_internal_gap
        for left, right in zip(positions, positions[1:])
    )


def _valid_segment(
    positions: Sequence[int],
    start_idx: int,
    end_idx: int,
    max_cluster_width: int,
    max_internal_gap: int,
) -> bool:
    if positions[end_idx] - positions[start_idx] + 1 > max_cluster_width:
        return False
    if end_idx == start_idx:
        return True
    return all(
        right - left <= max_internal_gap
        for left, right in zip(positions[start_idx:end_idx], positions[start_idx + 1 : end_idx + 1])
    )


def _dp_partition_positions(
    positions: Sequence[int],
    dp_weights: Dict[int, float],
    max_cluster_width: int,
    max_internal_gap: int,
    cluster_penalty: float,
    compactness_weight: float,
) -> List[List[int]]:
    """Globally partition one gene's sorted positions into compact clusters."""
    n_positions = len(positions)
    if n_positions == 0:
        return []

    dp_cost = [math.inf] * (n_positions + 1)
    dp_clusters = [10**12] * (n_positions + 1)
    previous = [-1] * (n_positions + 1)
    dp_cost[0] = 0.0
    dp_clusters[0] = 0

    for start_idx in range(n_positions):
        if not math.isfinite(dp_cost[start_idx]):
            continue

        for end_idx in range(start_idx, n_positions):
            if positions[end_idx] - positions[start_idx] + 1 > max_cluster_width:
                break
            if (
                end_idx > start_idx
                and positions[end_idx] - positions[end_idx - 1] > max_internal_gap
            ):
                break
            if not _valid_segment(
                positions,
                start_idx,
                end_idx,
                max_cluster_width,
                max_internal_gap,
            ):
                continue

            segment_positions = positions[start_idx : end_idx + 1]
            segment_cost = _segment_dispersion_cost(
                segment_positions,
                dp_weights,
                compactness_weight,
            )
            candidate_cost = dp_cost[start_idx] + cluster_penalty + segment_cost
            candidate_clusters = dp_clusters[start_idx] + 1
            target = end_idx + 1

            if (
                candidate_cost < dp_cost[target] - 1e-9
                or (
                    abs(candidate_cost - dp_cost[target]) <= 1e-9
                    and candidate_clusters < dp_clusters[target]
                )
            ):
                dp_cost[target] = candidate_cost
                dp_clusters[target] = candidate_clusters
                previous[target] = start_idx

    clusters: List[List[int]] = []
    cursor = n_positions
    while cursor > 0:
        start_idx = previous[cursor]
        if start_idx < 0:
            # Singletons are always valid, so this is defensive only.
            start_idx = cursor - 1
        clusters.append(list(positions[start_idx:cursor]))
        cursor = start_idx

    clusters.reverse()
    return clusters


def _absorb_weak_singletons(
    clusters: List[List[int]],
    group: pd.DataFrame,
    max_cluster_width: int,
    max_internal_gap: int,
    min_observation_count: int,
    strong_single_observation_count: int,
    strong_single_min_relative_abundance: float,
    enabled: bool,
) -> List[List[int]]:
    if not enabled or len(clusters) < 2:
        return clusters

    transcript_sample_totals = group.groupby(
        ["transcript_id", "sample"], dropna=False
    )["site_count"].sum()
    merged = [list(cluster) for cluster in clusters]
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(merged):
            cluster = merged[i]
            stats = _cluster_support_stats(
                group,
                cluster,
                transcript_sample_totals,
                min_observation_count,
                strong_single_observation_count,
                strong_single_min_relative_abundance,
            )
            if not stats["is_weak_singleton"]:
                i += 1
                continue

            candidates = []
            for neighbor_idx in (i - 1, i + 1):
                if neighbor_idx < 0 or neighbor_idx >= len(merged):
                    continue
                neighbor = merged[neighbor_idx]
                neighbor_stats = _cluster_support_stats(
                    group,
                    neighbor,
                    transcript_sample_totals,
                    min_observation_count,
                    strong_single_observation_count,
                    strong_single_min_relative_abundance,
                )
                combined = sorted(cluster + neighbor)
                if not neighbor_stats["is_strong"]:
                    continue
                if not _valid_positions(combined, max_cluster_width, max_internal_gap):
                    continue
                distance = min(
                    abs(cluster[0] - neighbor[0]),
                    abs(cluster[0] - neighbor[-1]),
                )
                candidates.append(
                    (
                        distance,
                        -neighbor_stats["supported_observations"],
                        -neighbor_stats["max_observation_count"],
                        neighbor_idx,
                        combined,
                    )
                )

            if not candidates:
                i += 1
                continue

            _distance, _supported, _max_count, neighbor_idx, combined = min(candidates)
            keep_idx = min(i, neighbor_idx)
            drop_idx = max(i, neighbor_idx)
            merged[keep_idx] = combined
            del merged[drop_idx]
            changed = True
            i = max(0, keep_idx - 1)

    return merged


def _cluster_one_gene_dp(
    key: Tuple[str, str, str],
    group: pd.DataFrame,
    max_cluster_width: int,
    max_internal_gap: int,
    mode_support_window: int,
    sample_weight: float,
    count_weight: float,
    mode_sample_weight: float,
    mode_count_weight: float,
    dp_cluster_penalty: float,
    dp_compactness_weight: float,
    min_observation_count: int,
    strong_single_observation_count: int,
    strong_single_min_relative_abundance: float,
    absorb_weak_singletons: bool,
) -> List[dict]:
    chrom, gene_id, strand = key
    sample_sets, total_counts = _position_evidence(group)
    positions = sorted(sample_sets)
    dp_weights = _position_dp_weights(
        positions,
        sample_sets,
        total_counts,
        sample_weight,
        count_weight,
    )
    clusters = _dp_partition_positions(
        positions,
        dp_weights,
        max_cluster_width,
        max_internal_gap,
        dp_cluster_penalty,
        dp_compactness_weight,
    )
    clusters = _absorb_weak_singletons(
        clusters,
        group,
        max_cluster_width,
        max_internal_gap,
        min_observation_count,
        strong_single_observation_count,
        strong_single_min_relative_abundance,
        absorb_weak_singletons,
    )

    cluster_rows: List[dict] = []
    for cluster_number, cluster_positions in enumerate(clusters):
        cluster_start = cluster_positions[0]
        cluster_end = cluster_positions[-1]
        cluster_width = cluster_end - cluster_start + 1
        mode = _choose_mode(
            cluster_positions,
            sample_sets,
            total_counts,
            mode_support_window,
            sample_weight,
            count_weight,
            mode_sample_weight,
            mode_count_weight,
        )

        cluster_key = f"{chrom}|{gene_id}|{strand}|{cluster_number}"
        unified_id = f"{chrom}:{cluster_start}-{cluster_end}:{strand}"

        for pos in cluster_positions:
            cluster_rows.append(
                {
                    "chromosome": chrom,
                    "gene_id": gene_id,
                    "strand": strand,
                    "site_position": pos,
                    "cluster_key": cluster_key,
                    "unified_ID": unified_id,
                    "cluster_start": cluster_start,
                    "cluster_end": cluster_end,
                    "cluster_width": cluster_width,
                    "n_unique_positions": len(cluster_positions),
                    **mode,
                }
            )

    return cluster_rows


def build_clusters_dp(
    df: pd.DataFrame,
    max_cluster_width: int,
    max_internal_gap: int,
    mode_support_window: int,
    sample_weight: float,
    count_weight: float,
    mode_sample_weight: float,
    mode_count_weight: float,
    dp_cluster_penalty: float,
    dp_compactness_weight: float,
    min_observation_count: int,
    strong_single_observation_count: int,
    strong_single_min_relative_abundance: float,
    absorb_weak_singletons: bool,
) -> pd.DataFrame:
    """Build a position-to-cluster map with DP segmentation."""
    rows: List[dict] = []
    grouped = df.groupby(GENE_KEY, sort=True, dropna=False)
    total_groups = grouped.ngroups
    log.info("DP clustering %d chromosome/gene/strand groups", total_groups)

    for i, (key, group) in enumerate(grouped, 1):
        rows.extend(
            _cluster_one_gene_dp(
                key,
                group,
                max_cluster_width,
                max_internal_gap,
                mode_support_window,
                sample_weight,
                count_weight,
                mode_sample_weight,
                mode_count_weight,
                dp_cluster_penalty,
                dp_compactness_weight,
                min_observation_count,
                strong_single_observation_count,
                strong_single_min_relative_abundance,
                absorb_weak_singletons,
            )
        )
        if i % 1000 == 0 or i == total_groups:
            log.info("  DP clustered %d / %d gene groups", i, total_groups)

    cluster_map = pd.DataFrame(rows)
    log.info(
        "Built %d DP clusters from %d unique positions",
        cluster_map["cluster_key"].nunique(),
        len(cluster_map),
    )
    return cluster_map


def evaluate_cluster_filters_dp(
    detailed: pd.DataFrame,
    min_single_transcript_count: int,
    min_multi_transcript_count: int,
    min_supported_transcripts: int,
    min_observation_count: int,
    min_supported_observations: int,
    strong_single_observation_count: int,
    strong_single_min_relative_abundance: float,
    min_cluster_samples: int,
    filter_strategy: str,
    no_filter: bool,
) -> pd.DataFrame:
    if (
        filter_strategy == "observations"
        and strong_single_observation_count > 0
        and "prefilter_cluster_relative_abundance" not in detailed.columns
    ):
        raise ValueError(
            "strong single-observation rescue requires pre-filter "
            "prefilter_cluster_relative_abundance"
        )

    records: List[dict] = []
    for cluster_key, group in detailed.groupby("cluster_key", sort=False):
        n_samples = group["sample"].nunique()
        transcript_counts = (
            group.groupby("transcript_id")["site_count"].sum().sort_values(ascending=False)
        )
        n_transcripts = len(transcript_counts)

        passed = False
        pass_rule = ""
        reason = ""

        if no_filter:
            passed = True
            pass_rule = "no_filter"
        elif n_samples < min_cluster_samples:
            reason = f"n_samples_lt_{min_cluster_samples}"
        elif filter_strategy == "observations":
            observation_counts = (
                group.groupby(["transcript_id", "sample"], dropna=False)["site_count"]
                .sum()
                .sort_values(ascending=False)
            )
            supported_observations = observation_counts[
                observation_counts >= min_observation_count
            ]
            max_observation = (
                float(observation_counts.iloc[0]) if not observation_counts.empty else 0.0
            )
            observation_abundance = (
                group.groupby(["transcript_id", "sample"], dropna=False)[
                    "prefilter_cluster_relative_abundance"
                ]
                .max()
                .reindex(observation_counts.index)
                .fillna(0.0)
            )
            strong_observation_abundance = observation_abundance[
                observation_counts >= strong_single_observation_count
            ]
            max_strong_observation_abundance = (
                float(strong_observation_abundance.max())
                if not strong_observation_abundance.empty
                else 0.0
            )
            strong_single = (
                strong_single_observation_count > 0
                and max_observation >= strong_single_observation_count
                and max_strong_observation_abundance
                >= strong_single_min_relative_abundance
            )
            if len(supported_observations) >= min_supported_observations:
                passed = True
                pass_rule = "supported_transcript_sample_observations"
            elif strong_single:
                passed = True
                pass_rule = "strong_single_transcript_sample_observation_with_abundance"
            else:
                reason = (
                    f"fewer_than_{min_supported_observations}_transcript_sample"
                    f"_observations_with_count_ge_{min_observation_count}"
                )
                if strong_single_observation_count > 0:
                    reason += (
                        f"_and_max_observation_lt_{strong_single_observation_count}"
                        f"_or_relative_abundance_lt_"
                        f"{strong_single_min_relative_abundance:g}"
                    )
        else:
            if n_transcripts == 1:
                count = float(transcript_counts.iloc[0])
                if count >= min_single_transcript_count:
                    passed = True
                    pass_rule = "single_transcript_count"
                else:
                    reason = f"single_transcript_count_lt_{min_single_transcript_count}"
            else:
                supported = transcript_counts[
                    transcript_counts >= min_multi_transcript_count
                ]
                if len(supported) >= min_supported_transcripts:
                    passed = True
                    pass_rule = "multi_transcript_count"
                else:
                    reason = (
                        f"fewer_than_{min_supported_transcripts}_transcripts"
                        f"_with_count_ge_{min_multi_transcript_count}"
                    )

        records.append(
            {
                "cluster_key": cluster_key,
                "filter_passed": passed,
                "filter_pass_rule": pass_rule,
                "filter_reason": reason,
            }
        )

    return pd.DataFrame(records)


def _drop_internal_filter_columns(detailed: pd.DataFrame) -> pd.DataFrame:
    return detailed.drop(
        columns=["prefilter_cluster_relative_abundance"],
        errors="ignore",
    )


def _capitalize_first(value):
    if pd.isna(value):
        return value
    text = str(value)
    if not text:
        return text
    return text[0].upper() + text[1:]


def _capitalize_tissue_sample_names(detailed: pd.DataFrame) -> pd.DataFrame:
    if detailed.empty or "sample" not in detailed or "sample_attribute" not in detailed:
        return detailed

    detailed = detailed.copy()
    tissue_mask = detailed["sample_attribute"].eq("tissue") & detailed["sample"].notna()
    detailed.loc[tissue_mask, "sample"] = detailed.loc[tissue_mask, "sample"].map(
        _capitalize_first
    )
    return detailed


def _renumber_retained_cluster_keys(
    detailed: pd.DataFrame,
    filter_info: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if detailed.empty:
        return detailed, filter_info.copy()

    cluster_order = (
        detailed[
            [
                "cluster_key",
                "chromosome",
                "gene_id",
                "strand",
                "cluster_start",
                "cluster_end",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            [
                "chromosome",
                "gene_id",
                "strand",
                "cluster_start",
                "cluster_end",
                "cluster_key",
            ],
            kind="mergesort",
        )
    )

    mapping: Dict[str, str] = {}
    grouped = cluster_order.groupby(
        ["chromosome", "gene_id", "strand"], sort=False, dropna=False
    )
    for (chrom, gene_id, strand), group in grouped:
        for rank, row in enumerate(group.itertuples(index=False), 1):
            mapping[str(row.cluster_key)] = f"{chrom}|{gene_id}|{strand}|{rank}"

    detailed = detailed.copy()
    detailed["cluster_key"] = detailed["cluster_key"].map(
        lambda key: mapping.get(str(key), key)
    )

    output_filter_info = filter_info[
        filter_info["cluster_key"].astype(str).isin(mapping)
    ].copy()
    output_filter_info["cluster_key"] = output_filter_info["cluster_key"].map(
        lambda key: mapping.get(str(key), key)
    )
    return detailed, output_filter_info


def parse_args(argv: Optional[Sequence[str]] = None):
    parser = argparse.ArgumentParser(
        description="Unify single-sample APA calls with DP-segment clustering.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Example:
    python unify_apa_sites_dp_segment.py /path/to/Homo_sapiens
    python unify_apa_sites_dp_segment.py /path/to/Homo_sapiens \\
        --dp-cluster-penalty 225 --max-cluster-width 40
        """,
    )
    parser.add_argument(
        "base_dir",
        type=Path,
        help="Species-level directory containing cell_culture/ and/or tissue/ subdirs",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for output TSV files (default: base_dir)",
    )
    parser.add_argument(
        "--output-prefix",
        default=None,
        help=(
            "Output prefix before _sites.txt/_summary.txt. Default: "
            "{species}_dp_segment_unified_apa"
        ),
    )
    parser.add_argument(
        "--max-cluster-width",
        type=int,
        default=40,
        help="Maximum inclusive span of one APA cluster in nt (default: 40)",
    )
    parser.add_argument(
        "--max-internal-gap",
        type=int,
        default=24,
        help="Maximum allowed gap between adjacent observed positions inside one cluster (default: 24)",
    )
    parser.add_argument(
        "--mode-support-window",
        type=int,
        default=15,
        help="Window around candidate mode for local support scoring (default: 15)",
    )
    parser.add_argument(
        "--sample-weight",
        type=float,
        default=0.7,
        help="Evidence weight for unique sample support (default: 0.7)",
    )
    parser.add_argument(
        "--count-weight",
        type=float,
        default=0.3,
        help="Evidence weight for log read-count support (default: 0.3)",
    )
    parser.add_argument(
        "--mode-sample-weight",
        type=float,
        default=0.8,
        help="Final mode score weight for exact unique sample support (default: 0.8)",
    )
    parser.add_argument(
        "--mode-count-weight",
        type=float,
        default=0.2,
        help="Final mode score weight for exact read count support (default: 0.2)",
    )
    parser.add_argument(
        "--dp-cluster-penalty",
        type=float,
        default=225.0,
        help=(
            "Penalty for adding one DP cluster in bp^2 units. With equal support, "
            "225 splits two positions roughly when they are >30 nt apart (default: 225)"
        ),
    )
    parser.add_argument(
        "--dp-compactness-weight",
        type=float,
        default=1.0,
        help="Multiplier for weighted coordinate variance in the DP objective (default: 1.0)",
    )
    parser.add_argument(
        "--no-absorb-weak-singletons",
        action="store_true",
        help=(
            "Disable post-DP absorption of weak singleton positions into a strong "
            "neighboring cluster when width/gap constraints still pass"
        ),
    )
    parser.add_argument(
        "--biotypes",
        default=",".join(DEFAULT_BIOTYPES),
        help="Comma-separated transcript biotypes to keep (default: mRNA,lncRNA,lnc_RNA)",
    )
    parser.add_argument(
        "--exclude-predicted-transcripts",
        action="store_true",
        help="Exclude RefSeq predicted transcripts with IDs starting XM_ or XR_",
    )
    parser.add_argument(
        "--keep-scaffolds",
        action="store_true",
        help="Keep non-NC_ contigs/scaffolds instead of restricting to primary RefSeq accessions",
    )
    parser.add_argument(
        "--keep-mitochondrial",
        action="store_true",
        help="Keep mitochondrial RefSeq accessions",
    )
    parser.add_argument(
        "--filter-strategy",
        choices=("observations", "transcript-totals"),
        default="observations",
        help=(
            "Confidence filter strategy. 'observations' keeps clusters with enough "
            "transcript-sample observations; 'transcript-totals' uses older "
            "single/multi-transcript total-count rules (default: observations)"
        ),
    )
    parser.add_argument(
        "--min-observation-count",
        type=int,
        default=5,
        help=(
            "For --filter-strategy observations, required reads in one "
            "transcript/sample observation (default: 5)"
        ),
    )
    parser.add_argument(
        "--min-supported-observations",
        type=int,
        default=2,
        help=(
            "For --filter-strategy observations, minimum transcript/sample "
            "observations meeting --min-observation-count (default: 2)"
        ),
    )
    parser.add_argument(
        "--strong-single-observation-count",
        type=int,
        default=50,
        help=(
            "For --filter-strategy observations, also keep clusters with one "
            "transcript/sample observation at least this strong. Use 0 to disable "
            "(default: 50)"
        ),
    )
    parser.add_argument(
        "--strong-single-min-relative-abundance",
        type=float,
        default=0.25,
        help=(
            "For --filter-strategy observations, strong single-observation rescue "
            "also requires this pre-filter cluster relative abundance in the same "
            "transcript/sample. Ignored when --strong-single-observation-count is 0 "
            "(default: 0.25)"
        ),
    )
    parser.add_argument(
        "--min-single-transcript-count",
        type=int,
        default=10,
        help=(
            "For --filter-strategy transcript-totals, keep a single-transcript "
            "cluster only if that transcript has at least this many reads (default: 10)"
        ),
    )
    parser.add_argument(
        "--min-multi-transcript-count",
        type=int,
        default=5,
        help=(
            "For --filter-strategy transcript-totals, required reads per "
            "supported transcript in multi-transcript clusters (default: 5)"
        ),
    )
    parser.add_argument(
        "--min-supported-transcripts",
        type=int,
        default=2,
        help=(
            "For --filter-strategy transcript-totals, minimum transcripts "
            "meeting --min-multi-transcript-count (default: 2)"
        ),
    )
    parser.add_argument(
        "--min-cluster-samples",
        type=int,
        default=1,
        help="Minimum unique samples per cluster (default: 1)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Disable confidence filtering and keep all clusters",
    )
    parser.add_argument(
        "--write-unfiltered",
        action="store_true",
        help="Also write .unfiltered detailed and summary outputs",
    )
    return parser.parse_args(argv)


def _validate_args(args) -> None:
    if args.max_cluster_width < 1:
        log.error("--max-cluster-width must be >= 1")
        sys.exit(1)
    if args.max_internal_gap < 1:
        log.error("--max-internal-gap must be >= 1")
        sys.exit(1)
    if args.max_internal_gap > args.max_cluster_width - 1 and args.max_cluster_width > 1:
        log.warning(
            "--max-internal-gap (%d) is larger than useful for --max-cluster-width (%d)",
            args.max_internal_gap,
            args.max_cluster_width,
        )
    if args.mode_support_window < 0:
        log.error("--mode-support-window must be >= 0")
        sys.exit(1)
    if args.dp_cluster_penalty < 0:
        log.error("--dp-cluster-penalty must be >= 0")
        sys.exit(1)
    if args.dp_compactness_weight < 0:
        log.error("--dp-compactness-weight must be >= 0")
        sys.exit(1)
    if args.min_observation_count < 1:
        log.error("--min-observation-count must be >= 1")
        sys.exit(1)
    if args.min_supported_observations < 1:
        log.error("--min-supported-observations must be >= 1")
        sys.exit(1)
    if args.strong_single_observation_count < 0:
        log.error("--strong-single-observation-count must be >= 0")
        sys.exit(1)
    if not 0 <= args.strong_single_min_relative_abundance <= 1:
        log.error("--strong-single-min-relative-abundance must be between 0 and 1")
        sys.exit(1)
    if args.min_cluster_samples < 1:
        log.error("--min-cluster-samples must be >= 1")
        sys.exit(1)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    _validate_args(args)

    base_dir = args.base_dir.resolve()
    if not base_dir.is_dir():
        log.error("Base directory does not exist: %s", base_dir)
        sys.exit(1)

    species_name = base_dir.name
    output_dir = args.output_dir.resolve() if args.output_dir else base_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_prefix = args.output_prefix or f"{species_name}_dp_segment_unified_apa"

    sample_weight, count_weight = _normalize_weights(
        args.sample_weight, args.count_weight
    )
    mode_sample_weight, mode_count_weight = _normalize_weights(
        args.mode_sample_weight, args.mode_count_weight
    )
    biotypes = _parse_biotypes(args.biotypes)

    file_infos = discover_apa_files(base_dir)
    df = read_and_filter(
        file_infos=file_infos,
        biotypes=biotypes,
        keep_scaffolds=args.keep_scaffolds,
        keep_mitochondrial=args.keep_mitochondrial,
        exclude_predicted_transcripts=args.exclude_predicted_transcripts,
    )

    cluster_map = build_clusters_dp(
        df=df,
        max_cluster_width=args.max_cluster_width,
        max_internal_gap=args.max_internal_gap,
        mode_support_window=args.mode_support_window,
        sample_weight=sample_weight,
        count_weight=count_weight,
        mode_sample_weight=mode_sample_weight,
        mode_count_weight=mode_count_weight,
        dp_cluster_penalty=args.dp_cluster_penalty,
        dp_compactness_weight=args.dp_compactness_weight,
        min_observation_count=args.min_observation_count,
        strong_single_observation_count=args.strong_single_observation_count,
        strong_single_min_relative_abundance=args.strong_single_min_relative_abundance,
        absorb_weak_singletons=not args.no_absorb_weak_singletons,
    )
    detailed_all = assign_clusters(df, cluster_map)
    detailed_all = recalculate_cluster_relative_abundance(detailed_all)
    detailed_all = detailed_all.rename(
        columns={"cluster_relative_abundance": "prefilter_cluster_relative_abundance"}
    )

    filter_info = evaluate_cluster_filters_dp(
        detailed=detailed_all,
        min_single_transcript_count=args.min_single_transcript_count,
        min_multi_transcript_count=args.min_multi_transcript_count,
        min_supported_transcripts=args.min_supported_transcripts,
        min_observation_count=args.min_observation_count,
        min_supported_observations=args.min_supported_observations,
        strong_single_observation_count=args.strong_single_observation_count,
        strong_single_min_relative_abundance=args.strong_single_min_relative_abundance,
        min_cluster_samples=args.min_cluster_samples,
        filter_strategy=args.filter_strategy,
        no_filter=args.no_filter,
    )
    pass_keys = set(filter_info.loc[filter_info["filter_passed"], "cluster_key"])
    fail_keys = set(filter_info.loc[~filter_info["filter_passed"], "cluster_key"])

    detailed = detailed_all[detailed_all["cluster_key"].isin(pass_keys)].copy()
    detailed, output_filter_info = _renumber_retained_cluster_keys(detailed, filter_info)
    detailed = recalculate_cluster_relative_abundance(detailed)
    detailed = _drop_internal_filter_columns(detailed)
    detailed = _capitalize_tissue_sample_names(detailed)
    detailed = sort_detailed(detailed)
    dropped = detailed_all[detailed_all["cluster_key"].isin(fail_keys)].copy()

    summary = summarize_clusters(detailed, output_filter_info)
    filtered_out = summarize_clusters(dropped, filter_info)
    warn_duplicate_coordinate_ids(summary)

    out_detailed = output_dir / f"{output_prefix}_sites.txt"
    out_summary = output_dir / f"{output_prefix}_summary.txt"
    out_filtered = output_dir / f"{output_prefix}_filtered_out.txt"

    detailed.to_csv(out_detailed, sep="\t", index=False)
    summary.to_csv(out_summary, sep="\t", index=False)
    filtered_out.to_csv(out_filtered, sep="\t", index=False)

    log.info("Wrote filtered detailed output: %s (%d rows)", out_detailed, len(detailed))
    log.info("Wrote filtered summary output: %s (%d clusters)", out_summary, len(summary))
    log.info(
        "Wrote filtered-out cluster audit: %s (%d clusters)",
        out_filtered,
        len(filtered_out),
    )

    if args.write_unfiltered:
        unfiltered_detailed = recalculate_cluster_relative_abundance(detailed_all.copy())
        unfiltered_detailed = _drop_internal_filter_columns(unfiltered_detailed)
        unfiltered_detailed = _capitalize_tissue_sample_names(unfiltered_detailed)
        unfiltered_detailed = sort_detailed(unfiltered_detailed)
        unfiltered_summary = summarize_clusters(unfiltered_detailed, filter_info)
        out_unfiltered_detailed = output_dir / f"{output_prefix}_sites.unfiltered.txt"
        out_unfiltered_summary = output_dir / f"{output_prefix}_summary.unfiltered.txt"
        unfiltered_detailed.to_csv(out_unfiltered_detailed, sep="\t", index=False)
        unfiltered_summary.to_csv(out_unfiltered_summary, sep="\t", index=False)
        log.info(
            "Wrote unfiltered detailed output: %s (%d rows)",
            out_unfiltered_detailed,
            len(unfiltered_detailed),
        )
        log.info(
            "Wrote unfiltered summary output: %s (%d clusters)",
            out_unfiltered_summary,
            len(unfiltered_summary),
        )

    log.info(
        "Done. Retained %d / %d clusters.",
        len(summary),
        filter_info["cluster_key"].nunique(),
    )


if __name__ == "__main__":
    main()
