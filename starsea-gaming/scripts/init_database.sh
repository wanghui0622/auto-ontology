#!/usr/bin/env bash
# Apply DDL to an already-running StarSea Postgres (idempotent only on empty DB).
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

echo "Applying schemas to ${PGUSER}@${PGHOST}:${PGPORT}/${PGDATABASE}"
psql -v ON_ERROR_STOP=1 -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
  -f sql/01_create_schemas.sql
psql -v ON_ERROR_STOP=1 -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
  -f sql/02_create_tables.sql
psql -v ON_ERROR_STOP=1 -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
  -f sql/03_constraints_indexes.sql

READONLY_USER="${STARSEA_READONLY_USER:-starsea_readonly}"
READONLY_PASSWORD="${STARSEA_READONLY_PASSWORD:-starsea_readonly_password}"

psql -v ON_ERROR_STOP=1 -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${READONLY_USER}') THEN
    CREATE ROLE ${READONLY_USER} LOGIN PASSWORD '${READONLY_PASSWORD}';
  END IF;
END
\$\$;
GRANT CONNECT ON DATABASE ${PGDATABASE} TO ${READONLY_USER};
SQL

psql -v ON_ERROR_STOP=1 -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
  -v readonly_user="$READONLY_USER" \
  -f sql/04_grants_readonly.sql

echo "Done."
