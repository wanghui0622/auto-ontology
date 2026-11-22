#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a && source .env && set +a
fi
export PGPASSWORD="${STARSEA_PG_PASSWORD:-starsea_dev_password}"
OUT="${1:-/opt/cursor/artifacts/starsea-stage6-analytics.log}"
psql -v ON_ERROR_STOP=1 \
  -h "${STARSEA_PG_HOST:-127.0.0.1}" \
  -p "${STARSEA_PG_PORT:-5433}" \
  -U "${STARSEA_PG_USER:-starsea}" \
  -d "${STARSEA_PG_DB:-starsea_gaming}" \
  -f sql/analytics-workload.sql | tee "$OUT"
echo "wrote $OUT"
