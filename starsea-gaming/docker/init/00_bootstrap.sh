#!/bin/bash
# Runs once on first Postgres data directory initialization.
set -euo pipefail

echo "[starsea] applying DDL..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -f /sql/01_create_schemas.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -f /sql/02_create_tables.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -f /sql/03_constraints_indexes.sql

READONLY_USER="${STARSEA_READONLY_USER:-starsea_readonly}"
READONLY_PASSWORD="${STARSEA_READONLY_PASSWORD:-starsea_readonly_password}"

echo "[starsea] creating readonly role ${READONLY_USER}..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${READONLY_USER}') THEN
    CREATE ROLE ${READONLY_USER} LOGIN PASSWORD '${READONLY_PASSWORD}';
  END IF;
END
\$\$;

GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${READONLY_USER};
GRANT USAGE ON SCHEMA identity, game, mall, payment, support, marketing TO ${READONLY_USER};
GRANT SELECT ON ALL TABLES IN SCHEMA identity, game, mall, payment, support, marketing TO ${READONLY_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA identity GRANT SELECT ON TABLES TO ${READONLY_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA game GRANT SELECT ON TABLES TO ${READONLY_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA mall GRANT SELECT ON TABLES TO ${READONLY_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA payment GRANT SELECT ON TABLES TO ${READONLY_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA support GRANT SELECT ON TABLES TO ${READONLY_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA marketing GRANT SELECT ON TABLES TO ${READONLY_USER};
SQL

echo "[starsea] schema bootstrap complete."
