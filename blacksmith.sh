#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKER_DIR="$ROOT/worker"
PAGES_DIR="$ROOT/pages"
CHANNEL="${1:-check}"
RELEASE_ID="${RELEASE_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"

die(){ printf 'blacksmith: %s\n' "$*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"; }
health(){
  local url="$1" tries="${2:-12}"
  [[ "$url" == https://* ]] || die "health URL must use HTTPS"
  for ((i=1;i<=tries;i++)); do
    if curl --fail --silent --show-error --max-time 10 "$url" >/dev/null; then return 0; fi
    sleep 5
  done
  return 1
}
checksum(){
  local out="$ROOT/release-records/$RELEASE_ID"
  mkdir -p "$out"
  (cd "$ROOT" && find worker pages mockingbird -type f -print0 | sort -z | xargs -0 sha256sum) > "$out/SHA256SUMS"
  printf '%s\n' "$RELEASE_ID" > "$out/RELEASE_ID"
  printf 'Release manifest: %s\n' "$out"
}
check(){
  need node; need npm; need npx; need shellcheck
  bash -n "$ROOT/blacksmith.sh"
  shellcheck "$ROOT/blacksmith.sh"
  (cd "$WORKER_DIR" && npm install && npm run typecheck)
  test -s "$PAGES_DIR/index.html"
  test -s "$ROOT/mockingbird/src/main/kotlin/eria/mockingbird/Mockingbird.kt"
  checksum
  printf 'Checks passed. No deployment performed.\n'
}
deploy_worker(){
  local env="$1" health_url="$2"
  need npx
  [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]] || die "CLOUDFLARE_API_TOKEN must be supplied through secret storage"
  if [[ -n "$env" ]]; then
    (cd "$WORKER_DIR" && npx wrangler deploy --env "$env")
  else
    (cd "$WORKER_DIR" && npx wrangler deploy)
  fi
  [[ -n "$health_url" ]] || die "set the Worker health URL to verify deployment"
  health "$health_url" || die "Worker health check failed; production promotion halted"
}
deploy_pages(){
  local project="$1" branch="$2"
  need npx
  [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]] || die "CLOUDFLARE_API_TOKEN must be supplied through secret storage"
  [[ -n "$project" ]] || die "set CLOUDFLARE_PAGES_PROJECT"
  npx wrangler pages deploy "$PAGES_DIR" --project-name "$project" --branch "$branch"
}
case "$CHANNEL" in
  check) check ;;
  worker-staging) check; deploy_worker "" "${WORKER_STAGING_HEALTH_URL:-}" ;;
  worker-production)
    [[ "${PROMOTE_PRODUCTION:-}" == "YES" ]] || die "set PROMOTE_PRODUCTION=YES after staging validation"
    check; deploy_worker production "${WORKER_PRODUCTION_HEALTH_URL:-}" ;;
  pages-preview) check; deploy_pages "${CLOUDFLARE_PAGES_PROJECT:-}" "${PAGES_PREVIEW_BRANCH:-preview}" ;;
  pages-production)
    [[ "${PROMOTE_PRODUCTION:-}" == "YES" ]] || die "set PROMOTE_PRODUCTION=YES after preview validation"
    check; deploy_pages "${CLOUDFLARE_PAGES_PROJECT:-}" main ;;
  *) die "usage: ./blacksmith.sh {check|worker-staging|worker-production|pages-preview|pages-production}" ;;
esac
