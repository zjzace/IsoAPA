# APA Confidence Levels

`annotate_apa.py` assigns one confidence label per APA cluster using the PAS
annotation plus cluster support evidence.

## Support Metrics

For each `cluster_key`, support is calculated from the unified APA sites table.

- `n_samples`: number of unique samples supporting the cluster.
- `n_transcripts`: number of unique transcripts supporting the cluster.
- `total_site_count`: total read count across all rows in the cluster.
- `supported_observations`: number of `transcript_id + sample` observations whose
  cluster-level summed `site_count` is at least `5`.
- `max_observation_count`: maximum cluster-level summed `site_count` among all
  `transcript_id + sample` observations.
- `max_cluster_relative_abundance`: maximum `cluster_relative_abundance` among
  all `transcript_id + sample` observations.

## Support Tiers

Strong support:

```text
n_samples >= 2
AND supported_observations >= 3
AND total_site_count >= 30
```

Moderate support:

```text
supported_observations >= 2
AND total_site_count >= 10
```

Single-rescue support:

```text
supported_observations < 2
AND max_observation_count >= 20
AND max_cluster_relative_abundance >= 0.25
```

## PAS Types

PAS type comes directly from `annotate_apa.py`.

- `canonical`: canonical upstream hexamer, currently `AATAAA` or `ATTAAA`.
- `variant`: variant upstream hexamer.
- `upstream`: upstream auxiliary 4-mer.
- `downstream`: downstream auxiliary 4-mer.
- `none`: no PAS motif found.

## APA Levels

Levels are assigned from strongest to weakest.

```text
APA-L1:
  canonical PAS
  AND strong support

APA-L2:
  canonical PAS
  AND moderate support

  OR

  variant PAS
  AND strong support

APA-L3:
  variant PAS
  AND moderate support

  OR

  upstream/downstream PAS
  AND strong support

  OR

  no PAS
  AND strong support

APA-L4:
  upstream/downstream/no PAS
  AND moderate support

APA-L5:
  single-rescue support
  OR anything weaker than APA-L1 to APA-L4
```

## Interpretation

- `APA-L1` and `APA-L2`: high-confidence APA sites.
- `APA-L3`: moderate-confidence APA sites.
- `APA-L4`: lower-confidence retained APA sites.
- `APA-L5`: candidate APA sites, including single-observation rescue sites.
