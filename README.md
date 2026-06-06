# ApaAtlas

**ApaAtlas** is a web-based scientific database for exploring isoform-level polyadenylation (PA) sites across diverse species, tissues, and cell lines. The resource links PA site usage to individual transcript isoforms, enabling users to examine alternative 3′ end formation at a resolution that is not preserved by gene-level summaries.

ApaAtlas provides interactive search, transcript- and locus-level visualization, database-scale statistics, and downloadable result tables for downstream analysis.

---

## Overview

Alternative polyadenylation shapes transcript 3′ ends and can alter mRNA stability, localization, translation, and post-transcriptional regulation. Many resources summarize PA sites at the gene level, which can obscure transcript-specific regulatory patterns. ApaAtlas was designed to preserve the connection between each PA site and its corresponding transcript isoform.

The web interface supports:

- gene, transcript, species, and sample-based search;
- transcript-level PA site summaries;
- locus-level genome browser visualization;
- sample-resolved abundance profiles;
- PA motif and APA confidence annotations;
- database-wide statistics;
- export of PA site tables, BED tracks, and abundance matrices.

---

## Workflow

ApaAtlas is constructed from long-read transcriptomic datasets using an isoform-aware PA site discovery workflow. Reads are aligned to reference genomes, assigned to transcript models, filtered for full-length support, clustered into PA site groups, screened for internal priming artifacts, and summarized as transcript-resolved PA site annotations.

![Isoform-level PA site workflow](frontend/public/images/trek-workflow.jpg)

The workflow is intended to retain transcript identity throughout PA site discovery, so that alternative 3′ end usage can be interpreted in the context of specific isoforms rather than only at the gene level.

---

## Main Features

| Module | Purpose |
|---|---|
| **Search** | Query genes, transcripts, species, and samples with interactive filtering and sortable results. |
| **Gene View** | Review all transcript isoforms for a gene and inspect associated PA sites, abundance, APA level, and representative transcript status. |
| **Locus View** | Visualize a selected transcript locus with exon structure, PA sites, abundance heatmaps, PA motifs, and genome-browser tracks. |
| **Statistics** | Explore database-scale summaries, including species richness, PA site multiplicity, PA motif composition, and highly regulated genes. |
| **Download** | Export PA site records, genome browser BED files, and sample abundance matrices in analysis-ready formats. |
| **Help** | Read field definitions, workflow notes, FAQ entries, confidence-level explanations, and genome/reference resource links. |

---

## Repository Structure

```text
ApaAtlas/
├── backend/                 # FastAPI application and SQLite database mount point
├── frontend/                # Vite/Vue frontend served by nginx in production
├── data/                    # Runtime genome-browser BED and BED index files
├── docs/                    # Curated reference metadata and supporting documentation
├── scripts/                 # Data-processing and deployment helper scripts
├── stack.yml                # Docker Swarm stack definition
├── start.sh                 # Local setup and development launcher
└── README.md
```

---

## Local Development

ApaAtlas uses a FastAPI backend and a Vite frontend. The local development workflow is managed by `start.sh`.

```bash
./start.sh
```

After startup:

| Service | URL |
|---|---|
| Frontend | `http://localhost:3000` |
| Backend API | `http://localhost:8000` |
| API documentation | `http://localhost:8000/docs` |

The local script prepares the runtime environment, checks whether the local database and genome-browser indices are available, installs frontend dependencies when needed, and starts both services.

---

## Deployment

ApaAtlas is configured for Docker Swarm deployment behind an external Traefik reverse proxy. The production deployment uses precomputed runtime data and does not run the data-construction workflow inside containers.

Create a deployment bundle locally:

```bash
scripts/deploy/package_for_server.sh
```

Copy the generated archive and deployment helper to the target server:

```bash
scp deploy_packages/ApaAtlas-deploy-*.tar.gz deploy_packages/deploy_on_server.sh user@server:/home/tflab/
```

Deploy on the server:

```bash
cd /home/tflab
bash deploy_on_server.sh ApaAtlas-deploy-YYYYMMDD-HHMMSS.tar.gz
```

The server-side script removes an existing `apaatlas` stack if present, backs up the previous deployment directory, builds local Docker images, and redeploys the Swarm stack.

The configured production domain is:

```text
https://apaatlas.sls.cuhk.edu.hk
```

---

## Data Access

ApaAtlas provides downloadable result tables directly through the web interface and API. Supported exports include:

- PA site tables with genomic coordinates, cluster ranges, motif annotations, and abundance summaries;
- genome browser BED files using database PA site identifiers;
- sample abundance matrices with count and relative-abundance columns.

Genome and annotation reference parent links are available from the Help page under **Genome and annotation references**.

---

## Citation

Citation information will be added after publication. If you use ApaAtlas before formal publication, please cite the project website and contact the maintainers for the recommended acknowledgement.

---

## Contact

For questions, bug reports, or feature requests:

- Email: `tf.chan@cuhk.edu.hk`
- GitHub Issues: `https://github.com/zjzace/ApaAtlas/issues`
