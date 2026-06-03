#!/usr/bin/env python3
"""
unify_apa_sites_batch_species.py - batch APA site unification for mixed species.

This is a new implementation that leaves unify_apa_sites.py unchanged.

It unifies single-sample APA calls at the gene level:
    chromosome + effective_gene_id + strand

It keeps the biological clustering model from unify_apa_sites_biological.py:
  - hard maximum cluster span, default 40 nt
  - hard maximum internal gap, default 24 nt
  - mode-seeded splitting instead of adjacent-gap chaining
  - representative mode chosen from the strongest observed cleavage position
  - local support window, default +/-15 nt, for shifted Nanopore calls
  - coordinate-only public unified_ID:
        chromosome:cluster_start-cluster_end:strand
  - internal cluster_key keeps effective_gene_id to prevent accidental merging
  - cluster-level transcript-aware filtering

This batch variant is intentionally more permissive for non-human/non-mouse
annotations: it keeps scaffolds by default, accepts protein_coding and blank
biotype rows, and uses gene_name when gene_id is blank.
"""

from __future__ import annotations

import argparse
import bisect
import logging
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_BIOTYPES = ("mRNA", "lncRNA", "lnc_RNA", "protein_coding", "")
EXPECTED_COLUMNS = {
    "transcript_id",
    "gene_id",
    "gene_name",
    "chromosome",
    "strand",
    "site_position",
    "site_count",
    "site_abundance",
    "transcript_biotype",
}

# Human and mouse RefSeq mitochondrial accessions. Other species can be kept by
# passing --keep-mitochondrial if their accession is not listed here.
MITOCHONDRIAL_REFSEQ_ACCESSIONS = {
    "NC_012920.1",  # Homo sapiens
    "NC_005089.1",  # Mus musculus
}

GENE_KEY = ["chromosome", "effective_gene_id", "strand"]
JOIN_KEY = GENE_KEY + ["site_position"]


# ---------------------------------------------------------------------------
# File discovery and input filtering
# ---------------------------------------------------------------------------


def discover_apa_files(base_dir: Path) -> List[dict]:
    """Find input *apa_sites.txt files anywhere under one species directory."""
    files = sorted(base_dir.rglob("*apa_sites.txt"))
    if not files:
        log.error("No *apa_sites.txt files found under %s", base_dir)
        sys.exit(1)

    discovered: List[dict] = []
    for fpath in files:
        parts = fpath.relative_to(base_dir).parts
        sample_attr = parts[0] if len(parts) >= 2 else "sample"

        discovered.append(
            {
                "path": fpath,
                "sample_attribute": sample_attr,
                "sample": fpath.parent.name,
            }
        )

    log.info("Discovered %d APA site files under %s", len(discovered), base_dir)
    return discovered


def _parse_biotypes(value: str) -> set:
    biotypes = {item.strip() for item in value.split(",")}
    return {"lncRNA" if item == "lnc_RNA" else item for item in biotypes}


def read_and_filter(
    file_infos: List[dict],
    biotypes: set,
    keep_scaffolds: bool,
    keep_mitochondrial: bool,
    exclude_predicted_transcripts: bool,
) -> pd.DataFrame:
    """Read all APA files, concatenate, and apply batch-safe input filters."""
    frames: List[pd.DataFrame] = []
    for info in file_infos:
        fpath = info["path"]
        try:
            df = pd.read_csv(
                fpath,
                sep="\t",
                dtype={
                    "transcript_id": str,
                    "gene_id": str,
                    "gene_name": str,
                    "chromosome": str,
                    "strand": str,
                    "transcript_biotype": str,
                },
            )
        except Exception as exc:
            log.warning("Failed to read %s: %s", fpath, exc)
            continue

        missing = EXPECTED_COLUMNS - set(df.columns)
        if missing:
            log.warning(
                "Skipping %s - missing columns: %s",
                fpath,
                ", ".join(sorted(missing)),
            )
            continue

        df["sample_attribute"] = info["sample_attribute"]
        df["sample"] = info["sample"]
        frames.append(df)

    if not frames:
        log.error("No valid APA site files could be loaded.")
        sys.exit(1)

    combined = pd.concat(frames, ignore_index=True)
    log.info("Total rows loaded: %d", len(combined))

    combined["site_position"] = pd.to_numeric(
        combined["site_position"], errors="coerce"
    )
    combined["site_count"] = pd.to_numeric(combined["site_count"], errors="coerce")
    combined["site_abundance"] = pd.to_numeric(
        combined["site_abundance"], errors="coerce"
    )

    before = len(combined)
    combined = combined.dropna(subset=["site_position", "site_count"]).copy()
    combined["site_position"] = combined["site_position"].astype(int)
    combined["site_count"] = combined["site_count"].astype(float)
    log.info("After numeric cleanup: %d rows (removed %d)", len(combined), before - len(combined))

    combined["transcript_biotype"] = combined["transcript_biotype"].replace(
        {"lnc_RNA": "lncRNA"}
    )
    combined["transcript_biotype"] = combined["transcript_biotype"].fillna("")
    combined["gene_id"] = combined["gene_id"].fillna("").astype(str).str.strip()
    combined["gene_name"] = combined["gene_name"].fillna("").astype(str).str.strip()
    combined["effective_gene_id"] = combined["gene_id"].where(
        combined["gene_id"] != "", combined["gene_name"]
    )
    before = len(combined)
    combined = combined[
        combined["effective_gene_id"].astype(str).str.strip() != ""
    ].copy()
    log.info(
        "After effective gene id cleanup: %d rows (removed %d)",
        len(combined),
        before - len(combined),
    )

    before = len(combined)
    combined = combined[combined["transcript_biotype"].isin(biotypes)].copy()
    log.info(
        "After biotype filter (%s): %d rows (removed %d)",
        ",".join(sorted(biotypes)),
        len(combined),
        before - len(combined),
    )

    if exclude_predicted_transcripts:
        before = len(combined)
        combined = combined[
            ~combined["transcript_id"].str.startswith(("XM_", "XR_"), na=False)
        ].copy()
        log.info(
            "After predicted transcript filter (XM_/XR_ removed): %d rows (removed %d)",
            len(combined),
            before - len(combined),
        )

    if not keep_scaffolds:
        before = len(combined)
        combined = combined[combined["chromosome"].str.startswith("NC_", na=False)].copy()
        log.info(
            "After primary RefSeq accession filter (kept NC_*): %d rows (removed %d)",
            len(combined),
            before - len(combined),
        )

    if not keep_mitochondrial:
        before = len(combined)
        combined = combined[
            ~combined["chromosome"].isin(MITOCHONDRIAL_REFSEQ_ACCESSIONS)
        ].copy()
        log.info(
            "After mitochondrial filter: %d rows (removed %d)",
            len(combined),
            before - len(combined),
        )

    if combined.empty:
        log.error("All APA rows were removed by filters.")
        sys.exit(1)

    sample_counts = combined.groupby("sample").size().sort_index()
    for sample_name, count in sample_counts.items():
        log.info("  Sample %-24s: %d records", sample_name, count)

    return combined


# ---------------------------------------------------------------------------
# Mode-seeded clustering
# ---------------------------------------------------------------------------


def _position_evidence(group: pd.DataFrame) -> Tuple[Dict[int, set], Dict[int, float]]:
    sample_sets: Dict[int, set] = {}
    total_counts: Dict[int, float] = {}
    for pos, sub in group.groupby("site_position", sort=True):
        pos_int = int(pos)
        sample_sets[pos_int] = set(sub["sample"].dropna().astype(str))
        total_counts[pos_int] = float(sub["site_count"].sum())
    return sample_sets, total_counts


def _interval_stats(
    positions: Sequence[int],
    sample_sets: Dict[int, set],
    total_counts: Dict[int, float],
) -> Tuple[int, float]:
    samples = set()
    total = 0.0
    for pos in positions:
        samples.update(sample_sets[pos])
        total += total_counts[pos]
    return len(samples), total


def _local_stats(
    pos: int,
    positions: Sequence[int],
    sample_sets: Dict[int, set],
    total_counts: Dict[int, float],
    window: int,
) -> Tuple[int, float]:
    left = bisect.bisect_left(positions, pos - window)
    right = bisect.bisect_right(positions, pos + window)
    return _interval_stats(positions[left:right], sample_sets, total_counts)


def _choose_seed(
    positions: Sequence[int],
    sample_sets: Dict[int, set],
    total_counts: Dict[int, float],
    mode_support_window: int,
    sample_weight: float,
    count_weight: float,
) -> Tuple[int, Dict[int, Tuple[float, int, float]]]:
    local: Dict[int, Tuple[int, float]] = {
        pos: _local_stats(pos, positions, sample_sets, total_counts, mode_support_window)
        for pos in positions
    }
    max_samples = max((value[0] for value in local.values()), default=1) or 1
    max_count = max((value[1] for value in local.values()), default=1.0) or 1.0

    scored: Dict[int, Tuple[float, int, float]] = {}
    for pos, (n_samples, total_count) in local.items():
        score = (
            sample_weight * n_samples / max_samples
            + count_weight * total_count / max_count
        )
        scored[pos] = (score, n_samples, total_count)

    seed = max(
        positions,
        key=lambda pos: (
            scored[pos][0],
            scored[pos][1],
            scored[pos][2],
            len(sample_sets[pos]),
            total_counts[pos],
            -pos,
        ),
    )
    return seed, scored


def _choose_best_interval(
    seed: int,
    positions: Sequence[int],
    sample_sets: Dict[int, set],
    total_counts: Dict[int, float],
    max_cluster_width: int,
    max_internal_gap: int,
) -> List[int]:
    seed_idx = bisect.bisect_left(positions, seed)
    best_positions: Optional[List[int]] = None
    best_key: Optional[Tuple[int, float, int, int, float, int]] = None

    for start_idx in range(seed_idx, -1, -1):
        start = positions[start_idx]
        if seed - start + 1 > max_cluster_width:
            break

        max_end = start + max_cluster_width - 1
        max_end_idx = bisect.bisect_right(positions, max_end) - 1
        if max_end_idx < seed_idx:
            continue

        left_side = list(positions[start_idx : seed_idx + 1])
        if len(left_side) > 1 and any(
            b - a > max_internal_gap for a, b in zip(left_side, left_side[1:])
        ):
            continue

        for end_idx in range(seed_idx, max_end_idx + 1):
            if (
                end_idx > seed_idx
                and positions[end_idx] - positions[end_idx - 1] > max_internal_gap
            ):
                break

            candidate = list(positions[start_idx : end_idx + 1])
            n_samples, total_count = _interval_stats(
                candidate, sample_sets, total_counts
            )
            width = candidate[-1] - candidate[0] + 1
            midpoint_dist = abs(((candidate[0] + candidate[-1]) / 2.0) - seed)
            key = (
                n_samples,
                total_count,
                len(candidate),
                -width,
                -midpoint_dist,
                -candidate[0],
            )
            if best_key is None or key > best_key:
                best_key = key
                best_positions = candidate

    if best_positions is None:
        return [seed]
    return best_positions


def _choose_mode(
    cluster_positions: Sequence[int],
    sample_sets: Dict[int, set],
    total_counts: Dict[int, float],
    mode_support_window: int,
    sample_weight: float,
    count_weight: float,
    mode_sample_weight: float,
    mode_count_weight: float,
) -> dict:
    local: Dict[int, Tuple[int, float]] = {
        pos: _local_stats(
            pos, cluster_positions, sample_sets, total_counts, mode_support_window
        )
        for pos in cluster_positions
    }
    max_samples = max((value[0] for value in local.values()), default=1) or 1
    max_count = max((value[1] for value in local.values()), default=1.0) or 1.0
    max_exact_samples = max((len(sample_sets[pos]) for pos in cluster_positions), default=1) or 1
    max_exact_count = max((total_counts[pos] for pos in cluster_positions), default=1.0) or 1.0

    local_scored: Dict[int, Tuple[float, int, float]] = {}
    for pos in cluster_positions:
        local_samples, local_count = local[pos]
        score = (
            sample_weight * local_samples / max_samples
            + count_weight * local_count / max_count
        )
        local_scored[pos] = (score, local_samples, local_count)

    cluster_weights = np.array([total_counts[pos] for pos in cluster_positions], dtype=float)
    if cluster_weights.sum() > 0:
        cluster_center = float(np.average(np.array(cluster_positions), weights=cluster_weights))
    else:
        cluster_center = (cluster_positions[0] + cluster_positions[-1]) / 2.0

    best = None
    best_key = None
    for pos in cluster_positions:
        local_score, local_samples, local_count = local_scored[pos]
        exact_samples = len(sample_sets[pos])
        exact_count = total_counts[pos]
        mode_score = (
            mode_sample_weight * exact_samples / max_exact_samples
            + mode_count_weight * exact_count / max_exact_count
        )
        key = (
            mode_score,
            exact_samples,
            exact_count,
            local_score,
            local_samples,
            local_count,
            -abs(pos - cluster_center),
            -pos,
        )
        if best_key is None or key > best_key:
            best_key = key
            best = {
                "mode_site_position": pos,
                "mode_score": round(mode_score, 4),
                "mode_local_n_samples": local_samples,
                "mode_local_total_site_count": local_count,
                "mode_exact_n_samples": exact_samples,
                "mode_exact_total_site_count": exact_count,
            }

    assert best is not None
    return best


def _cluster_one_gene(
    key: Tuple[str, str, str],
    group: pd.DataFrame,
    max_cluster_width: int,
    max_internal_gap: int,
    mode_support_window: int,
    sample_weight: float,
    count_weight: float,
    mode_sample_weight: float,
    mode_count_weight: float,
) -> List[dict]:
    chrom, effective_gene_id, strand = key
    sample_sets, total_counts = _position_evidence(group)
    remaining = sorted(sample_sets)
    cluster_rows: List[dict] = []
    cluster_number = 0

    while remaining:
        seed, _seed_scores = _choose_seed(
            remaining,
            sample_sets,
            total_counts,
            mode_support_window,
            sample_weight,
            count_weight,
        )
        cluster_positions = _choose_best_interval(
            seed,
            remaining,
            sample_sets,
            total_counts,
            max_cluster_width,
            max_internal_gap,
        )
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

        cluster_key = f"{chrom}|{effective_gene_id}|{strand}|{cluster_number}"
        unified_id = f"{chrom}:{cluster_start}-{cluster_end}:{strand}"

        for pos in cluster_positions:
            cluster_rows.append(
                {
                    "chromosome": chrom,
                    "effective_gene_id": effective_gene_id,
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

        assigned = set(cluster_positions)
        remaining = [pos for pos in remaining if pos not in assigned]
        cluster_number += 1

    return cluster_rows


def build_clusters(
    df: pd.DataFrame,
    max_cluster_width: int,
    max_internal_gap: int,
    mode_support_window: int,
    sample_weight: float,
    count_weight: float,
    mode_sample_weight: float,
    mode_count_weight: float,
) -> pd.DataFrame:
    """Build a position-to-cluster map using mode-seeded splitting."""
    rows: List[dict] = []
    grouped = df.groupby(GENE_KEY, sort=True, dropna=False)
    total_groups = grouped.ngroups
    log.info("Clustering %d chromosome/gene/strand groups", total_groups)

    for i, (key, group) in enumerate(grouped, 1):
        rows.extend(
            _cluster_one_gene(
                key,
                group,
                max_cluster_width,
                max_internal_gap,
                mode_support_window,
                sample_weight,
                count_weight,
                mode_sample_weight,
                mode_count_weight,
            )
        )
        if i % 1000 == 0 or i == total_groups:
            log.info("  Clustered %d / %d gene groups", i, total_groups)

    cluster_map = pd.DataFrame(rows)
    log.info(
        "Built %d clusters from %d unique positions",
        cluster_map["cluster_key"].nunique(),
        len(cluster_map),
    )
    return cluster_map


# ---------------------------------------------------------------------------
# Filtering and summaries
# ---------------------------------------------------------------------------


def assign_clusters(df: pd.DataFrame, cluster_map: pd.DataFrame) -> pd.DataFrame:
    detailed = df.merge(cluster_map, on=JOIN_KEY, how="inner")
    detailed = detailed.rename(columns={"site_position": "original_site_position"})

    columns = [
        "transcript_id",
        "gene_id",
        "gene_name",
        "effective_gene_id",
        "chromosome",
        "strand",
        "cluster_key",
        "unified_ID",
        "original_site_position",
        "cluster_start",
        "cluster_end",
        "cluster_width",
        "mode_site_position",
        "mode_score",
        "mode_local_n_samples",
        "mode_local_total_site_count",
        "mode_exact_n_samples",
        "mode_exact_total_site_count",
        "n_unique_positions",
        "site_count",
        "transcript_biotype",
        "sample_attribute",
        "sample",
    ]
    detailed = detailed[columns]
    return detailed


def recalculate_cluster_relative_abundance(detailed: pd.DataFrame) -> pd.DataFrame:
    """Recalculate APA relative abundance after cluster filtering.

    The denominator is the sum of retained cluster counts for the same
    transcript and sample. Exact-position rows inside one cluster share the same
    cluster-level abundance.
    """
    if detailed.empty:
        detailed["cluster_relative_abundance"] = pd.Series(dtype=float)
        return detailed

    keys = ["transcript_id", "sample", "cluster_key"]
    cluster_counts = (
        detailed.groupby(keys, dropna=False)["site_count"]
        .sum()
        .rename("cluster_count_for_abundance")
        .reset_index()
    )
    denominators = (
        cluster_counts.groupby(["transcript_id", "sample"], dropna=False)[
            "cluster_count_for_abundance"
        ]
        .sum()
        .rename("transcript_sample_total_count")
        .reset_index()
    )
    abundance = cluster_counts.merge(
        denominators,
        on=["transcript_id", "sample"],
        how="left",
    )
    abundance["cluster_relative_abundance"] = (
        abundance["cluster_count_for_abundance"]
        / abundance["transcript_sample_total_count"]
    )

    detailed = detailed.merge(
        abundance[
            keys
            + [
                "cluster_count_for_abundance",
                "transcript_sample_total_count",
                "cluster_relative_abundance",
            ]
        ],
        on=keys,
        how="left",
    )
    detailed["cluster_relative_abundance"] = (
        detailed["cluster_relative_abundance"].round(4)
    )
    detailed = detailed.drop(
        columns=["cluster_count_for_abundance", "transcript_sample_total_count"]
    )
    return detailed


def evaluate_cluster_filters(
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
    columns = ["cluster_key", "filter_passed", "filter_pass_rule", "filter_reason"]
    if detailed.empty:
        return pd.DataFrame(columns=columns)

    if (
        filter_strategy == "observations"
        and strong_single_observation_count > 0
        and "prefilter_cluster_relative_abundance" not in detailed.columns
    ):
        raise ValueError(
            "strong single-observation rescue requires pre-filter "
            "prefilter_cluster_relative_abundance"
        )

    cluster_keys = pd.Series(
        detailed["cluster_key"].drop_duplicates().to_numpy(), name="cluster_key"
    )
    if no_filter:
        return pd.DataFrame(
            {
                "cluster_key": cluster_keys,
                "filter_passed": True,
                "filter_pass_rule": "no_filter",
                "filter_reason": "",
            }
        )

    if filter_strategy == "observations":
        cluster_stats = (
            detailed.groupby("cluster_key", sort=False, dropna=False)["sample"]
            .nunique()
            .rename("n_samples")
            .reset_index()
        )
        observations = (
            detailed.groupby(
                ["cluster_key", "transcript_id", "sample"],
                sort=False,
                dropna=False,
            )
            .agg(
                observation_count=("site_count", "sum"),
                observation_relative_abundance=(
                    "prefilter_cluster_relative_abundance",
                    "max",
                ),
            )
            .reset_index()
        )
        supported_observations = (
            observations.loc[
                observations["observation_count"] >= min_observation_count
            ]
            .groupby("cluster_key", sort=False, dropna=False)
            .size()
            .rename("supported_observations")
            .reset_index()
        )
        max_observation = (
            observations.groupby("cluster_key", sort=False, dropna=False)[
                "observation_count"
            ]
            .max()
            .rename("max_observation")
            .reset_index()
        )

        stats = (
            pd.DataFrame({"cluster_key": cluster_keys})
            .merge(cluster_stats, on="cluster_key", how="left")
            .merge(supported_observations, on="cluster_key", how="left")
            .merge(max_observation, on="cluster_key", how="left")
        )
        stats["n_samples"] = stats["n_samples"].fillna(0).astype(int)
        stats["supported_observations"] = (
            stats["supported_observations"].fillna(0).astype(int)
        )
        stats["max_observation"] = stats["max_observation"].fillna(0.0)

        if strong_single_observation_count > 0:
            strong_abundance = (
                observations.loc[
                    observations["observation_count"]
                    >= strong_single_observation_count
                ]
                .groupby("cluster_key", sort=False, dropna=False)[
                    "observation_relative_abundance"
                ]
                .max()
                .rename("max_strong_observation_abundance")
                .reset_index()
            )
            stats = stats.merge(strong_abundance, on="cluster_key", how="left")
            stats["max_strong_observation_abundance"] = stats[
                "max_strong_observation_abundance"
            ].fillna(0.0)
            strong_single = (
                (stats["max_observation"] >= strong_single_observation_count)
                & (
                    stats["max_strong_observation_abundance"]
                    >= strong_single_min_relative_abundance
                )
            )
        else:
            strong_single = pd.Series(False, index=stats.index)

        enough_samples = stats["n_samples"] >= min_cluster_samples
        supported_pass = (
            stats["supported_observations"] >= min_supported_observations
        )
        passed = enough_samples & (supported_pass | strong_single)

        stats["filter_passed"] = passed
        stats["filter_pass_rule"] = ""
        stats.loc[
            enough_samples & supported_pass,
            "filter_pass_rule",
        ] = "supported_transcript_sample_observations"
        stats.loc[
            enough_samples & ~supported_pass & strong_single,
            "filter_pass_rule",
        ] = "strong_single_transcript_sample_observation_with_abundance"

        stats["filter_reason"] = ""
        stats.loc[
            ~enough_samples,
            "filter_reason",
        ] = f"n_samples_lt_{min_cluster_samples}"
        fail_reason = (
            f"fewer_than_{min_supported_observations}_transcript_sample"
            f"_observations_with_count_ge_{min_observation_count}"
        )
        if strong_single_observation_count > 0:
            fail_reason += (
                f"_and_max_observation_lt_{strong_single_observation_count}"
                f"_or_relative_abundance_lt_"
                f"{strong_single_min_relative_abundance:g}"
            )
        stats.loc[
            enough_samples & ~passed,
            "filter_reason",
        ] = fail_reason

        return stats[columns]

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

        if n_samples < min_cluster_samples:
            reason = f"n_samples_lt_{min_cluster_samples}"
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


def _format_number(value: float) -> str:
    if pd.isna(value):
        return ""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _weighted_mean_and_sd(values: np.ndarray, weights: np.ndarray) -> Tuple[float, float]:
    if len(values) == 0 or weights.sum() <= 0:
        return (math.nan, math.nan)
    mean = float(np.average(values, weights=weights))
    variance = float(np.average((values - mean) ** 2, weights=weights))
    return mean, math.sqrt(variance)


def _weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    if len(values) == 0 or weights.sum() <= 0:
        return math.nan
    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = weights[order]
    cumulative = np.cumsum(sorted_weights)
    cutoff = quantile * sorted_weights.sum()
    return float(sorted_values[np.searchsorted(cumulative, cutoff, side="left")])


def _transcript_counts_string(group: pd.DataFrame) -> str:
    counts = group.groupby("transcript_id")["site_count"].sum()
    items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ",".join(f"{tid}:{_format_number(count)}" for tid, count in items)


def summarize_clusters(
    detailed: pd.DataFrame,
    filter_info: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    filter_map = {}
    if filter_info is not None and not filter_info.empty:
        filter_map = filter_info.set_index("cluster_key").to_dict(orient="index")

    records: List[dict] = []
    for cluster_key, group in detailed.groupby("cluster_key", sort=False):
        first = group.iloc[0]
        transcript_ids = sorted(group["transcript_id"].dropna().unique())
        sample_list = sorted(group["sample"].dropna().unique())
        biotypes = sorted(group["transcript_biotype"].dropna().unique())
        positions = group["original_site_position"].to_numpy(dtype=float)
        weights = group["site_count"].to_numpy(dtype=float)
        weighted_mean, weighted_sd = _weighted_mean_and_sd(positions, weights)
        q25 = _weighted_quantile(positions, weights, 0.25)
        q75 = _weighted_quantile(positions, weights, 0.75)
        filter_row = filter_map.get(cluster_key, {})

        records.append(
            {
                "cluster_key": cluster_key,
                "unified_ID": first["unified_ID"],
                "gene_id": first["gene_id"],
                "gene_name": first["gene_name"],
                "effective_gene_id": first["effective_gene_id"],
                "chromosome": first["chromosome"],
                "strand": first["strand"],
                "cluster_start": int(first["cluster_start"]),
                "cluster_end": int(first["cluster_end"]),
                "cluster_width": int(first["cluster_width"]),
                "mode_site_position": int(first["mode_site_position"]),
                "mode_score": first["mode_score"],
                "mode_local_n_samples": int(first["mode_local_n_samples"]),
                "mode_local_total_site_count": _format_number(
                    first["mode_local_total_site_count"]
                ),
                "mode_exact_n_samples": int(first["mode_exact_n_samples"]),
                "mode_exact_total_site_count": _format_number(
                    first["mode_exact_total_site_count"]
                ),
                "n_unique_positions": int(first["n_unique_positions"]),
                "weighted_mean_position": round(weighted_mean, 2)
                if not math.isnan(weighted_mean)
                else "",
                "weighted_position_sd": round(weighted_sd, 2)
                if not math.isnan(weighted_sd)
                else "",
                "position_iqr": _format_number(q75 - q25)
                if not math.isnan(q25) and not math.isnan(q75)
                else "",
                "n_transcripts": len(transcript_ids),
                "transcript_ids": ",".join(transcript_ids),
                "transcript_cluster_counts": _transcript_counts_string(group),
                "total_site_count": _format_number(group["site_count"].sum()),
                "n_samples": len(sample_list),
                "n_tissues": group.loc[
                    group["sample_attribute"] == "tissue", "sample"
                ].nunique(),
                "n_cell_cultures": group.loc[
                    group["sample_attribute"] == "cell_culture", "sample"
                ].nunique(),
                "sample_list": ",".join(sample_list),
                "transcript_biotype": ",".join(biotypes),
                "median_cluster_relative_abundance": round(
                    float(group["cluster_relative_abundance"].median()), 4
                )
                if "cluster_relative_abundance" in group
                and group["cluster_relative_abundance"].notna().any()
                else "",
                "filter_pass_rule": filter_row.get("filter_pass_rule", ""),
                "filter_reason": filter_row.get("filter_reason", ""),
            }
        )

    summary = pd.DataFrame(records)
    if summary.empty:
        return summary

    return summary.sort_values(
        ["chromosome", "cluster_start", "cluster_end", "strand", "effective_gene_id"],
        ignore_index=True,
    )


def sort_detailed(detailed: pd.DataFrame) -> pd.DataFrame:
    return detailed.sort_values(
        [
            "chromosome",
            "cluster_start",
            "cluster_end",
            "strand",
            "effective_gene_id",
            "transcript_id",
            "sample",
            "original_site_position",
        ],
        ignore_index=True,
    )


def warn_duplicate_coordinate_ids(summary: pd.DataFrame) -> None:
    if summary.empty:
        return
    gene_counts = summary.groupby("unified_ID")["effective_gene_id"].nunique()
    duplicated = gene_counts[gene_counts > 1]
    if not duplicated.empty:
        log.warning(
            "%d coordinate-only unified_ID values are shared by multiple effective gene ids.",
            len(duplicated),
        )


# ---------------------------------------------------------------------------
# CLI and main
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[Sequence[str]] = None):
    parser = argparse.ArgumentParser(
        description="Unify mixed-species single-sample APA calls with mode-seeded biological clustering.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Example:
    python unify_apa_sites_batch_species.py /path/to/Species_name
    python unify_apa_sites_batch_species.py /path/to/Species_name \\
        --max-cluster-width 40 --mode-support-window 15
        """,
    )
    parser.add_argument(
        "base_dir",
        type=Path,
        help="Species-level directory containing *apa_sites.txt files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for output TSV files (default: base_dir)",
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
        help="Mode score weight for local unique sample support (default: 0.7)",
    )
    parser.add_argument(
        "--count-weight",
        type=float,
        default=0.3,
        help="Mode score weight for local read count support (default: 0.3)",
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
        "--biotypes",
        default=",".join(DEFAULT_BIOTYPES),
        help="Comma-separated transcript biotypes to keep; include a trailing comma to keep blank biotypes (default: mRNA,lncRNA,lnc_RNA,protein_coding,blank)",
    )
    parser.add_argument(
        "--exclude-predicted-transcripts",
        action="store_true",
        help="Exclude RefSeq predicted transcripts with IDs starting XM_ or XR_",
    )
    parser.add_argument(
        "--keep-scaffolds",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep non-NC_ contigs/scaffolds (default: true for batch species)",
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
            "transcript-sample observations plus optional strong single-observation "
            "rescue; 'transcript-totals' uses older single/multi-transcript "
            "total-count rules (default: observations)"
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
        default=20,
        help=(
            "For --filter-strategy observations, also keep clusters with one "
            "transcript/sample observation at least this strong. Use 0 to disable "
            "(default: 20 for batch species)"
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
            "For --filter-strategy transcript-totals, required reads per supported "
            "transcript in multi-transcript clusters (default: 5)"
        ),
    )
    parser.add_argument(
        "--min-supported-transcripts",
        type=int,
        default=2,
        help=(
            "For --filter-strategy transcript-totals, minimum transcripts meeting "
            "--min-multi-transcript-count (default: 2)"
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
    parser.add_argument(
        "--skip-summary",
        action="store_true",
        help=(
            "Only write the filtered detailed *_unified_apa_sites.txt output; "
            "skip summary/audit files for faster large batch reruns"
        ),
    )
    return parser.parse_args(argv)


def _normalize_weights(sample_weight: float, count_weight: float) -> Tuple[float, float]:
    total = sample_weight + count_weight
    if total <= 0:
        log.error("sample-weight + count-weight must be positive.")
        sys.exit(1)
    if abs(total - 1.0) > 1e-9:
        log.warning(
            "Normalizing mode score weights: sample=%s count=%s",
            sample_weight,
            count_weight,
        )
    return sample_weight / total, count_weight / total


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    base_dir = args.base_dir.resolve()
    if not base_dir.is_dir():
        log.error("Base directory does not exist: %s", base_dir)
        sys.exit(1)
    output_dir = (args.output_dir or base_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

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

    sample_weight, count_weight = _normalize_weights(
        args.sample_weight, args.count_weight
    )
    mode_sample_weight, mode_count_weight = _normalize_weights(
        args.mode_sample_weight, args.mode_count_weight
    )
    biotypes = _parse_biotypes(args.biotypes)
    species_name = base_dir.name

    file_infos = discover_apa_files(base_dir)
    df = read_and_filter(
        file_infos=file_infos,
        biotypes=biotypes,
        keep_scaffolds=args.keep_scaffolds,
        keep_mitochondrial=args.keep_mitochondrial,
        exclude_predicted_transcripts=args.exclude_predicted_transcripts,
    )

    cluster_map = build_clusters(
        df=df,
        max_cluster_width=args.max_cluster_width,
        max_internal_gap=args.max_internal_gap,
        mode_support_window=args.mode_support_window,
        sample_weight=sample_weight,
        count_weight=count_weight,
        mode_sample_weight=mode_sample_weight,
        mode_count_weight=mode_count_weight,
    )
    detailed_all = assign_clusters(df, cluster_map)
    detailed_all = recalculate_cluster_relative_abundance(detailed_all)
    detailed_all = detailed_all.rename(
        columns={"cluster_relative_abundance": "prefilter_cluster_relative_abundance"}
    )

    filter_info = evaluate_cluster_filters(
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
    detailed = recalculate_cluster_relative_abundance(detailed)
    detailed = _drop_internal_filter_columns(detailed)
    detailed = sort_detailed(detailed)
    dropped = detailed_all[detailed_all["cluster_key"].isin(fail_keys)].copy()

    out_detailed = output_dir / f"{species_name}_unified_apa_sites.txt"
    detailed.to_csv(out_detailed, sep="\t", index=False)
    log.info("Wrote filtered detailed output: %s (%d rows)", out_detailed, len(detailed))

    retained_cluster_count = detailed["cluster_key"].nunique()
    if args.skip_summary:
        log.info("Skipped summary/audit outputs (--skip-summary)")
    else:
        summary = summarize_clusters(detailed, filter_info)
        filtered_out = summarize_clusters(dropped, filter_info)
        warn_duplicate_coordinate_ids(summary)

        out_summary = output_dir / f"{species_name}_unified_apa_summary.txt"
        out_filtered = output_dir / f"{species_name}_unified_apa_filtered_out.txt"

        summary.to_csv(out_summary, sep="\t", index=False)
        filtered_out.to_csv(out_filtered, sep="\t", index=False)

        retained_cluster_count = len(summary)
        log.info(
            "Wrote filtered summary output: %s (%d clusters)",
            out_summary,
            len(summary),
        )
        log.info(
            "Wrote filtered-out cluster audit: %s (%d clusters)",
            out_filtered,
            len(filtered_out),
        )

    if args.write_unfiltered:
        unfiltered_detailed = recalculate_cluster_relative_abundance(detailed_all.copy())
        unfiltered_detailed = _drop_internal_filter_columns(unfiltered_detailed)
        unfiltered_detailed = sort_detailed(unfiltered_detailed)
        unfiltered_summary = summarize_clusters(unfiltered_detailed, filter_info)
        out_unfiltered_detailed = output_dir / f"{species_name}_unified_apa_sites.unfiltered.txt"
        out_unfiltered_summary = output_dir / f"{species_name}_unified_apa_summary.unfiltered.txt"
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
        retained_cluster_count,
        filter_info["cluster_key"].nunique(),
    )


if __name__ == "__main__":
    main()
