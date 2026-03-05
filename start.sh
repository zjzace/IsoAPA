#!/bin/bash
# =============================================================================
#  ApaAtlas – one-shot setup & launch script
#
#  Steps performed on every run:
#    1. Locate conda/mamba and create the 'apaatlas' environment if needed
#    2. Activate the environment
#    3. Verify Node.js is available
#    4. Build GTF byte-offset index (.tidx) for every species that needs one
#    5. Build FASTA byte-offset index (.fidx) for every species that needs one
#    6. Detect data changes; rebuild SQLite DB + run ETL when needed
#    7. Install frontend npm deps if missing
#    8. Start the backend (uvicorn, port 8000)
#    9. Start the frontend (vite dev, port 3000)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
DATA_DIR="$SCRIPT_DIR/data"
ENV_NAME="apaatlas"
DB_FILE="$BACKEND_DIR/apa_atlas.db"
# Store hash alongside the DB so it travels with the project on the same machine
DATA_HASH_FILE="$BACKEND_DIR/.data_hash"

# ─── helpers ──────────────────────────────────────────────────────────────────

log()  { echo ""; echo "$1"; }
info() { echo "  $1"; }
ok()   { echo "  [ok] $1"; }
warn() { echo "  [warn] $1"; }
die()  { echo ""; echo "ERROR: $1" >&2; exit 1; }

# MD5 (portable: md5sum on Linux, md5 on macOS)
md5_cmd() {
    if command -v md5sum &>/dev/null; then
        md5sum "$1" | awk '{print $1}'
    else
        md5 -q "$1"
    fi
}

# Hash all APA data files (TSV/TXT) – excludes large reference binaries
get_data_hash() {
    find "$DATA_DIR" -type f \( -name "*.txt" -o -name "*.tsv" \) \
        ! -path "*/reference/*" -print0 2>/dev/null \
        | sort -z \
        | xargs -0 md5sum 2>/dev/null \
        | md5sum | awk '{print $1}' \
        || echo "none"
}

should_reload_db() {
    [[ ! -f "$DB_FILE" ]] && return 0
    [[ ! -f "$DATA_HASH_FILE" ]] && return 0
    local current stored
    current=$(get_data_hash)
    stored=$(cat "$DATA_HASH_FILE")
    [[ "$current" != "$stored" ]] && return 0
    return 1
}

# ─── step 1 : conda / mamba environment ──────────────────────────────────────

log "=========================================="
log "  ApaAtlas – setup & launch"
log "=========================================="

log "[1/9] Conda environment"

# Locate mamba or conda (prefer mamba)
CONDA_EXE=""
for candidate in mamba conda; do
    if command -v "$candidate" &>/dev/null; then
        CONDA_EXE="$candidate"
        break
    fi
done

# If neither is on PATH try the most common install locations
if [[ -z "$CONDA_EXE" ]]; then
    for base in \
        "$HOME/Tools/Miniforge3" \
        "$HOME/miniforge3" \
        "$HOME/mambaforge" \
        "$HOME/miniconda3" \
        "$HOME/anaconda3" \
        "/opt/conda" \
        "/opt/homebrew/Caskroom/mambaforge/base"
    do
        for candidate in mamba conda; do
            if [[ -x "$base/bin/$candidate" ]]; then
                CONDA_EXE="$base/bin/$candidate"
                CONDA_BASE="$base"
                break 2
            fi
        done
    done
fi

[[ -z "$CONDA_EXE" ]] && die "conda/mamba not found. Install Miniforge3 from https://github.com/conda-forge/miniforge and re-run."

info "Using: $CONDA_EXE"

# Derive base prefix so we can source activate
if [[ -z "${CONDA_BASE:-}" ]]; then
    CONDA_BASE="$("$CONDA_EXE" info --base 2>/dev/null || true)"
fi

# Activate helper: source the conda shell functions then activate
activate_env() {
    local init_script=""
    for candidate in \
        "$CONDA_BASE/etc/profile.d/conda.sh" \
        "$CONDA_BASE/etc/profile.d/mamba.sh"
    do
        if [[ -f "$candidate" ]]; then
            init_script="$candidate"
            break
        fi
    done

    if [[ -n "$init_script" ]]; then
        # shellcheck disable=SC1090
        source "$init_script"
        conda activate "$ENV_NAME" 2>/dev/null || true
    else
        # Fallback: prepend env bin to PATH directly
        local env_bin
        env_bin="$("$CONDA_EXE" run -n "$ENV_NAME" python -c 'import sys,os; print(os.path.dirname(sys.executable))' 2>/dev/null || true)"
        if [[ -n "$env_bin" ]]; then
            export PATH="$env_bin:$PATH"
        fi
    fi
}

# Create environment if it doesn't exist
if "$CONDA_EXE" env list 2>/dev/null | grep -qE "(^|\s)${ENV_NAME}(\s|$)"; then
    ok "Environment '$ENV_NAME' already exists"
else
    info "Creating environment '$ENV_NAME' from $BACKEND_DIR/environment.yml ..."
    "$CONDA_EXE" env create -f "$BACKEND_DIR/environment.yml" \
        || die "Failed to create conda environment"
    ok "Environment created"
fi

# ─── step 2 : activate ────────────────────────────────────────────────────────

log "[2/9] Activating environment"
activate_env

# Resolve python inside the environment (robust even if activate did nothing)
PYTHON="$("$CONDA_EXE" run -n "$ENV_NAME" which python 2>/dev/null \
          || command -v python3 \
          || die "python not found")"
info "Python: $PYTHON ($($PYTHON --version 2>&1))"

# ─── step 3 : node.js ─────────────────────────────────────────────────────────

log "[3/9] Checking Node.js"
if ! command -v node &>/dev/null; then
    die "node not found. Install Node.js (https://nodejs.org) and re-run."
fi
ok "Node $(node --version) / npm $(npm --version)"

# ─── step 4 : GTF byte-offset index ──────────────────────────────────────────

log "[4/9] GTF index (.tidx)"

# Walk every species reference directory and build an index for any GTF that
# lacks one (or whose GTF is newer than its index).
INDEXER="$BACKEND_DIR/build_gtf_index.py"

if [[ ! -f "$INDEXER" ]]; then
    die "GTF indexer not found at $INDEXER"
fi

shopt -s nullglob
found_gtf=false
for ref_dir in "$DATA_DIR"/*/reference; do
    for gtf_file in "$ref_dir"/*.gtf "$ref_dir"/*.gff3; do
        [[ -f "$gtf_file" ]] || continue
        found_gtf=true
        tidx_file="${gtf_file}.tidx"
        needs_index=false

        if [[ ! -f "$tidx_file" ]]; then
            needs_index=true
            info "No index found for $(basename "$gtf_file")"
        elif [[ "$gtf_file" -nt "$tidx_file" ]]; then
            needs_index=true
            info "GTF is newer than index for $(basename "$gtf_file"), rebuilding..."
        else
            ok "Index up-to-date: $(basename "$tidx_file")"
        fi

        if $needs_index; then
            info "Building index for $(basename "$gtf_file") (this runs once, ~10-30s) ..."
            "$PYTHON" "$INDEXER" "$gtf_file" \
                || warn "Failed to build index for $gtf_file — structure endpoint may be slow"
        fi
    done
done
shopt -u nullglob

if ! $found_gtf; then
    warn "No GTF files found under $DATA_DIR/*/reference/ — skipping index step"
fi

# ─── step 5 : FASTA byte-offset index ────────────────────────────────────────

log "[5/9] FASTA index (.fidx)"

FASTA_INDEXER="$BACKEND_DIR/build_fasta_index.py"

if [[ ! -f "$FASTA_INDEXER" ]]; then
    warn "FASTA indexer not found at $FASTA_INDEXER — skipping (sequence endpoints may fail)"
else
    shopt -s nullglob
    found_fasta=false
    for ref_dir in "$DATA_DIR"/*/reference; do
        for fa_file in "$ref_dir"/*.fa "$ref_dir"/*.fasta "$ref_dir"/*.fa.gz; do
            [[ -f "$fa_file" ]] || continue
            # Skip .gz — random access requires uncompressed file
            [[ "$fa_file" == *.gz ]] && { warn "Skipping compressed FASTA: $(basename "$fa_file") — decompress for sequence access"; continue; }
            found_fasta=true
            fidx_file="${fa_file}.fidx"
            needs_index=false

            if [[ ! -f "$fidx_file" ]]; then
                needs_index=true
                info "No FASTA index found for $(basename "$fa_file")"
            elif [[ "$fa_file" -nt "$fidx_file" ]]; then
                needs_index=true
                info "FASTA is newer than index for $(basename "$fa_file"), rebuilding..."
            else
                ok "FASTA index up-to-date: $(basename "$fidx_file")"
            fi

            if $needs_index; then
                info "Building FASTA index for $(basename "$fa_file") (this runs once, ~60-120s for a 3 GB genome) ..."
                "$PYTHON" "$FASTA_INDEXER" "$fa_file" \
                    || warn "Failed to build FASTA index for $fa_file — sequence download endpoints will not work"
            fi
        done
    done
    shopt -u nullglob

    if ! $found_fasta; then
        warn "No FASTA files found under $DATA_DIR/*/reference/ — skipping FASTA index step"
    fi
fi

# ─── step 6 : database / ETL ─────────────────────────────────────────────────

log "[6/9] Database & ETL"

if should_reload_db; then
    info "Data change detected (or DB missing) — rebuilding database ..."
    rm -f "$DB_FILE"
    info "Running ETL pipeline ..."
    (cd "$BACKEND_DIR" && "$PYTHON" -m app.services.etl) \
        || warn "ETL returned non-zero — database may be incomplete"
    get_data_hash > "$DATA_HASH_FILE"
    ok "Database ready"
else
    ok "No data changes — using existing database"
fi

# ─── step 7 : frontend dependencies ──────────────────────────────────────────

log "[7/9] Frontend dependencies"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    info "Installing npm packages (first run) ..."
    (cd "$FRONTEND_DIR" && npm install) \
        || die "npm install failed"
    ok "npm packages installed"
else
    ok "node_modules present"
fi

# ─── step 8 : start backend ───────────────────────────────────────────────────

log "[8/9] Starting backend (port 8000)"

(cd "$BACKEND_DIR" && "$PYTHON" -m uvicorn main:app --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!
info "PID $BACKEND_PID"

# Wait briefly and confirm the process is still alive
sleep 2
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    die "Backend failed to start. Check the output above for errors."
fi
ok "Backend running"

# ─── step 9 : start frontend ──────────────────────────────────────────────────

log "[9/9] Starting frontend (port 3000)"

(cd "$FRONTEND_DIR" && npm run dev) &
FRONTEND_PID=$!
info "PID $FRONTEND_PID"

sleep 3
if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null
    die "Frontend failed to start. Check the output above for errors."
fi
ok "Frontend running"

# ─── ready ────────────────────────────────────────────────────────────────────

echo ""
echo "=========================================="
echo "  ApaAtlas is running!"
echo "=========================================="
echo ""
echo "  Backend API : http://localhost:8000"
echo "  Frontend    : http://localhost:3000"
echo "  API docs    : http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

# Save PIDs for the trap
echo "$BACKEND_PID"  > /tmp/apaatlas_backend.pid
echo "$FRONTEND_PID" > /tmp/apaatlas_frontend.pid

cleanup() {
    echo ""
    echo "Stopping servers ..."
    kill "$(cat /tmp/apaatlas_backend.pid 2>/dev/null)"  2>/dev/null || true
    kill "$(cat /tmp/apaatlas_frontend.pid 2>/dev/null)" 2>/dev/null || true
    rm -f /tmp/apaatlas_backend.pid /tmp/apaatlas_frontend.pid
    conda deactivate 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

wait
