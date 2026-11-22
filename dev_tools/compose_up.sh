#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# One command for the Docker Compose stack.
#
# The only database container is PostgreSQL 17 with pgvector
# (pgvector/pgvector:pg17). Compose creates the database named by
# POSTGRES_DATABASE (auto_ontology in .env.example). Alembic owns the public
# schema, Prisma owns the frontend schema, and pgvector collections are
# created in the vdb schema the first time embeddings are stored.
#
# Wide World Importers is not part of this stack. It is an optional source
# database loaded by a separate seed script. The placeholder CONNECTION_STRINGS
# in .env.example points at credentials that do not exist, so a newly created
# .env leaves that line commented and the UI can start.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if ! docker compose version >/dev/null 2>&1; then
	echo "Docker Compose v2 is required (docker compose version)." >&2
	exit 1
fi

if [ ! -f .env ]; then
	cp .env.example .env
	python3 - <<'PY'
import pathlib
import re
import secrets

path = pathlib.Path(".env")
text = path.read_text()
text = re.sub(
    r"^CONNECTION_STRINGS=",
    "# CONNECTION_STRINGS=",
    text,
    count=1,
    flags=re.M,
)
text = re.sub(
    r"^AUTH_SECRET=myverylongsecret123$",
    "AUTH_SECRET=" + secrets.token_urlsafe(32),
    text,
    count=1,
    flags=re.M,
)
path.write_text(text)
PY
	echo "Created .env from .env.example."
	echo "The placeholder source database was left unset."
	echo "Replace the local passwords in .env before exposing this machine."
fi

if ! docker compose up -d --build; then
	echo "docker compose up failed. Recent service status:" >&2
	docker compose ps >&2 || true
	docker compose logs --tail 80 auto-ontology-migrate frontend-migrate auto-ontology auto-ontology-frontend >&2 || true
	exit 1
fi

echo "Waiting for the UI at http://127.0.0.1:3000/login"
ready=0
for _ in $(seq 1 120); do
	if curl -sf -o /dev/null http://127.0.0.1:3000/login; then
		ready=1
		break
	fi
	sleep 5
done

if [ "$ready" != 1 ]; then
	echo "The UI did not become ready. Recent service status:" >&2
	docker compose ps >&2 || true
	docker compose logs --tail 60 auto-ontology auto-ontology-frontend auto-ontology-migrate frontend-migrate >&2 || true
	exit 1
fi

echo "Auto Ontology is up."
echo "  UI:       http://localhost:3000"
echo "  API:      http://localhost:3001"
echo "  Postgres: pgvector/pgvector:pg17, database name from POSTGRES_DATABASE in .env"
echo "Sign in with AUTO_ONTOLOGY_ADMIN_EMAIL and AUTO_ONTOLOGY_ADMIN_PASSWORD from .env."
