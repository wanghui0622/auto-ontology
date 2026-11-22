#!/usr/bin/env python3
"""Verify Stage 2 schema via psql (no extra Python deps)."""

from __future__ import annotations

import os
import subprocess
import sys


EXPECTED = {
    "identity": 6,
    "game": 11,
    "mall": 7,
    "payment": 7,
    "support": 7,
    "marketing": 7,
}

REQUIRED_PLAYER_FK_TABLES = {
    ("game", "characters"),
    ("game", "player_sessions"),
    ("mall", "mall_orders"),
    ("payment", "recharge_orders"),
    ("support", "tickets"),
    ("marketing", "player_attributions"),
}


def psql_tuples(sql: str) -> list[tuple[str, ...]]:
    env = os.environ.copy()
    env["PGPASSWORD"] = os.getenv("STARSEA_PG_PASSWORD", "starsea_dev_password")
    cmd = [
        "psql",
        "-h",
        os.getenv("STARSEA_PG_HOST", "127.0.0.1"),
        "-p",
        os.getenv("STARSEA_PG_PORT", "5433"),
        "-U",
        os.getenv("STARSEA_PG_USER", "starsea"),
        "-d",
        os.getenv("STARSEA_PG_DB", "starsea_gaming"),
        "-v",
        "ON_ERROR_STOP=1",
        "-At",
        "-F",
        "|",
        "-c",
        sql,
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    return [tuple(ln.split("|")) for ln in lines]


def main() -> int:
    errors: list[str] = []

    counts = {row[0]: int(row[1]) for row in psql_tuples(
        """
        SELECT table_schema, count(*)
        FROM information_schema.tables
        WHERE table_schema IN ('identity','game','mall','payment','support','marketing')
          AND table_type = 'BASE TABLE'
        GROUP BY 1
        """
    )}
    for schema, expected in EXPECTED.items():
        actual = counts.get(schema, 0)
        if actual != expected:
            errors.append(f"{schema}: expected {expected} tables, got {actual}")

    fk_rows = {
        (r[0], r[1])
        for r in psql_tuples(
            """
            SELECT tc.table_schema, tc.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.constraint_schema = tc.constraint_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND ccu.table_schema = 'identity'
              AND ccu.table_name = 'players'
              AND kcu.column_name IN ('player_id')
            """
        )
    }
    for required in REQUIRED_PLAYER_FK_TABLES:
        if required not in fk_rows:
            errors.append(f"missing player FK on {required[0]}.{required[1]}")

    comments = int(
        psql_tuples(
            """
            SELECT count(*)
            FROM pg_catalog.pg_description d
            JOIN pg_catalog.pg_class c ON d.objoid = c.oid
            JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname IN ('identity','game','mall','payment','support','marketing')
              AND c.relkind = 'r'
              AND d.objsubid = 0
            """
        )[0][0]
    )
    if comments < 45:
        errors.append(f"expected >=45 table comments, got {comments}")

    float_money = psql_tuples(
        """
        SELECT table_schema || '.' || table_name || '.' || column_name
        FROM information_schema.columns
        WHERE table_schema IN ('identity','game','mall','payment','support','marketing')
          AND column_name IN (
            'order_amount','paid_amount','payable_amount','balance',
            'refund_amount','cost_amount','list_price','change_amount',
            'credit_currency_amount','price_amount_cny'
          )
          AND data_type <> 'numeric'
        """
    )
    if float_money:
        errors.append(f"non-numeric money columns: {float_money}")

    role = os.getenv("STARSEA_READONLY_USER", "starsea_readonly")
    roles = psql_tuples(f"SELECT 1 FROM pg_roles WHERE rolname = '{role}'")
    if not roles:
        errors.append(f"readonly role missing: {role}")

    if errors:
        print("VERIFY FAILED")
        for e in errors:
            print(f" - {e}")
        return 1

    print("VERIFY OK")
    print(f" tables={sum(EXPECTED.values())} fks_to_players={len(fk_rows)} comments={comments}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or exc.stdout, file=sys.stderr)
        raise SystemExit(2) from exc
