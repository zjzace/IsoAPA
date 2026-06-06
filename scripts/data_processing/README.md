# Data Processing Scripts

This directory stores standalone utilities used before loading data into
ApaAtlas. They are not part of the web application runtime.

## Scripts

- `download_apa_data.sh`: downloads long-read RNA-seq FASTQ files from SRA/ENA
  using the local metadata TSV and local storage paths configured in the script.
- `unify_apa_sites_batch_species.py`: batches per-sample APA calls into
  species-level unified PA site tables.
- `unify_apa_sites_dp_segment.py`: alternative dynamic-programming PA site
  clustering implementation for unifying cleavage positions.
- `annotate_apa.py`: annotates unified PA clusters with flanking sequence, PAS
  motifs, PAS type, search level, and APA confidence level.
- `append_representative_status.py`: appends a `representative_status` column to
  each species-level `*_unified_apa_sites.txt` table using local transcript tags
  from the species reference annotation file. Known values include `MANE_Select`,
  `RefSeq_Select`, `Ensembl_Canonical`, `APPRIS_Principal`, and
  `not_representative`.

These scripts contain environment- and filesystem-specific paths from the data
processing workflow. Review the path variables and command-line arguments before
running them on another machine.
