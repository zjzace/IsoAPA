#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
DATA_DIR="$SCRIPT_DIR/data"
CONDA_SH="/home/zjzace/miniforge3/etc/profile.d/conda.sh"
ENV_NAME="apaatlas"
DB_FILE="$BACKEND_DIR/apa_atlas.db"
DATA_HASH_FILE="/tmp/apaatlas_data_hash.txt"

get_data_hash() {
    find "$DATA_DIR" -type f \( -name "*.txt" -o -name "*.tsv" -o -name "*.gtf" -o -name "*.gff3" -o -name "*.fa" -o -name "*.fasta" \) -exec md5sum {} \; 2>/dev/null | sort | md5sum | cut -d' ' -f1
}

should_reload_db() {
    if [ ! -f "$DB_FILE" ]; then
        return 0
    fi
    
    if [ ! -f "$DATA_HASH_FILE" ]; then
        return 0
    fi
    
    CURRENT_HASH=$(get_data_hash)
    STORED_HASH=$(cat "$DATA_HASH_FILE")
    
    if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
        return 0
    fi
    
    return 1
}

echo "=========================================="
echo "  Starting ApaAtlas..."
echo "=========================================="

if mamba env list | grep -q "[[:space:]]$ENV_NAME "; then
    echo ""
    echo "[1/6] Conda environment '$ENV_NAME' already exists, skipping creation."
else
    echo ""
    echo "[1/6] Creating conda environment '$ENV_NAME'..."
    cd "$BACKEND_DIR"
    mamba env create -f environment.yml
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create conda environment"
        exit 1
    fi
fi

echo ""
echo "[2/6] Activating conda environment..."
source "$CONDA_SH"
conda activate "$ENV_NAME"

if [ $? -ne 0 ]; then
    echo "Error: Failed to activate conda environment"
    exit 1
fi

echo "  Python version: $(python --version)"

if ! command -v node &> /dev/null; then
    echo "Error: node not found"
    exit 1
fi

echo ""
echo "[3/6] Checking for data changes..."
if should_reload_db; then
    echo "  New/changed data detected, recreating database..."
    rm -f "$DB_FILE"
    CURRENT_HASH=$(get_data_hash)
    echo "$CURRENT_HASH" > "$DATA_HASH_FILE"
    echo "[4/6] Initializing database and loading data..."
    cd "$BACKEND_DIR"
    python -m app.services.etl
    if [ $? -ne 0 ]; then
        echo "Warning: ETL failed or no data to load, continuing..."
    fi
else
    echo "  No data changes detected, using existing database."
    echo "[4/6] Skipping database initialization."
fi

echo ""
echo "[5/6] Starting backend server on port 8000..."
cd "$BACKEND_DIR"
python -m uvicorn main:app --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!

sleep 3

echo "[6/6] Starting frontend server on port 3000..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo "  Installing frontend dependencies..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!

sleep 5

echo ""
echo "=========================================="
echo "  ApaAtlas is running!"
echo "=========================================="
echo ""
echo "  Backend API:  http://localhost:8000"
echo "  Frontend:    http://localhost:3000"
echo ""
echo "  Press Ctrl+C to stop all servers"
echo ""

echo "$BACKEND_PID" > /tmp/apaatlas_backend.pid
echo "$FRONTEND_PID" > /tmp/apaatlas_frontend.pid

trap "echo ''; echo 'Stopping servers...'; kill $(cat /tmp/apaatlas_backend.pid) $(cat /tmp/apaatlas_frontend.pid) 2>/dev/null; rm -f /tmp/apaatlas_backend.pid /tmp/apaatlas_frontend.pid; conda deactivate 2>/dev/null; exit 0" SIGINT SIGTERM

wait
