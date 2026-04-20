#!/bin/bash
# =============================================================================
#  ApaAtlas – one-shot setup & launch script
#
#  Steps performed on every run:
#    1. Locate conda/mamba and create the 'apaatlas' environment if needed
#    2. Activate the environment
#    3. Verify Node.js is available
#    4. Detect data changes; rebuild SQLite DB + run ETL when needed
#    5. Install frontend npm deps if missing
#    6. Start the backend (uvicorn, port 8000)
#    7. Start the frontend (vite dev, port 3000)
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

log "[1/7] Conda environment"

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

log "[2/7] Activating environment"
activate_env

# Resolve python inside the environment (robust even if activate did nothing)
PYTHON="$("$CONDA_EXE" run -n "$ENV_NAME" which python 2>/dev/null \
          || command -v python3 \
          || die "python not found")"
info "Python: $PYTHON ($($PYTHON --version 2>&1))"

# ─── step 3 : node.js ─────────────────────────────────────────────────────────

log "[3/7] Checking Node.js"
if ! command -v node &>/dev/null; then
    die "node not found. Install Node.js (https://nodejs.org) and re-run."
fi
ok "Node $(node --version) / npm $(npm --version)"

# ─── step 4 : database / ETL ─────────────────────────────────────────────────

log "[4/7] Database & ETL"

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

# ─── step 5 : frontend dependencies ──────────────────────────────────────────

log "[5/7] BED12 indices"

_bed12_any_built=0
for _bed in "$DATA_DIR"/*/reference/*.bed; do
    [[ -f "$_bed" ]] || continue
    if [[ ! -f "${_bed}.bidx" ]]; then
        info "Building BED12 index: $(basename "$_bed") ..."
        "$PYTHON" "$BACKEND_DIR/build_bed12_index.py" "$_bed" \
            || warn "Failed to build index for $_bed"
        _bed12_any_built=1
    fi
done
if [[ "$_bed12_any_built" -eq 0 ]]; then
    ok "All BED12 indices present"
else
    ok "BED12 index build complete"
fi

log "[6/8] Frontend dependencies"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    info "Installing npm packages (first run) ..."
    (cd "$FRONTEND_DIR" && npm install) \
        || die "npm install failed"
    ok "npm packages installed"
else
    ok "node_modules present"
fi

# ─── step 6 : start backend ───────────────────────────────────────────────────

log "[7/8] Starting backend (port 8000)"

(cd "$BACKEND_DIR" && "$PYTHON" -m uvicorn main:app --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!
info "PID $BACKEND_PID"

# Wait briefly and confirm the process is still alive
sleep 2
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    die "Backend failed to start. Check the output above for errors."
fi
ok "Backend running"

# ─── step 7 : start frontend ──────────────────────────────────────────────────

log "[8/8] Starting frontend (port 3000)"

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
