# ApaAtlas - Alternative Polyadenylation Database

A modern web-based database for browsing, searching, and visualizing isoform-level Alternative Polyadenylation (APA) loci.

## Features

- **Landing Page**: Visually striking hero section with search, database statistics dashboard, and educational content about APA
- **Search & Browse**: Multi-field filtering, autocomplete, paginated results, and CSV export
- **Locus Detail**: APA site visualization with sample-specific data and comparative charts
- **Gene Detail**: Overview of all transcripts and APA sites for a gene
- **Modern UI**: Material Design aesthetic with dark mode support
- **Scalable**: SQLite for development, PostgreSQL-ready for production

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Vue 3 + Vuetify 3
- **Visualization**: Chart.js

## Project Structure

```
ApaAtlas/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # ETL script
│   ├── main.py           # FastAPI app
│   ├── requirements.txt  # Python dependencies
│   └── environment.yml   # Conda/mamba environment
├── frontend/
│   ├── src/
│   │   ├── views/        # Home, Search, LocusDetail, GeneDetail
│   │   ├── plugins/      # Vuetify config
│   │   ├── router/
│   │   └── services/     # API service
│   ├── package.json
│   └── vite.config.js
├── data/                  # APA data files (not included in repo)
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.9+ (via mamba/conda)
- Node.js 18+
- npm or yarn

### Option 1: Using Mamba/Conda

```bash
# Create environment from.yml file
cd backend
mamba env create -f environment.yml

# Activate environment
mamba activate apaatlas

# Initialize database and load data
python -m app.services.etl

# Start the API server
uvicorn main:app --reload --port 8000
```

### Option 2: Using Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database and load data
python -m app.services.etl

# Start the API server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

### Using start.sh

For convenience, you can use the startup script:

```bash
./start.sh
```

This will start both backend (port 8000) and frontend (port 3000).

## Data Setup

The `data/` folder contains APA data files in the following structure:

```
data/
└── homo_sapiens/
    ├── reference/
    │   ├── Homo_sapiens.GRCh38.115.gtf
    │   └── Homo_sapiens.GRCh38.dna_sm.primary_assembly.fa
    ├── A549/A549.apa_sites.txt
    ├── HepG2/HepG2.apa_sites.txt
    └── K562/K562.apa_sites.txt
```

Each sample folder contains APA sites data with columns:
- transcript_id, gene_id, gene_name, chromosome, strand, ID, site_position, site_count, site_abundance

Run the ETL to load data:
```bash
python -m app.services.etl
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/stats` | GET | Dashboard statistics |
| `/api/v1/search` | GET | Search transcripts with filters |
| `/api/v1/autocomplete` | GET | Autocomplete suggestions |
| `/api/v1/transcript/{id}` | GET | Locus detail by transcript ID |
| `/api/v1/gene/{id}` | GET | Gene detail with all transcripts |
| `/api/v1/species` | GET | List all species |
| `/api/v1/samples` | GET | List all samples |

## Search Parameters

- `gene_name`: Gene symbol (e.g., "ARF5")
- `transcript_id`: Transcript identifier (e.g., "ENST00000000233")
- `gene_id`: Gene identifier (e.g., "ENSG00000004059")
- `sample`: Sample name (e.g., "A549", "HepG2", "K562")
- `species`: Species name (e.g., "Human")
- `chromosome`: Chromosome
- `page`: Page number (default: 1)
- `limit`: Results per page (default: 50)

## Example Queries

```bash
# Get statistics
curl http://localhost:8000/api/v1/stats

# Search for a gene
curl "http://localhost:8000/api/v1/search?gene_name=ARF5"

# Get locus detail
curl http://localhost:8000/api/v1/transcript/ENST00000000233

# Get gene detail
curl http://localhost:8000/api/v1/gene/ENSG00000004059
```

## Database Schema

The database is normalized with the following tables:

- **species**: Species information
- **samples**: Sample names (cell lines/tissues), linked to species
- **genes**: Gene information (ID, name, chromosome, strand)
- **transcripts**: Transcript records, linked to genes
- **apa_sites**: APA site data (unique by transcript + position), with sample_data JSON

## Production Deployment

For production with PostgreSQL:

1. Update `backend/app/config.py`:
```python
DATABASE_URL: str = "postgresql://user:password@localhost/apa_atlas"
```

2. Build frontend:
```bash
cd frontend
npm run build
```

3. Configure reverse proxy (nginx) to serve both backend and frontend

## License

MIT License
