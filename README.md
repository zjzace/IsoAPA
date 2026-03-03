# ApaAtlas - Alternative Polyadenylation Database

A modern web-based database for browsing, searching, and visualizing isoform-level Alternative Polyadenylation (APA) loci.

## Features

- **Landing Page**: Visually striking hero section with search, database statistics dashboard, and educational content about APA
- **Search & Browse**: Multi-field filtering, autocomplete, paginated results, and CSV export
- **Locus Detail**: IGV.js genome browser integration, APA site visualization, and comparative charts
- **Modern UI**: Material Design aesthetic with dark mode support
- **Scalable**: SQLite for development, PostgreSQL-ready for production

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Vue 3 + Vuetify 3
- **Visualization**: Chart.js, IGV.js

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
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── views/        # Home, Search, LocusDetail
│   │   ├── plugins/      # Vuetify config
│   │   ├── router/
│   │   └── services/     # API service
│   ├── package.json
│   └── vite.config.js
├── data/
│   └── apa_sites_expanded.txt
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### 1. Backend Setup

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

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/stats` | GET | Dashboard statistics |
| `/api/v1/search` | GET | Search transcripts with filters |
| `/api/v1/autocomplete` | GET | Autocomplete suggestions |
| `/api/v1/transcript/{id}` | GET | Locus detail by transcript ID |
| `/api/v1/species` | GET | List all species |
| `/api/v1/tissues` | GET | List all tissues |

## Search Parameters

- `gene_name`: Gene symbol (e.g., "SIRV5")
- `transcript_id`: Transcript identifier
- `gene_id`: Gene identifier
- `tissue`: Tissue name
- `species`: Species name
- `chromosome`: Chromosome
- `page`: Page number (default: 1)
- `limit`: Results per page (default: 50)

## Example Queries

```bash
# Get statistics
curl http://localhost:8000/api/v1/stats

# Search for a gene
curl "http://localhost:8000/api/v1/search?gene_name=SIRV5"

# Get locus detail
curl http://localhost:8000/api/v1/transcript/SIRV512
```

## Database Schema

The database is normalized with the following tables:

- **species**: Species names
- **tissues**: Tissue names (linked to species)
- **genes**: Gene information (ID, name, chromosome, strand)
- **transcripts**: Transcript records (linked to genes)
- **apa_sites**: APA site data (linked to transcripts, tissues, species)

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
