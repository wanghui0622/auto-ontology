"""Orphan-key smoke checks (application-level) for seeded data."""

from __future__ import annotations

import os

import psycopg
import pytest


def _conn() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("STARSEA_PG_HOST", "127.0.0.1"),
        port=int(os.getenv("STARSEA_PG_PORT", "5433")),
        dbname=os.getenv("STARSEA_PG_DB", "starsea_gaming"),
        user=os.getenv("STARSEA_PG_USER", "starsea"),
        password=os.getenv("STARSEA_PG_PASSWORD", "starsea_dev_password"),
    )


@pytest.fixture(scope="module")
def db():
    try:
        conn = _conn()
        conn.execute("SELECT 1 FROM identity.players LIMIT 1")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"database unavailable: {exc}")
    yield conn
    conn.close()


def test_characters_reference_players(db: psycopg.Connection) -> None:
    n = db.execute(
        """
        SELECT count(*) FROM game.characters c
        LEFT JOIN identity.players p ON p.player_id = c.player_id
        WHERE p.player_id IS NULL
        """
    ).fetchone()[0]
    assert n == 0


def test_recharge_orders_reference_players(db: psycopg.Connection) -> None:
    n = db.execute(
        """
        SELECT count(*) FROM payment.recharge_orders o
        LEFT JOIN identity.players p ON p.player_id = o.player_id
        WHERE p.player_id IS NULL
        """
    ).fetchone()[0]
    assert n == 0
