# ApaAtlas

**ApaAtlas** is a web-based database for exploring isoform-level alternative polyadenylation (APA) sites across multiple species and cell types. It provides an integrated interface for searching, visualizing, and downloading APA site data derived from RNA-seq experiments, with annotations referenced to the NCBI/RefSeq genome assemblies.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Model](#data-model)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Launch](#quick-launch)
  - [Manual Setup](#manual-setup)
- [Data Setup](#data-setup)
- [API Reference](#api-reference)
- [Download Formats](#download-formats)
- [Production Deployment](#production-deployment)
- [License](#license)

---

## Overview

Alternative polyadenylation generates transcript isoforms with distinct 3′ ends from a single gene. ApaAtlas curates polyadenylation sites at the transcript isoform level, linking each site to its supporting samples and providing quantitative abundance estimates per sample. The database currently supports four species (Human, Mouse, Rat, Zebrafish) and is designed to accommodate additional species through its ETL pipeline.

---

## Features

| Module | Description |
|---|---|
| **Home** | Full-text search across gene name, RefSeq transcript ID, sample, and species with live autocomplete |
| **Search & Browse** | Paginated, multi-field filtered results table with per-row navigation |
| **Gene Detail** | All transcripts and associated APA sites for a given gene, with expandable per-transcript tables |
| **Locus Detail** | Per-site visualization including transcript structure (from BED12 reference), per-sample abundance bar charts, and an embedded IGV genome browser track |
| **Statistics** | Database-wide summary statistics: site counts by species, chromosome, strand, and top genes by APA site count |
| **Download** | Bulk data export in three formats: PA Sites (TSV/CSV), Genome Browser BED, and Sample Abundance Matrix |
| **Help** | Guided documentation for all pages and data fields |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI 0.109, SQLAlchemy 2.0, Alembic 1.13 |
| **Database** | SQLite (development) / PostgreSQL (production, via psycopg2) |
| **Frontend** | Vue 3.4, Vuetify 3.5, Vue Router 4, Vite 5 |
| **Visualization** | Chart.js 4, D3 7, IGV.js 2.15 |
| **Styling** | Material Design (Vuetify), Sass |

---

## Project Structure

```
ApaAtlas/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # All API and download endpoints
│   │   ├── models/
│   │   │   └── database.py        # SQLAlchemy ORM models
│   │   ├── schemas/
│   │   │   └── schemas.py         # Pydantic request/response schemas
│   │   ├── services/
│   │   │   └── etl.py             # Data ingestion pipeline
│   │   └── config.py              # Application settings
│   ├── build_bed12_index.py       # BED12 byte-offset index builder
│   ├── main.py                    # FastAPI application entry point
│   ├── requirements.txt           # Python package dependencies
│   └── environment.yml            # Conda/mamba environment specification
├── frontend/
│   ├── src/
│   │   ├── views/                 # Page components
│   │   │   ├── Home.vue
│   │   │   ├── Search.vue
│   │   │   ├── GeneDetail.vue
│   │   │   ├── LocusDetail.vue
│   │   │   ├── Statistics.vue
│   │   │   ├── Download.vue
│   │   │   └── Help.vue
│   │   ├── components/            # Shared UI components
│   │   ├── services/              # API client (Axios)
│   │   ├── plugins/               # Vuetify configuration
│   │   └── router/                # Vue Router configuration
│   ├── package.json
│   └── vite.config.js             # Vite build config with API proxy
├── data/                          # APA data files (not tracked by git)
├── start.sh                       # One-shot setup and launch script
└── .env.example                   # Environment variable template
```

---

## Data Model

The database schema is normalized across five tables:

```
Species ──< Samples
Species ──< APASites
Genes ──< Transcripts ──< APASites
```

| Table | Key Columns |
|---|---|
| `species` | `name`, `latin_name`, `assembly` |
| `samples` | `name`, `sample_type`, `species_id` |
| `genes` | `gene_id` (Entrez), `gene_name`, `chromosome`, `strand` |
| `transcripts` | `transcript_id` (RefSeq), `gene_id` |
| `apa_sites` | `unified_id` (site_id), `transcript_id`, `species_id`, `mode_site_position`, `site_count`, `site_abundance`, `sample_data` (JSON), `cluster_start`, `cluster_end`, `sequence`, `pas_motif`, `pas_position`, `pas_type` |

The `sample_data` column stores a JSON array of per-sample records:

```json
[
  {
    "sample_name": "A549",
    "sample_type": "cell_culture",
    "original_site_position": 5094791,
    "site_count": 142,
    "site_abundance": 0.312
  }
]
```

---

## Getting Started

### Prerequisites

- **Python 3.9+** managed via [Miniforge3 / Mamba](https://github.com/conda-forge/miniforge) (recommended) or `venv`
- **Node.js 18+** and npm
- APA site data files placed under `data/` (see [Data Setup](#data-setup))

### Quick Launch

The included `start.sh` script handles the full setup and launch sequence:

1. Creates the `apaatlas` conda environment (if absent)
2. Detects data file changes and rebuilds the SQLite database via ETL
3. Builds BED12 byte-offset indices for transcript structure visualization
4. Installs frontend npm packages (first run only)
5. Starts the FastAPI backend on port 8000
6. Starts the Vite development server on port 3000

```bash
./start.sh
```

Once running:

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

Press `Ctrl+C` to stop both servers.

### Manual Setup

**Backend:**

```bash
cd backend

# Option A — Conda/Mamba (recommended)
mamba env create -f environment.yml
mamba activate apaatlas

# Option B — pip virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Ingest data and initialize the database
python -m app.services.etl

# Start the API server
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

---

## Data Setup

Place raw APA site files under `data/` following this directory layout:

```
data/
├── homo_sapiens/
│   ├── homo_sapiens_unified_apa_sites.txt      # Required: unified cross-sample site table
│   ├── homo_sapiens_unified_apa.anno.txt       # Optional: PAS motif / cluster annotations
│   └── reference/
│       └── *.bed                               # BED12 transcript structure file (for IGV)
├── mus_musculus/
│   └── ...
├── rattus_norvegicus/
│   └── ...
└── danio_rerio/
    └── ...
```

**Supported species folders** and their genome assemblies:

| Folder | Common Name | Assembly |
|---|---|---|
| `homo_sapiens` | Human | GRCh38 |
| `mus_musculus` | Mouse | GRCm39 |
| `rattus_norvegicus` | Rat | rn6 |
| `danio_rerio` | Zebrafish | GRCz11 |

**Unified APA sites file format** (tab-separated, with header):

| Column | Description |
|---|---|
| `transcript_id` | NCBI RefSeq transcript identifier |
| `gene_id` | NCBI Entrez Gene identifier |
| `gene_name` | Official gene symbol |
| `chromosome` | Chromosome name |
| `strand` | `+` or `-` |
| `unified_ID` | Cross-sample APA site identifier |
| `site_position` | Genomic coordinate of the PA cleavage site |
| `site_count` | Read support count |
| `site_abundance` | Relative abundance within the transcript (0–1) |
| `sample_name` | Sample or cell line name |
| `sample_type` | Sample type (e.g., `cell_culture`, `tissue`) |

Run the ETL pipeline to (re-)build the database:

```bash
cd backend
python -m app.services.etl
```

The pipeline performs two passes per species: aggregating per-sample data into per-site clusters, then bulk-inserting records in batches of 5,000. Changes are detected automatically by `start.sh` using an MD5 hash of all data files.

---

## API Reference

All endpoints are prefixed with `/api/v1`.

### Core Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/stats` | Database-wide statistics (counts, distributions) |
| `GET` | `/search` | Search and filter APA sites |
| `GET` | `/autocomplete` | Autocomplete suggestions for search fields |
| `GET` | `/transcript/{transcript_id}` | Full locus detail for a RefSeq transcript |
| `GET` | `/gene/{gene_id}` | All transcripts and APA sites for a gene |
| `GET` | `/species` | List all species |
| `GET` | `/samples` | List all samples |

### Search Parameters (`/search`)

| Parameter | Type | Description |
|---|---|---|
| `gene_name` | string | Gene symbol, partial match (e.g., `ARF5`) |
| `transcript_id` | string | RefSeq transcript ID, partial match |
| `gene_id` | string | Entrez Gene ID |
| `sample` | string | Sample name (e.g., `A549`) |
| `species` | string | Species name (e.g., `Human`) |
| `chromosome` | string | Chromosome (e.g., `chr1`) |
| `page` | integer | Page number (default: `1`) |
| `limit` | integer | Results per page (default: `50`) |

### Download Endpoints

| Method | Path | Format | Description |
|---|---|---|---|
| `GET` | `/download/apa-sites` | TSV / CSV | Per-sample PA site table |
| `GET` | `/download/bed` | BED6 | Genome browser track |
| `GET` | `/download/abundance-matrix` | TSV | PA site × sample count matrix |
| `GET` | `/download/transcripts` | TSV / CSV | Transcript-level summary |

All download endpoints accept an optional `species` query parameter to filter by species.

**Example requests:**

```bash
# Retrieve all Human PA sites as TSV
curl "http://localhost:8000/api/v1/download/apa-sites?species=Human&format=tsv" \
  -o pa_sites_human.tsv

# Search for a gene
curl "http://localhost:8000/api/v1/search?gene_name=ZFP3&species=Human"

# Get locus detail
curl "http://localhost:8000/api/v1/transcript/NM_001234"
```

---

## Download Formats

### PA Sites (TSV/CSV)

One row per APA site per sample.

| Column | Type | Description |
|---|---|---|
| `gene_name` | string | Official gene symbol |
| `gene_id` | string | NCBI Entrez Gene ID |
| `transcript_id` | string | NCBI RefSeq Transcript ID |
| `site_id` | string | Unique APA site identifier (shared across samples) |
| `representative_position` | integer | Consensus genomic coordinate (mode across samples) |
| `sample_site_position` | integer | PA cleavage coordinate in this specific sample |
| `site_abundance` | float | Relative abundance within the transcript for this sample (0–1) |
| `species` | string | Species name |
| `sample` | string | Sample / cell line name |

### Genome Browser BED (BED6)

Compatible with IGV, UCSC Genome Browser, and JBrowse.

| Column | Type | Description |
|---|---|---|
| `chrom` | string | Chromosome in UCSC format (e.g., `chr1`) |
| `chromStart` | integer | 0-based start coordinate |
| `chromEnd` | integer | 1-based end coordinate (half-open interval) |
| `name` | string | `gene_name\|transcript_id\|site_id` |
| `score` | string | `.` (no score assigned) |
| `strand` | string | `+` or `-` |

### Sample Abundance Matrix (TSV)

One row per APA site; one column per sample containing the read count at that site.

| Column | Type | Description |
|---|---|---|
| `site_id` | string | APA site identifier |
| `transcript_id` | string | NCBI RefSeq Transcript ID |
| `gene_name` | string | Official gene symbol |
| `chromosome` | string | Chromosome |
| `strand` | string | `+` or `-` |
| `species` | string | Species name |
| `[sample_name]` | integer | One column per sample — read count at this PA site |

---

## Production Deployment

**1. Configure the database connection**

Copy `.env.example` to `.env` and set the PostgreSQL connection string:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/apa_atlas
```

**2. Run database migrations**

```bash
cd backend
alembic upgrade head
```

**3. Build the frontend**

```bash
cd frontend
npm run build
```

The compiled assets are written to `frontend/dist/`.

**4. Configure a reverse proxy**

Use nginx (or equivalent) to serve the frontend static files and proxy API requests:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend static files
    root /path/to/ApaAtlas/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**5. Start the backend**

```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
```

---

## License

MIT License
