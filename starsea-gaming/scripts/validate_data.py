#!/usr/bin/env python3
"""Stage 4 data-quality validation for StarSea Gaming.

Checks scale, PK/FK integrity, nulls, status consistency, wallet math,
recharge/payment alignment, mall delivery, attribution/registration,
and metric smoke calculations. Writes docs/data-quality-report.md.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

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

ORPHAN_CHECKS = [
    (
        "game.characters.player_id",
        """
        SELECT count(*) FROM game.characters c
        LEFT JOIN identity.players p ON p.player_id = c.player_id
        WHERE p.player_id IS NULL
        """,
    ),
    (
        "mall.mall_orders.player_id",
        """
        SELECT count(*) FROM mall.mall_orders o
        LEFT JOIN identity.players p ON p.player_id = o.player_id
        WHERE p.player_id IS NULL
        """,
    ),
    (
        "payment.recharge_orders.player_id",
        """
        SELECT count(*) FROM payment.recharge_orders o
        LEFT JOIN identity.players p ON p.player_id = o.player_id
        WHERE p.player_id IS NULL
        """,
    ),
    (
        "support.tickets.player_id",
        """
        SELECT count(*) FROM support.tickets t
        LEFT JOIN identity.players p ON p.player_id = t.player_id
        WHERE p.player_id IS NULL
        """,
    ),
    (
        "marketing.player_attributions.player_id",
        """
        SELECT count(*) FROM marketing.player_attributions a
        LEFT JOIN identity.players p ON p.player_id = a.player_id
        WHERE p.player_id IS NULL
        """,
    ),
    (
        "payment.wallet_ledgers.wallet_id",
        """
        SELECT count(*) FROM payment.wallet_ledgers l
        LEFT JOIN payment.wallets w ON w.wallet_id = l.wallet_id
        WHERE w.wallet_id IS NULL
        """,
    ),
    (
        "mall.mall_order_items.mall_order_id",
        """
        SELECT count(*) FROM mall.mall_order_items i
        LEFT JOIN mall.mall_orders o ON o.mall_order_id = i.mall_order_id
        WHERE o.mall_order_id IS NULL
        """,
    ),
    (
        "payment.payment_transactions.recharge_order_id",
        """
        SELECT count(*) FROM payment.payment_transactions t
        LEFT JOIN payment.recharge_orders o ON o.recharge_order_id = t.recharge_order_id
        WHERE o.recharge_order_id IS NULL
        """,
    ),
]


@dataclass
class CheckResult:
    name: str
    category: str
    status: str  # PASS / FAIL / WARN
    detail: str
    value: Any = None


@dataclass
class Report:
    generated_at: str
    checks: list[CheckResult] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def errors(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status == "FAIL"]

    @property
    def warnings(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status == "WARN"]


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("STARSEA_PG_HOST", "127.0.0.1"),
        port=int(os.getenv("STARSEA_PG_PORT", "5433")),
        dbname=os.getenv("STARSEA_PG_DB", "starsea_gaming"),
        user=os.getenv("STARSEA_PG_USER", "starsea"),
        password=os.getenv("STARSEA_PG_PASSWORD", "starsea_dev_password"),
    )


def add(report: Report, name: str, category: str, ok: bool, detail: str, value: Any = None, warn: bool = False) -> None:
    if ok:
        status = "PASS"
    elif warn:
        status = "WARN"
    else:
        status = "FAIL"
    report.checks.append(CheckResult(name=name, category=category, status=status, detail=detail, value=value))


def run_validation(conn: psycopg.Connection) -> Report:
    report = Report(generated_at=datetime.now(timezone.utc).isoformat())
    cur = conn.cursor()

    # ---- scale ----
    for table, minimum in MIN_COUNTS.items():
        cur.execute(f"SELECT count(*) FROM {table}")
        n = int(cur.fetchone()[0])
        report.counts[table] = n
        add(
            report,
            f"scale:{table}",
            "scale",
            n >= minimum,
            f"count={n}, minimum={minimum}",
            value=n,
        )

    # ---- PK uniqueness (spot-check major tables) ----
    pk_checks = [
        ("identity.players", "player_id"),
        ("game.characters", "character_id"),
        ("mall.mall_orders", "mall_order_id"),
        ("payment.recharge_orders", "recharge_order_id"),
        ("payment.wallets", "wallet_id"),
        ("payment.wallet_ledgers", "ledger_id"),
        ("support.tickets", "ticket_id"),
        ("marketing.campaigns", "campaign_id"),
        ("marketing.player_attributions", "attribution_id"),
    ]
    for table, pk in pk_checks:
        cur.execute(
            f"""
            SELECT count(*) AS total, count(DISTINCT {pk}) AS distinct_pk
            FROM {table}
            """
        )
        total, distinct_pk = cur.fetchone()
        add(
            report,
            f"pk:{table}.{pk}",
            "primary_key",
            total == distinct_pk,
            f"total={total}, distinct={distinct_pk}",
        )

    # ---- required nulls ----
    null_checks = [
        ("identity.players", "nickname"),
        ("identity.players", "register_time"),
        ("game.characters", "player_id"),
        ("mall.mall_orders", "player_id"),
        ("mall.mall_orders", "payable_amount"),
        ("payment.recharge_orders", "order_amount"),
        ("payment.wallets", "balance"),
        ("payment.wallet_ledgers", "change_amount"),
        ("support.tickets", "player_id"),
        ("support.ticket_messages", "message_body"),
        ("marketing.player_attributions", "attribution_type"),
    ]
    for table, col in null_checks:
        cur.execute(f"SELECT count(*) FROM {table} WHERE {col} IS NULL")
        n = int(cur.fetchone()[0])
        add(report, f"null:{table}.{col}", "nullability", n == 0, f"null_rows={n}")

    # ---- orphan / FK application checks ----
    for name, sql in ORPHAN_CHECKS:
        cur.execute(sql)
        n = int(cur.fetchone()[0])
        add(report, f"fk_orphan:{name}", "foreign_key", n == 0, f"orphans={n}")

    # catalog FK count
    cur.execute(
        """
        SELECT count(*)
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
          AND table_schema IN ('identity','game','mall','payment','support','marketing')
        """
    )
    fk_n = int(cur.fetchone()[0])
    add(report, "fk:catalog_count", "foreign_key", fk_n >= 80, f"fk_constraints={fk_n}", value=fk_n)

    # ---- wallet reconciliation ----
    cur.execute(
        """
        SELECT count(*) FROM (
          SELECT w.wallet_id
          FROM payment.wallets w
          LEFT JOIN payment.wallet_ledgers l ON l.wallet_id = w.wallet_id
          GROUP BY w.wallet_id, w.balance
          HAVING w.balance <> COALESCE(SUM(l.change_amount), 0)
        ) bad
        """
    )
    n = int(cur.fetchone()[0])
    add(report, "wallet:balance_equals_ledger_sum", "wallet", n == 0, f"mismatches={n}")

    cur.execute("SELECT count(*) FROM payment.wallets WHERE balance < 0")
    n = int(cur.fetchone()[0])
    add(report, "wallet:no_negative_balance", "wallet", n == 0, f"negative={n}")

    # ledger balance_after monotonic chain spot-check: last ledger balance_after == wallet.balance
    cur.execute(
        """
        WITH last_ledger AS (
          SELECT DISTINCT ON (wallet_id)
            wallet_id, balance_after
          FROM payment.wallet_ledgers
          ORDER BY wallet_id, occurred_at DESC, created_at DESC, ledger_id DESC
        )
        SELECT count(*)
        FROM payment.wallets w
        JOIN last_ledger l ON l.wallet_id = w.wallet_id
        WHERE w.balance <> l.balance_after
        """
    )
    n = int(cur.fetchone()[0])
    add(report, "wallet:last_ledger_matches_balance", "wallet", n == 0, f"mismatches={n}")

    # ---- recharge / payment consistency ----
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
    n = int(cur.fetchone()[0])
    add(report, "recharge:success_has_success_txn", "recharge", n == 0, f"missing_txn={n}")

    # for success orders, paid_amount should equal order_amount in this dataset
    cur.execute(
        """
        SELECT count(*)
        FROM payment.recharge_orders o
        JOIN payment.payment_transactions t
          ON t.recharge_order_id = o.recharge_order_id AND t.status = 'success'
        WHERE o.status IN ('success', 'refunded')
          AND t.paid_amount <> o.order_amount
        """
    )
    n = int(cur.fetchone()[0])
    add(
        report,
        "recharge:paid_amount_equals_order_amount",
        "recharge",
        n == 0,
        f"mismatches={n} (demo generator sets them equal; promotions may differ later)",
    )

    # successful recharge should have credit ledger
    cur.execute(
        """
        SELECT count(*)
        FROM payment.recharge_orders o
        WHERE o.status = 'success'
          AND NOT EXISTS (
            SELECT 1 FROM payment.wallet_ledgers l
            WHERE l.recharge_order_id = o.recharge_order_id
              AND l.entry_type = 'recharge_credit'
          )
        """
    )
    n = int(cur.fetchone()[0])
    add(report, "recharge:success_has_credit_ledger", "recharge", n == 0, f"missing_ledger={n}")

    # ---- mall delivery consistency ----
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
    n = int(cur.fetchone()[0])
    add(report, "mall:paid_has_delivery", "mall", n == 0, f"missing_delivery={n}")

    # order item line_amount = unit_price * quantity
    cur.execute(
        """
        SELECT count(*)
        FROM mall.mall_order_items
        WHERE line_amount <> unit_price * quantity
        """
    )
    n = int(cur.fetchone()[0])
    add(report, "mall:line_amount_math", "mall", n == 0, f"bad_lines={n}")

    # wallet mall debit exists for diamond paid orders
    cur.execute(
        """
        SELECT count(*)
        FROM mall.mall_orders o
        WHERE o.price_currency = 'DIAMOND'
          AND o.status IN ('paid', 'delivered', 'refunded', 'partial_refunded')
          AND o.paid_amount > 0
          AND NOT EXISTS (
            SELECT 1 FROM payment.wallet_ledgers l
            WHERE l.mall_order_id = o.mall_order_id
              AND l.entry_type = 'mall_debit'
          )
        """
    )
    n = int(cur.fetchone()[0])
    add(report, "mall:diamond_paid_has_wallet_debit", "mall", n == 0, f"missing_debit={n}")

    # ---- attribution / registration ----
    cur.execute(
        """
        SELECT count(*) FROM identity.players p
        WHERE NOT EXISTS (
          SELECT 1 FROM marketing.player_attributions a
          WHERE a.player_id = p.player_id AND a.attribution_type = 'first_touch'
        )
        """
    )
    n = int(cur.fetchone()[0])
    add(report, "attribution:every_player_first_touch", "attribution", n == 0, f"missing={n}")

    # first_touch channel family aligns with registration_sources.source_type via code
    cur.execute(
        """
        SELECT count(*)
        FROM identity.players p
        JOIN identity.registration_sources rs ON rs.registration_source_id = p.registration_source_id
        JOIN marketing.player_attributions a
          ON a.player_id = p.player_id AND a.attribution_type = 'first_touch'
        JOIN marketing.marketing_channels mc ON mc.marketing_channel_id = a.marketing_channel_id
        WHERE rs.source_code <> mc.channel_code
        """
    )
    n = int(cur.fetchone()[0])
    add(report, "attribution:first_touch_matches_registration_source", "attribution", n == 0, f"mismatches={n}")

    cur.execute(
        """
        SELECT attribution_type, count(*)
        FROM marketing.player_attributions
        GROUP BY 1 ORDER BY 1
        """
    )
    attr_dist = {r[0]: int(r[1]) for r in cur.fetchall()}
    add(
        report,
        "attribution:has_three_types",
        "attribution",
        set(attr_dist) >= {"first_touch", "last_touch", "campaign_conversion"},
        f"distribution={attr_dist}",
        value=attr_dist,
    )

    # ---- status consistency ----
    cur.execute(
        """
        SELECT count(*) FROM mall.mall_orders
        WHERE status = 'cancelled' AND paid_amount <> 0
        """
    )
    n = int(cur.fetchone()[0])
    add(report, "status:cancelled_mall_unpaid", "status", n == 0, f"bad_rows={n}")

    cur.execute(
        """
        SELECT count(*) FROM support.tickets
        WHERE status IN ('resolved', 'closed') AND closed_at IS NULL
        """
    )
    n = int(cur.fetchone()[0])
    add(report, "status:closed_tickets_have_closed_at", "status", n == 0, f"bad_rows={n}")

    cur.execute(
        """
        SELECT count(*) FROM game.mission_records
        WHERE status = 'completed' AND completed_at IS NULL
        """
    )
    n = int(cur.fetchone()[0])
    add(report, "status:completed_missions_have_completed_at", "status", n == 0, f"bad_rows={n}")

    cur.execute(
        """
        SELECT count(*) FROM support.ticket_messages
        WHERE length(trim(message_body)) < 4
        """
    )
    n = int(cur.fetchone()[0])
    add(report, "support:message_body_meaningful", "status", n == 0, f"short_messages={n}")

    # ---- metric smoke calculations ----
    metrics = compute_metrics(cur)
    report.metrics = metrics

    add(
        report,
        "metric:dau_positive",
        "metrics",
        metrics["dau_last_day"] > 0,
        f"dau_last_day={metrics['dau_last_day']}",
        value=metrics["dau_last_day"],
    )
    add(
        report,
        "metric:mau_ge_wau_ge_dau",
        "metrics",
        metrics["mau_30d"] >= metrics["wau_7d"] >= metrics["dau_last_day"],
        f"dau={metrics['dau_last_day']}, wau={metrics['wau_7d']}, mau={metrics['mau_30d']}",
    )
    add(
        report,
        "metric:recharge_gmv_distinct_from_mall_gmv",
        "metrics",
        metrics["recharge_success_amount_cny"] != metrics["mall_gmv_diamond"]
        or metrics["mall_gmv_cny"] > 0,
        "recharge CNY revenue and mall GMV use different measures",
        value={
            "recharge_success_amount_cny": metrics["recharge_success_amount_cny"],
            "mall_gmv_cny": metrics["mall_gmv_cny"],
            "mall_gmv_diamond": metrics["mall_gmv_diamond"],
        },
    )
    add(
        report,
        "metric:arpu_le_arppu",
        "metrics",
        Decimal(metrics["arppu"]) >= Decimal(metrics["arpu"]),
        f"arpu={metrics['arpu']}, arppu={metrics['arppu']}",
    )
    add(
        report,
        "metric:pay_rate_in_0_1",
        "metrics",
        0 <= metrics["pay_rate"] <= 1,
        f"pay_rate={metrics['pay_rate']}",
    )
    add(
        report,
        "metric:ticket_resolve_rate_in_0_1",
        "metrics",
        0 <= metrics["ticket_resolve_rate"] <= 1,
        f"ticket_resolve_rate={metrics['ticket_resolve_rate']}",
    )
    # CAC sanity: cost / new players by first_touch channel > 0 for channels with spend
    add(
        report,
        "metric:cac_channels_computed",
        "metrics",
        len(metrics["cac_by_channel"]) > 0,
        f"channels={list(metrics['cac_by_channel'].keys())}",
        value=metrics["cac_by_channel"],
    )

    # payer long-tail
    cur.execute(
        """
        SELECT player_type, count(*)
        FROM identity.players
        GROUP BY 1 ORDER BY 1
        """
    )
    dist = {r[0]: int(r[1]) for r in cur.fetchall()}
    add(
        report,
        "distribution:player_type_long_tail",
        "distribution",
        dist.get("free", 0) > dist.get("whale", 0) and dist.get("whale", 0) > 0,
        f"distribution={dist}",
        value=dist,
    )

    cur.close()
    return report


def compute_metrics(cur: psycopg.Cursor) -> dict[str, Any]:
    # Anchor "today" as max session login date in data for stability
    cur.execute("SELECT max(login_at::date) FROM game.player_sessions")
    as_of = cur.fetchone()[0]

    cur.execute(
        """
        SELECT count(DISTINCT player_id)
        FROM game.player_sessions
        WHERE login_at::date = %s
        """,
        (as_of,),
    )
    dau = int(cur.fetchone()[0])

    cur.execute(
        """
        SELECT count(DISTINCT player_id)
        FROM game.player_sessions
        WHERE login_at::date > %s::date - 7 AND login_at::date <= %s
        """,
        (as_of, as_of),
    )
    wau = int(cur.fetchone()[0])

    cur.execute(
        """
        SELECT count(DISTINCT player_id)
        FROM game.player_sessions
        WHERE login_at::date > %s::date - 30 AND login_at::date <= %s
        """,
        (as_of, as_of),
    )
    mau = int(cur.fetchone()[0])

    cur.execute(
        """
        SELECT COALESCE(SUM(order_amount), 0)
        FROM payment.recharge_orders
        WHERE status IN ('success', 'refunded', 'partial_refunded')
        """
    )
    # Note: refunded still counted in gross success-at-time; net revenue separate
    recharge_gross = Decimal(cur.fetchone()[0])

    cur.execute(
        """
        SELECT COALESCE(SUM(order_amount), 0)
        FROM payment.recharge_orders
        WHERE status = 'success'
        """
    )
    recharge_success = Decimal(cur.fetchone()[0])

    cur.execute(
        """
        SELECT
          COALESCE(SUM(paid_amount) FILTER (WHERE price_currency = 'CNY'
            AND status IN ('paid','delivered','refunded','partial_refunded')), 0),
          COALESCE(SUM(paid_amount) FILTER (WHERE price_currency = 'DIAMOND'
            AND status IN ('paid','delivered','refunded','partial_refunded')), 0)
        FROM mall.mall_orders
        """
    )
    mall_cny, mall_diamond = cur.fetchone()
    mall_cny = Decimal(mall_cny)
    mall_diamond = Decimal(mall_diamond)

    cur.execute("SELECT count(*) FROM identity.players")
    players = int(cur.fetchone()[0])

    cur.execute(
        """
        SELECT count(DISTINCT player_id)
        FROM payment.recharge_orders
        WHERE status = 'success'
        """
    )
    payers = int(cur.fetchone()[0])

    arpu = (recharge_success / players) if players else Decimal(0)
    arppu = (recharge_success / payers) if payers else Decimal(0)
    pay_rate = (payers / players) if players else 0.0

    cur.execute(
        """
        SELECT
          count(*) FILTER (WHERE status IN ('resolved','closed'))::float / NULLIF(count(*),0)
        FROM support.tickets
        """
    )
    ticket_resolve_rate = float(cur.fetchone()[0] or 0)

    cur.execute(
        """
        SELECT
          mc.channel_code,
          COALESCE(SUM(ac.cost_amount), 0) AS cost,
          count(DISTINCT a.player_id) AS new_players
        FROM marketing.marketing_channels mc
        LEFT JOIN marketing.ad_costs ac ON ac.marketing_channel_id = mc.marketing_channel_id
        LEFT JOIN marketing.player_attributions a
          ON a.marketing_channel_id = mc.marketing_channel_id
         AND a.attribution_type = 'first_touch'
        GROUP BY mc.channel_code
        ORDER BY mc.channel_code
        """
    )
    cac = {}
    for code, cost, new_players in cur.fetchall():
        cost_d = Decimal(cost)
        np = int(new_players)
        cac[code] = {
            "cost_cny": str(cost_d),
            "new_players_first_touch": np,
            "cac": str((cost_d / np).quantize(Decimal("0.01")) if np else None),
        }

    cur.execute(
        """
        SELECT
          count(*) FILTER (WHERE status IN ('success','refunded','partial_refunded'))::float
            / NULLIF(count(*),0)
        FROM payment.recharge_orders
        """
    )
    recharge_success_rate = float(cur.fetchone()[0] or 0)

    cur.execute(
        """
        SELECT COALESCE(AVG(duration_seconds), 0)
        FROM game.player_sessions
        WHERE duration_seconds IS NOT NULL
        """
    )
    avg_session = float(cur.fetchone()[0])

    return {
        "as_of_date": str(as_of),
        "dau_last_day": dau,
        "wau_7d": wau,
        "mau_30d": mau,
        "recharge_gross_including_later_refunded_cny": str(recharge_gross),
        "recharge_success_amount_cny": str(recharge_success),
        "mall_gmv_cny": str(mall_cny),
        "mall_gmv_diamond": str(mall_diamond),
        "players": players,
        "payers_success_recharge": payers,
        "arpu": str(arpu.quantize(Decimal("0.01"))),
        "arppu": str(arppu.quantize(Decimal("0.01"))),
        "pay_rate": round(pay_rate, 4),
        "recharge_success_rate": round(recharge_success_rate, 4),
        "ticket_resolve_rate": round(ticket_resolve_rate, 4),
        "avg_session_seconds": round(avg_session, 2),
        "cac_by_channel": cac,
    }


def render_markdown(report: Report) -> str:
    errors = report.errors
    warnings = report.warnings
    lines = [
        "# 数据质量报告（Stage 4）",
        "",
        f"- generated_at (UTC): `{report.generated_at}`",
        f"- checks: {len(report.checks)}",
        f"- PASS: {sum(1 for c in report.checks if c.status == 'PASS')}",
        f"- FAIL: {len(errors)}",
        f"- WARN: {len(warnings)}",
        f"- overall: **{'PASS' if not errors else 'FAIL'}**",
        "",
        "## 1. 数据规模",
        "",
        "| 表 | 行数 | 下限 |",
        "|---|---:|---:|",
    ]
    for table, minimum in MIN_COUNTS.items():
        n = report.counts.get(table, 0)
        lines.append(f"| `{table}` | {n} | {minimum} |")

    lines += ["", "## 2. 检查明细", ""]
    by_cat: dict[str, list[CheckResult]] = {}
    for c in report.checks:
        by_cat.setdefault(c.category, []).append(c)
    for cat in sorted(by_cat):
        lines.append(f"### {cat}")
        lines.append("")
        lines.append("| 检查项 | 状态 | 说明 |")
        lines.append("|---|---|---|")
        for c in by_cat[cat]:
            lines.append(f"| `{c.name}` | {c.status} | {c.detail} |")
        lines.append("")

    lines += ["## 3. 经营指标抽检（口径见下）", ""]
    m = report.metrics
    lines += [
        f"- 统计锚定日 `as_of_date` = `{m.get('as_of_date')}`（取会话最大登录日）",
        f"- DAU = {m.get('dau_last_day')}",
        f"- WAU(7d) = {m.get('wau_7d')}",
        f"- MAU(30d) = {m.get('mau_30d')}",
        f"- 充值成功金额（CNY，`status=success`）= {m.get('recharge_success_amount_cny')}",
        f"- 商城 GMV CNY / DIAMOND = {m.get('mall_gmv_cny')} / {m.get('mall_gmv_diamond')}",
        f"- ARPU / ARPPU = {m.get('arpu')} / {m.get('arppu')}",
        f"- 付费率 = {m.get('pay_rate')}",
        f"- 充值成功率 = {m.get('recharge_success_rate')}",
        f"- 工单解决率 = {m.get('ticket_resolve_rate')}",
        f"- 平均会话时长(秒) = {m.get('avg_session_seconds')}",
        "",
        "### CAC by first_touch channel",
        "",
        "| channel | cost_cny | new_players | CAC |",
        "|---|---:|---:|---:|",
    ]
    for code, row in (m.get("cac_by_channel") or {}).items():
        lines.append(
            f"| `{code}` | {row['cost_cny']} | {row['new_players_first_touch']} | {row['cac']} |"
        )

    lines += [
        "",
        "## 4. 指标口径摘要",
        "",
        "| 指标 | 口径 |",
        "|---|---|",
        "| DAU | `game.player_sessions` 在锚定日去重 `player_id` |",
        "| WAU / MAU | 锚定日前 7 / 30 天去重玩家 |",
        "| 充值成功金额 | `payment.recharge_orders.order_amount` 且 `status='success'`（人民币标价） |",
        "| 商城 GMV | `mall.mall_orders.paid_amount`，按 `price_currency` 分开；不含充值收入 |",
        "| ARPU | 充值成功金额 / 全部玩家 |",
        "| ARPPU | 充值成功金额 / 至少一笔成功充值的玩家 |",
        "| 付费率 | 成功充值玩家数 / 全部玩家 |",
        "| CAC | 渠道广告成本 / 该渠道 `first_touch` 玩家数 |",
        "",
        "## 5. 结论",
        "",
    ]
    if errors:
        lines.append("存在失败项，需修复后重跑 `scripts/validate_data.py`：")
        for e in errors:
            lines.append(f"- `{e.name}`: {e.detail}")
    else:
        lines.append(
            "PASS — 外键/主键/空值、钱包核对、充值与支付、商城发放、归因注册对齐、"
            "状态一致性与核心经营指标抽检均通过。"
        )
    if warnings:
        lines.append("")
        lines.append("警告：")
        for w in warnings:
            lines.append(f"- `{w.name}`: {w.detail}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

    conn = connect()
    try:
        report = run_validation(conn)
    finally:
        conn.close()

    md = render_markdown(report)
    report_path = ROOT / "docs" / "data-quality-report.md"
    report_path.write_text(md, encoding="utf-8")

    json_path = Path("/opt/cursor/artifacts/starsea-stage4-report.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {
                "generated_at": report.generated_at,
                "counts": report.counts,
                "metrics": report.metrics,
                "checks": [asdict(c) for c in report.checks],
                "fail": len(report.errors),
                "warn": len(report.warnings),
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print(md)
    print(f"\nwrote {report_path}")
    print(f"wrote {json_path}")
    if report.errors:
        print("VALIDATE FAILED")
        return 1
    print("VALIDATE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
