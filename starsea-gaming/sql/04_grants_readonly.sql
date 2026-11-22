-- Optional grants for an existing readonly role (non-Docker / re-run safe).
-- Usage:
--   psql ... -v readonly_user=starsea_readonly -f sql/04_grants_readonly.sql

GRANT USAGE ON SCHEMA identity, game, mall, payment, support, marketing TO :"readonly_user";
GRANT SELECT ON ALL TABLES IN SCHEMA identity TO :"readonly_user";
GRANT SELECT ON ALL TABLES IN SCHEMA game TO :"readonly_user";
GRANT SELECT ON ALL TABLES IN SCHEMA mall TO :"readonly_user";
GRANT SELECT ON ALL TABLES IN SCHEMA payment TO :"readonly_user";
GRANT SELECT ON ALL TABLES IN SCHEMA support TO :"readonly_user";
GRANT SELECT ON ALL TABLES IN SCHEMA marketing TO :"readonly_user";
