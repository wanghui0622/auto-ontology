#!/usr/bin/env python3
"""Stage 3/4 data quality checks: scale, FKs, wallet reconciliation, status rules."""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]

MIN_COUNTS = {
    "identity.players": 2000,
    "identity.player_accounts": 2500,
    "game.games": 2,
    "game.game_servers": 10,
    "game.characters": 3000,
    "game.player_sessions": 30000,
    "game.game_events": 50000,
    "game.mission_records": 15000,
    "game.battles": 10000,
    "mall.products": 100,
    "mall.mall_orders": 8000,
    "mall.mall_order_items": 15000,
    "payment.recharge_orders": 6000,
    "payment.payment_transactions": 6000,
    "payment.wallet_ledgers": 20000,
    "support.tickets": 3000,
    "support.ticket_messages": 12000,
    "marketing.campaigns": 30,
    "marketing.ad_costs": 3000,
    "marketing.player_attributions": 2000,
    "marketing.campaign_participations": 8000,
}


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("STARSEA_PG_HOST", "127.0.0.1"),
        port=int(os.getenv("STARSEA_PG_PORT", "5433")),
        dbname=os.getenv("STARSEA_PG_DB", "starsea_gaming"),
        user=os.getenv("STARSEA_PG_USER", "starsea"),
        password=os.getenv("STARSEA_PG_PASSWORD", "starsea_dev_password"),
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    conn = connect()
    with conn.cursor() as cur:
        for table, minimum in MIN_COUNTS.items():
            cur.execute(f"SELECT count(*) FROM {table}")
            n = cur.fetchone()[0]
            if n < minimum:
                errors.append(f"{table}: count {n} < {minimum}")
            else:
                print(f"OK count {table}={n}")

        # wallet reconciliation
        cur.execute(
            """
            SELECT w.wallet_id, w.balance,
                   COALESCE(SUM(l.change_amount), 0) AS ledger_sum
            FROM payment.wallets w
            LEFT JOIN payment.wallet_ledgers l ON l.wallet_id = w.wallet_id
            GROUP BY w.wallet_id, w.balance
            HAVING w.balance <> COALESCE(SUM(l.change_amount), 0)
            LIMIT 20
            """
        )
        bad = cur.fetchall()
        if bad:
            errors.append(f"wallet balance mismatch rows={len(bad)} sample={bad[:3]}")
        else:
            print("OK wallet balances reconcile with ledgers")

        # successful recharge should have success txn
        cur.execute(
            """
            SELECT count(*)
            FROM payment.recharge_orders o
            WHERE o.status IN ('success', 'refunded', 'partial_refunded')
              AND NOT EXISTS (
                SELECT 1 FROM payment.payment_transactions t
                WHERE t.recharge_order_id = o.recharge_order_id
                  AND t.status = 'success'
              )
            """
        )
        n = cur.fetchone()[0]
        if n:
            errors.append(f"successful recharges without success txn: {n}")
        else:
            print("OK successful recharges have success transactions")

        # delivered/paid mall orders should have delivery records when not cancelled
        cur.execute(
            """
            SELECT count(*)
            FROM mall.mall_orders o
            WHERE o.status IN ('paid', 'delivered', 'refunded', 'partial_refunded')
              AND NOT EXISTS (
                SELECT 1 FROM mall.item_delivery_records d
                WHERE d.mall_order_id = o.mall_order_id
              )
            """
        )
        n = cur.fetchone()[0]
        if n:
            warnings.append(f"paid mall orders without delivery rows: {n}")
        else:
            print("OK mall paid/delivered orders have deliveries")

        # first_touch attribution per player
        cur.execute(
            """
            SELECT count(*) FROM identity.players p
            WHERE NOT EXISTS (
              SELECT 1 FROM marketing.player_attributions a
              WHERE a.player_id = p.player_id AND a.attribution_type = 'first_touch'
            )
            """
        )
        n = cur.fetchone()[0]
        if n:
            errors.append(f"players missing first_touch attribution: {n}")
        else:
            print("OK every player has first_touch attribution")

        # ticket messages nonempty semantic-ish (length)
        cur.execute(
            """
            SELECT count(*) FROM support.ticket_messages
            WHERE length(trim(message_body)) < 4
            """
        )
        n = cur.fetchone()[0]
        if n:
            errors.append(f"too-short ticket messages: {n}")
        else:
            print("OK ticket messages have content")

        # no negative wallet balances
        cur.execute("SELECT count(*) FROM payment.wallets WHERE balance < 0")
        n = cur.fetchone()[0]
        if n:
            errors.append(f"negative wallet balances: {n}")
        else:
            print("OK no negative wallet balances")

        # payer long-tail rough check
        cur.execute(
            """
            SELECT player_type, count(*)
            FROM identity.players
            GROUP BY 1 ORDER BY 1
            """
        )
        print("player_type distribution:", cur.fetchall())

        cur.execute(
            """
            SELECT
              COUNT(*) FILTER (WHERE status = 'success') AS success_n,
              COUNT(*) AS total_n
            FROM payment.recharge_orders
            """
        )
        print("recharge status success/total:", cur.fetchone())

    conn.close()

    report = ROOT / "docs" / "data-quality-report.md"
    lines = [
        "# 数据质量报告（Stage 3）",
        "",
        f"- errors: {len(errors)}",
        f"- warnings: {len(warnings)}",
        "",
    ]
    if errors:
        lines.append("## Errors")
        lines.extend(f"- {e}" for e in errors)
        lines.append("")
    if warnings:
        lines.append("## Warnings")
        lines.extend(f"- {w}" for w in warnings)
        lines.append("")
    if not errors:
        lines.append("## Result")
        lines.append("PASS — 规模与核心业务一致性检查通过。")
        lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {report}")

    if errors:
        print("VALIDATE FAILED")
        for e in errors:
            print(" -", e)
        for w in warnings:
            print(" warning:", w)
        return 1
    print("VALIDATE OK")
    for w in warnings:
        print(" warning:", w)
    return 0


if __name__ == "__main__":
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    raise SystemExit(main())
