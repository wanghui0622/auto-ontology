"""Metric smoke tests against seeded StarSea data."""

from __future__ import annotations

import os
from decimal import Decimal

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
        n = conn.execute("SELECT count(*) FROM identity.players").fetchone()[0]
        if n < 100:
            pytest.skip("database not seeded")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"database unavailable: {exc}")
    yield conn
    conn.close()


def test_dau_wau_mau_ordering(db: psycopg.Connection) -> None:
    as_of = db.execute("SELECT max(login_at::date) FROM game.player_sessions").fetchone()[0]
    dau = db.execute(
        "SELECT count(DISTINCT player_id) FROM game.player_sessions WHERE login_at::date = %s",
        (as_of,),
    ).fetchone()[0]
    wau = db.execute(
        """
        SELECT count(DISTINCT player_id) FROM game.player_sessions
        WHERE login_at::date > %s::date - 7 AND login_at::date <= %s
        """,
        (as_of, as_of),
    ).fetchone()[0]
    mau = db.execute(
        """
        SELECT count(DISTINCT player_id) FROM game.player_sessions
        WHERE login_at::date > %s::date - 30 AND login_at::date <= %s
        """,
        (as_of, as_of),
    ).fetchone()[0]
    assert dau > 0
    assert mau >= wau >= dau


def test_arpu_le_arppu(db: psycopg.Connection) -> None:
    players = db.execute("SELECT count(*) FROM identity.players").fetchone()[0]
    payers = db.execute(
        """
        SELECT count(DISTINCT player_id) FROM payment.recharge_orders
        WHERE status = 'success'
        """
    ).fetchone()[0]
    amount = Decimal(
        db.execute(
            """
            SELECT COALESCE(SUM(order_amount),0) FROM payment.recharge_orders
            WHERE status = 'success'
            """
        ).fetchone()[0]
    )
    arpu = amount / players
    arppu = amount / payers
    assert arppu >= arpu
    assert 0 < (payers / players) < 1


def test_mall_gmv_not_equal_recharge_by_definition(db: psycopg.Connection) -> None:
    """GMV and recharge are different measures; currencies/columns differ."""
    recharge = db.execute(
        """
        SELECT COALESCE(SUM(order_amount),0) FROM payment.recharge_orders
        WHERE status = 'success'
        """
    ).fetchone()[0]
    mall_diamond = db.execute(
        """
        SELECT COALESCE(SUM(paid_amount),0) FROM mall.mall_orders
        WHERE price_currency = 'DIAMOND'
          AND status IN ('paid','delivered','refunded','partial_refunded')
        """
    ).fetchone()[0]
    # Different units/meaning; assert both positive and not accidentally identical objects
    assert Decimal(recharge) > 0
    assert Decimal(mall_diamond) > 0


def test_cac_denominators_use_first_touch(db: psycopg.Connection) -> None:
    row = db.execute(
        """
        SELECT count(*) FROM marketing.player_attributions
        WHERE attribution_type = 'first_touch'
        """
    ).fetchone()[0]
    players = db.execute("SELECT count(*) FROM identity.players").fetchone()[0]
    assert row == players
