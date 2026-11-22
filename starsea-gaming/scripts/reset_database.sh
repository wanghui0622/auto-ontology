#!/usr/bin/env bash
# Drop and recreate business schemas, then re-apply DDL.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a && source .env && set +a
fi

PGHOST="${STARSEA_PG_HOST:-127.0.0.1}"
PGPORT="${STARSEA_PG_PORT:-5433}"
PGDATABASE="${STARSEA_PG_DB:-starsea_gaming}"
PGUSER="${STARSEA_PG_USER:-starsea}"
export PGPASSWORD="${STARSEA_PG_PASSWORD:-starsea_dev_password}"

echo "Resetting schemas on ${PGHOST}:${PGPORT}/${PGDATABASE}"
psql -v ON_ERROR_STOP=1 -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" <<'SQL'
DROP SCHEMA IF EXISTS identity CASCADE;
DROP SCHEMA IF EXISTS game CASCADE;
DROP SCHEMA IF EXISTS mall CASCADE;
DROP SCHEMA IF EXISTS payment CASCADE;
DROP SCHEMA IF EXISTS support CASCADE;
DROP SCHEMA IF EXISTS marketing CASCADE;
SQL

"$ROOT_DIR/scripts/init_database.sh"
