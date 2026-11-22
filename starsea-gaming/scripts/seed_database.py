#!/usr/bin/env python3
"""Load generated StarSea datasets into PostgreSQL (TRUNCATE + COPY)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import psycopg
from psycopg.types.json import Json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_data import TARGETS, build_dataset, summarize  # noqa: E402

# Insert order respects foreign keys.
TABLE_ORDER: list[tuple[str, list[str]]] = [
    ("identity.registration_sources", [
        "registration_source_id", "source_code", "source_name", "source_type",
        "description", "created_at", "updated_at",
    ]),
    ("marketing.marketing_channels", [
        "marketing_channel_id", "channel_code", "channel_name", "channel_family",
        "status", "created_at", "updated_at",
    ]),
    ("payment.payment_channels", [
        "payment_channel_id", "channel_code", "channel_name", "channel_type",
        "status", "created_at", "updated_at",
    ]),
    ("identity.player_tags", [
        "tag_id", "tag_code", "tag_name", "tag_category", "description",
        "created_at", "updated_at",
    ]),
    ("support.agents", [
        "agent_id", "agent_code", "agent_name", "team_name", "status",
        "created_at", "updated_at",
    ]),
    ("support.ticket_categories", [
        "category_id", "category_code", "category_name", "description",
        "created_at", "updated_at",
    ]),
    ("game.games", [
        "game_id", "game_code", "game_name", "genre", "status", "launched_at",
        "created_at", "updated_at",
    ]),
    ("game.game_servers", [
        "server_id", "game_id", "server_code", "server_name", "region", "status",
        "opened_at", "created_at", "updated_at",
    ]),
    ("game.missions", [
        "mission_id", "game_id", "mission_code", "mission_name", "mission_type",
        "min_level", "description", "created_at", "updated_at",
    ]),
    ("game.game_items", [
        "game_item_id", "game_id", "item_code", "item_name", "item_type", "rarity",
        "description", "created_at", "updated_at",
    ]),
    ("payment.recharge_products", [
        "recharge_product_id", "game_id", "product_code", "product_name",
        "price_amount_cny", "credit_currency_code", "credit_currency_amount",
        "status", "created_at", "updated_at",
    ]),
    ("mall.product_categories", [
        "category_id", "category_code", "category_name", "parent_category_id",
        "created_at", "updated_at",
    ]),
    ("mall.products", [
        "product_id", "category_id", "game_id", "product_code", "product_name",
        "price_currency", "list_price", "status", "description",
        "created_at", "updated_at",
    ]),
    ("mall.product_items", [
        "product_item_id", "product_id", "game_item_id", "quantity",
        "created_at", "updated_at",
    ]),
    ("marketing.campaigns", [
        "campaign_id", "campaign_code", "campaign_name", "game_id", "campaign_type",
        "status", "start_at", "end_at", "description", "created_at", "updated_at",
    ]),
    ("marketing.campaign_channels", [
        "campaign_id", "marketing_channel_id", "placement_note",
        "created_at", "updated_at",
    ]),
    ("marketing.ad_costs", [
        "ad_cost_id", "marketing_channel_id", "campaign_id", "cost_date",
        "cost_amount", "currency_code", "impressions", "clicks",
        "created_at", "updated_at",
    ]),
    ("identity.players", [
        "player_id", "nickname", "register_time", "register_channel",
        "registration_source_id", "country", "status", "player_type", "vip_level",
        "created_at", "updated_at",
    ]),
    ("identity.player_accounts", [
        "account_id", "player_id", "game_id", "account_name", "account_status",
        "created_at", "updated_at",
    ]),
    ("identity.player_devices", [
        "device_record_id", "player_id", "device_id", "device_os", "device_model",
        "first_seen_at", "last_seen_at", "created_at", "updated_at",
    ]),
    ("identity.player_tag_relations", [
        "player_id", "tag_id", "tagged_at", "tagged_by", "created_at", "updated_at",
    ]),
    ("payment.wallets", [
        "wallet_id", "player_id", "currency_code", "balance", "status",
        "created_at", "updated_at",
    ]),
    ("game.characters", [
        "character_id", "player_id", "game_id", "server_id", "character_name",
        "level", "combat_power", "total_play_minutes", "last_login_at", "status",
        "created_at", "updated_at",
    ]),
    ("game.character_attributes", [
        "attribute_id", "character_id", "attribute_key", "attribute_value",
        "effective_at", "created_at", "updated_at",
    ]),
    ("game.player_sessions", [
        "session_id", "player_id", "game_id", "character_id", "login_at",
        "logout_at", "duration_seconds", "client_version", "created_at", "updated_at",
    ]),
    ("game.game_events", [
        "event_id", "player_id", "character_id", "game_id", "event_type",
        "event_name", "event_payload", "event_time", "created_at", "updated_at",
    ]),
    ("game.mission_records", [
        "mission_record_id", "mission_id", "character_id", "status", "started_at",
        "completed_at", "created_at", "updated_at",
    ]),
    ("game.battles", [
        "battle_id", "game_id", "server_id", "battle_type", "result_summary",
        "started_at", "ended_at", "created_at", "updated_at",
    ]),
    ("game.battle_participants", [
        "battle_id", "character_id", "side", "result", "damage_dealt",
        "created_at", "updated_at",
    ]),
    ("payment.recharge_orders", [
        "recharge_order_id", "order_no", "player_id", "game_id", "recharge_product_id",
        "order_amount", "credit_currency_amount", "credit_currency_code", "status",
        "ordered_at", "completed_at", "created_at", "updated_at",
    ]),
    ("payment.payment_transactions", [
        "payment_transaction_id", "recharge_order_id", "payment_channel_id",
        "channel_txn_no", "paid_amount", "currency_code", "status", "paid_at",
        "failure_reason", "created_at", "updated_at",
    ]),
    ("payment.payment_refunds", [
        "payment_refund_id", "recharge_order_id", "payment_transaction_id",
        "refund_amount", "status", "reason_code", "reason_text", "refunded_at",
        "created_at", "updated_at",
    ]),
    ("mall.mall_orders", [
        "mall_order_id", "order_no", "player_id", "character_id", "game_id",
        "price_currency", "payable_amount", "paid_amount", "payment_method",
        "status", "ordered_at", "paid_at", "created_at", "updated_at",
    ]),
    ("mall.mall_order_items", [
        "mall_order_item_id", "mall_order_id", "product_id", "quantity",
        "unit_price", "line_amount", "created_at", "updated_at",
    ]),
    ("mall.mall_refunds", [
        "mall_refund_id", "mall_order_id", "refund_amount", "refund_currency",
        "status", "reason_code", "reason_text", "refunded_at",
        "created_at", "updated_at",
    ]),
    ("mall.item_delivery_records", [
        "delivery_id", "mall_order_id", "mall_order_item_id", "player_id",
        "character_id", "game_item_id", "quantity", "delivery_status",
        "delivered_at", "created_at", "updated_at",
    ]),
    ("marketing.campaign_participations", [
        "participation_id", "campaign_id", "player_id", "character_id", "joined_at",
        "participation_status", "converted_recharge_order_id", "converted_at",
        "created_at", "updated_at",
    ]),
    ("marketing.campaign_rewards", [
        "campaign_reward_id", "participation_id", "player_id", "reward_type",
        "reward_currency_code", "reward_amount", "game_item_id", "item_quantity",
        "grant_status", "granted_at", "created_at", "updated_at",
    ]),
    ("payment.wallet_ledgers", [
        "ledger_id", "wallet_id", "entry_type", "change_amount", "balance_after",
        "recharge_order_id", "mall_order_id", "campaign_reward_id", "remark",
        "occurred_at", "created_at", "updated_at",
    ]),
    ("marketing.player_attributions", [
        "attribution_id", "player_id", "marketing_channel_id", "campaign_id",
        "attribution_type", "attributed_at", "attribution_model",
        "created_at", "updated_at",
    ]),
    ("support.tickets", [
        "ticket_id", "ticket_no", "player_id", "category_id", "character_id",
        "recharge_order_id", "mall_order_id", "campaign_id", "subject", "priority",
        "status", "opened_at", "closed_at", "created_at", "updated_at",
    ]),
    ("support.ticket_messages", [
        "message_id", "ticket_id", "sender_type", "sender_player_id",
        "sender_agent_id", "message_body", "sent_at", "created_at", "updated_at",
    ]),
    ("support.ticket_assignments", [
        "assignment_id", "ticket_id", "agent_id", "assignment_reason",
        "assigned_at", "unassigned_at", "created_at", "updated_at",
    ]),
    ("support.ticket_resolution_records", [
        "resolution_id", "ticket_id", "resolved_by_agent_id", "resolution_code",
        "resolution_summary", "resolved_at", "created_at", "updated_at",
    ]),
    ("support.customer_satisfaction", [
        "csat_id", "ticket_id", "player_id", "score", "comment_text", "rated_at",
        "created_at", "updated_at",
    ]),
]


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("STARSEA_PG_HOST", "127.0.0.1"),
        port=int(os.getenv("STARSEA_PG_PORT", "5433")),
        dbname=os.getenv("STARSEA_PG_DB", "starsea_gaming"),
        user=os.getenv("STARSEA_PG_USER", "starsea"),
        password=os.getenv("STARSEA_PG_PASSWORD", "starsea_dev_password"),
    )


def truncate_all(conn: psycopg.Connection) -> None:
    tables = ", ".join(name for name, _ in reversed(TABLE_ORDER))
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE {tables} CASCADE")
    conn.commit()


def copy_table(conn: psycopg.Connection, table: str, columns: list[str], rows: list[tuple]) -> None:
    if not rows:
        return
    col_list = ", ".join(columns)
    with conn.cursor() as cur:
        with cur.copy(f"COPY {table} ({col_list}) FROM STDIN") as copy:
            for row in rows:
                out = []
                for col, val in zip(columns, row):
                    if col == "event_payload" and isinstance(val, dict):
                        out.append(Json(val))
                    else:
                        out.append(val)
                copy.write_row(out)
    conn.commit()


def main() -> int:
    seed = int(os.getenv("STARSEA_DATA_SEED", "42"))
    print(f"Generating dataset seed={seed} ...")
    t0 = time.time()
    ds = build_dataset(seed=seed)
    print(summarize(ds))
    print(f"generation_seconds={time.time() - t0:.1f}")

    # soft target check
    missing = []
    for key, target in TARGETS.items():
        # map key to table short names used in counts
        actual = ds.counts.get(key)
        if actual is None:
            # aliases
            aliases = {
                "player_attributions": "player_attributions",
                "ticket_messages": "ticket_messages",
                "tickets": "tickets",
            }
            actual = ds.counts.get(aliases.get(key, key), 0)
        if actual < target:
            missing.append(f"{key}: {actual} < {target}")
    if missing:
        print("WARNING: some targets not met:")
        for m in missing:
            print(" -", m)

    print("Connecting and truncating...")
    conn = connect()
    try:
        truncate_all(conn)
        t1 = time.time()
        for table, cols in TABLE_ORDER:
            rows = ds.tables.get(table, [])
            print(f"  loading {table}: {len(rows)}")
            copy_table(conn, table, cols, rows)
        print(f"load_seconds={time.time() - t1:.1f}")
    finally:
        conn.close()
    print("SEED OK")
    return 0


if __name__ == "__main__":
    # load .env if present
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    raise SystemExit(main())
