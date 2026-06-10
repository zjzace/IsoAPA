#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/deploy/package_for_server.sh [--host user@server] [--remote-dir /home/tflab] [--out-dir deploy_packages] [--dry-run]

What it does:
  1. Creates a clean Docker Swarm deployment bundle from the current project.
  2. Includes stack.yml, Docker build files, backend/frontend source, isoapa.db, stats_cache.json, and data/*.bed/*.bed.bidx.
  3. Excludes raw data tables (*.txt, *.tsv), node_modules, dist, caches, .git, and local runtime junk.
  4. Includes a server deploy helper that removes current/legacy stacks before redeploying.
  5. Optionally copies the tarball to a target server with rsync.

Examples:
  scripts/deploy/package_for_server.sh
  scripts/deploy/package_for_server.sh --dry-run
  scripts/deploy/package_for_server.sh --host tflab@server --remote-dir /home/tflab
USAGE
}

HOST=""
REMOTE_DIR=""
OUT_DIR="deploy_packages"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_NAME="IsoAPA"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST="${2:-}"; shift 2 ;;
    --remote-dir)
      REMOTE_DIR="${2:-}"; shift 2 ;;
    --out-dir)
      OUT_DIR="${2:-}"; shift 2 ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1 ;;
  esac
done

cd "$PROJECT_ROOT"

required_files=(
  "stack.yml"
  "backend/Dockerfile"
  "backend/.dockerignore"
  "backend/environment.yml"
  "backend/main.py"
  "backend/isoapa.db"
  "backend/stats_cache.json"
  "frontend/Dockerfile"
  "frontend/.dockerignore"
  "frontend/package.json"
  "frontend/package-lock.json"
  "frontend/vite.config.js"
  "frontend/nginx.conf"
  "scripts/deploy/deploy_on_server.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing required file: $file" >&2
    exit 1
  fi
done

first_bed="$(find data -mindepth 2 -maxdepth 2 -type f -name "*.bed" -print -quit)"
if [[ -z "$first_bed" ]]; then
  echo "No data/<species>/*.bed files found" >&2
  exit 1
fi

first_bidx="$(find data -mindepth 2 -maxdepth 2 -type f -name "*.bed.bidx" -print -quit)"
if [[ -z "$first_bidx" ]]; then
  echo "No data/<species>/*.bed.bidx files found" >&2
  exit 1
fi

bed_count="$(find data -mindepth 2 -maxdepth 2 -type f -name "*.bed" | wc -l | tr -d ' ')"
bidx_count="$(find data -mindepth 2 -maxdepth 2 -type f -name "*.bed.bidx" | wc -l | tr -d ' ')"
raw_count="$(find data -type f \( -name "*.txt" -o -name "*.tsv" \) | wc -l | tr -d ' ')"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run: deployment bundle can be created."
  echo "Project root: $PROJECT_ROOT"
  echo "Output dir: $OUT_DIR"
  echo "Required database: $(du -h backend/isoapa.db | awk '{print $1}') backend/isoapa.db"
  echo "Stats cache: $(du -h backend/stats_cache.json | awk '{print $1}') backend/stats_cache.json"
  echo "BED files included: $bed_count"
  echo "BED index files included: $bidx_count"
  echo "Raw .txt/.tsv files excluded: $raw_count"
  echo "Estimated runtime data size: $(du -ch backend/isoapa.db backend/stats_cache.json $(find data -mindepth 2 -maxdepth 2 -type f \( -name "*.bed" -o -name "*.bed.bidx" \)) | tail -1 | awk '{print $1}')"
  exit 0
fi

mkdir -p "$OUT_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
BUNDLE_DIR="$OUT_DIR/${PROJECT_NAME}-deploy-$STAMP"
TARBALL="$OUT_DIR/${PROJECT_NAME}-deploy-$STAMP.tar.gz"
MANIFEST="$BUNDLE_DIR/DEPLOY_MANIFEST.txt"
SERVER_DEPLOY_SCRIPT="$OUT_DIR/deploy_on_server.sh"

rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"
cp -a scripts/deploy/deploy_on_server.sh "$SERVER_DEPLOY_SCRIPT"
chmod +x "$SERVER_DEPLOY_SCRIPT"

copy_path() {
  local src="$1"
  local dst="$BUNDLE_DIR/$src"
  mkdir -p "$(dirname "$dst")"
  cp -a "$src" "$dst"
}

# Root-level deployment files.
for path in \
  stack.yml \
  README.md \
  .env.example; do
  [[ -e "$path" ]] && copy_path "$path"
done
cp -a scripts/deploy/deploy_on_server.sh "$BUNDLE_DIR/deploy_on_server.sh"

# Backend files needed to build and run the image.
copy_path backend/Dockerfile
copy_path backend/.dockerignore
copy_path backend/environment.yml
copy_path backend/main.py
copy_path backend/isoapa.db
copy_path backend/stats_cache.json
mkdir -p "$BUNDLE_DIR/backend/app"
rsync -a \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  backend/app/ "$BUNDLE_DIR/backend/app/"

# Frontend files needed to build the static image.
for path in \
  frontend/Dockerfile \
  frontend/.dockerignore \
  frontend/package.json \
  frontend/package-lock.json \
  frontend/index.html \
  frontend/vite.config.js \
  frontend/nginx.conf; do
  copy_path "$path"
done
mkdir -p "$BUNDLE_DIR/frontend/src" "$BUNDLE_DIR/frontend/public"
rsync -a \
  --exclude 'node_modules/' \
  --exclude 'dist/' \
  frontend/src/ "$BUNDLE_DIR/frontend/src/"
rsync -a frontend/public/ "$BUNDLE_DIR/frontend/public/"

# Runtime genome browser references only: BED and byte-offset index files.
while IFS= read -r -d '' file; do
  copy_path "$file"
done < <(find data -mindepth 2 -maxdepth 2 -type f \( -name "*.bed" -o -name "*.bed.bidx" \) -print0 | sort -z)

{
  echo "IsoAPA deployment bundle"
  echo "Created: $(date -Is)"
  echo "Source: $PROJECT_ROOT"
  echo
  echo "Included:"
  echo "- Docker Swarm stack.yml and Dockerfiles"
  echo "- Backend source and mamba environment.yml"
  echo "- Frontend source and package-lock.json"
  echo "- backend/isoapa.db"
  echo "- backend/stats_cache.json"
  echo "- data/<species>/*.bed and *.bed.bidx only"
  echo "- deploy_on_server.sh server-side deployment helper"
  echo "- Migration-safe cleanup for current and legacy Swarm stack/deploy names"
  echo
  echo "Excluded intentionally:"
  echo "- .git"
  echo "- frontend/node_modules and frontend/dist"
  echo "- Python caches"
  echo "- raw data tables (*.txt, *.tsv)"
  echo
  echo "Deploy on server:"
  echo "  bash deploy_on_server.sh $(basename "$TARBALL")"
  echo
  echo "Traefik should route: https://isoapa.sls.cuhk.edu.hk"
  echo
  echo "File count: $(find "$BUNDLE_DIR" -type f | wc -l)"
  echo "Bundle size before compression: $(du -sh "$BUNDLE_DIR" | awk '{print $1}')"
} > "$MANIFEST"

tar -czf "$TARBALL" -C "$OUT_DIR" "$(basename "$BUNDLE_DIR")"

echo "Created bundle: $TARBALL"
echo "Bundle size: $(du -sh "$TARBALL" | awk '{print $1}')"
echo "Manifest: $MANIFEST"

if [[ -n "$HOST" ]]; then
  if [[ -z "$REMOTE_DIR" ]]; then
    echo "--remote-dir is required when --host is provided" >&2
    exit 1
  fi
  echo "Copying bundle to $HOST:$REMOTE_DIR/"
  ssh "$HOST" "mkdir -p '$REMOTE_DIR'"
  rsync -av --progress "$TARBALL" "$HOST:$REMOTE_DIR/"
  echo "Copied. On server run:"
  echo "  cd '$REMOTE_DIR'"
  echo "  bash deploy_on_server.sh '$(basename "$TARBALL")'"
fi
