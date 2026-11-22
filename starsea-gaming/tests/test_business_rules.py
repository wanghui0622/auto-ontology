"""Business-rule checks against a seeded StarSea database."""

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
        conn.execute("SELECT 1")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"database unavailable: {exc}")
    yield conn
    conn.close()


def test_wallet_ledger_reconciles(db: psycopg.Connection) -> None:
    row = db.execute(
        """
        SELECT count(*) FROM (
          SELECT w.wallet_id
          FROM payment.wallets w
          LEFT JOIN payment.wallet_ledgers l ON l.wallet_id = w.wallet_id
          GROUP BY w.wallet_id, w.balance
          HAVING w.balance <> COALESCE(SUM(l.change_amount), 0)
        ) bad
        """
    ).fetchone()
    assert row[0] == 0


def test_player_scale(db: psycopg.Connection) -> None:
    n = db.execute("SELECT count(*) FROM identity.players").fetchone()[0]
    assert n >= 2000


def test_first_touch_coverage(db: psycopg.Connection) -> None:
    missing = db.execute(
        """
        SELECT count(*) FROM identity.players p
        WHERE NOT EXISTS (
          SELECT 1 FROM marketing.player_attributions a
          WHERE a.player_id = p.player_id AND a.attribution_type = 'first_touch'
        )
        """
    ).fetchone()[0]
    assert missing == 0
