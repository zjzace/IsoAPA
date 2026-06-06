#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-apaatlas}"
DEPLOY_DIR="${DEPLOY_DIR:-/home/tflab/ApaAtlas-deploy}"
BACKUP_DIR="${BACKUP_DIR:-/home/tflab/ApaAtlas-deploy-backups}"
BACKEND_IMAGE="${BACKEND_IMAGE:-apaatlas-backend:latest}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-apaatlas-frontend:latest}"
TRAEFIK_NETWORK="${TRAEFIK_NETWORK:-traefik-public}"

usage() {
  cat <<'USAGE'
Usage:
  bash deploy_on_server.sh ApaAtlas-deploy-YYYYMMDD-HHMMSS.tar.gz

Optional environment variables:
  STACK_NAME=apaatlas
  DEPLOY_DIR=/home/tflab/ApaAtlas-deploy
  BACKUP_DIR=/home/tflab/ApaAtlas-deploy-backups
  BACKEND_IMAGE=apaatlas-backend:latest
  FRONTEND_IMAGE=apaatlas-frontend:latest
  TRAEFIK_NETWORK=traefik-public

This script:
  1. Verifies Docker Swarm and the external Traefik network.
  2. Removes the existing ApaAtlas stack if present.
  3. Backs up the previous deployment directory.
  4. Extracts the new deployment bundle into DEPLOY_DIR.
  5. Builds local backend/frontend images.
  6. Deploys the Swarm stack.
USAGE
}

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

BUNDLE="${1:-}"
[[ -n "$BUNDLE" ]] || { usage; exit 1; }
[[ -f "$BUNDLE" ]] || die "Bundle not found: $BUNDLE"

command -v docker >/dev/null 2>&1 || die "docker command not found"
command -v tar >/dev/null 2>&1 || die "tar command not found"

SWARM_STATE="$(docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null || true)"
[[ "$SWARM_STATE" == "active" ]] || die "Docker Swarm is not active. Run: docker swarm init"

if ! docker network inspect "$TRAEFIK_NETWORK" >/dev/null 2>&1; then
  die "Required Docker network '$TRAEFIK_NETWORK' not found"
fi

case "$BUNDLE" in
  *.tar.gz|*.tgz) ;;
  *) die "Expected a .tar.gz or .tgz bundle" ;;
esac

WORK_ROOT="$(mktemp -d /tmp/apaatlas-deploy.XXXXXX)"
cleanup() {
  rm -rf "$WORK_ROOT"
}
trap cleanup EXIT

log "Extracting bundle"
tar -xzf "$BUNDLE" -C "$WORK_ROOT"

EXTRACTED_DIR="$(find "$WORK_ROOT" -mindepth 1 -maxdepth 1 -type d -name 'ApaAtlas-deploy-*' -print -quit)"
[[ -n "$EXTRACTED_DIR" ]] || die "Could not find extracted ApaAtlas-deploy-* directory"

for required in stack.yml backend/Dockerfile backend/apa_atlas.db backend/stats_cache.json frontend/Dockerfile frontend/nginx.conf data; do
  [[ -e "$EXTRACTED_DIR/$required" ]] || die "Extracted bundle missing required path: $required"
done

if docker stack ls --format '{{.Name}}' | grep -Fxq "$STACK_NAME"; then
  log "Removing existing stack: $STACK_NAME"
  docker stack rm "$STACK_NAME"

  log "Waiting for old services to stop"
  for _ in {1..60}; do
    if ! docker service ls --format '{{.Name}}' | grep -Eq "^${STACK_NAME}_"; then
      break
    fi
    sleep 2
  done

  if docker service ls --format '{{.Name}}' | grep -Eq "^${STACK_NAME}_"; then
    die "Timed out waiting for old $STACK_NAME services to stop"
  fi
else
  log "No existing stack named $STACK_NAME"
fi

if [[ -d "$DEPLOY_DIR" ]]; then
  mkdir -p "$BACKUP_DIR"
  BACKUP_PATH="$BACKUP_DIR/$(basename "$DEPLOY_DIR").$(date +%Y%m%d-%H%M%S)"
  log "Moving previous deployment to $BACKUP_PATH"
  mv "$DEPLOY_DIR" "$BACKUP_PATH"
fi

log "Installing new deployment to $DEPLOY_DIR"
mkdir -p "$(dirname "$DEPLOY_DIR")"
mv "$EXTRACTED_DIR" "$DEPLOY_DIR"

cd "$DEPLOY_DIR"

log "Building backend image: $BACKEND_IMAGE"
docker build -t "$BACKEND_IMAGE" ./backend

log "Building frontend image: $FRONTEND_IMAGE"
docker build -t "$FRONTEND_IMAGE" ./frontend

log "Deploying stack: $STACK_NAME"
docker stack deploy -c stack.yml "$STACK_NAME"

log "Current services"
docker stack services "$STACK_NAME"

cat <<EOF

Deployment submitted.

Useful checks:
  docker stack services $STACK_NAME
  docker service logs ${STACK_NAME}_backend --tail 80
  docker service logs ${STACK_NAME}_frontend --tail 80

Site:
  https://apaatlas.sls.cuhk.edu.hk
EOF
