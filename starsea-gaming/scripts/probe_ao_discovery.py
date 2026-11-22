#!/usr/bin/env python3
"""Stage 6: probe what Auto-Ontology's Postgres connector can discover.

Uses the Auto-Ontology connector library read-only against StarSea.
Does not write to the Auto-Ontology catalog database.

Prefer: ``uv run python starsea-gaming/scripts/probe_ao_discovery.py``
from the repo root (needs Auto-Ontology deps such as pandas).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

try:
    from auto_ontology.connectors.registry import create_connector
except ModuleNotFoundError as exc:  # pragma: no cover - env hint
    print(
        "Missing Auto-Ontology deps (e.g. pandas). "
        "Run from repo root: uv run python starsea-gaming/scripts/probe_ao_discovery.py",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc

BIZ = ("identity", "game", "mall", "payment", "support", "marketing")
CORE = [
    ("identity", "players"),
    ("game", "games"),
    ("game", "characters"),
    ("mall", "mall_orders"),
    ("payment", "recharge_orders"),
    ("payment", "wallets"),
    ("payment", "wallet_ledgers"),
    ("support", "tickets"),
    ("marketing", "campaigns"),
    ("marketing", "player_attributions"),
    ("mall", "mall_refunds"),
    ("payment", "payment_refunds"),
]
BRIDGES = [
    ("identity", "player_tag_relations"),
    ("game", "battle_participants"),
    ("mall", "product_items"),
    ("marketing", "campaign_channels"),
    ("support", "ticket_assignments"),
]


def main() -> int:
    cs = os.getenv(
        "STARSEA_READONLY_URL",
        "postgresql://{user}:{password}@{host}:{port}/{db}".format(
            user=os.getenv("STARSEA_READONLY_USER", "starsea_readonly"),
            password=os.getenv(
                "STARSEA_READONLY_PASSWORD", "starsea_readonly_password"
            ),
            host=os.getenv("STARSEA_PG_HOST", "127.0.0.1"),
            port=os.getenv("STARSEA_PG_PORT", "5433"),
            db=os.getenv("STARSEA_PG_DB", "starsea_gaming"),
        ),
    )
    c = create_connector(cs)
    try:
        c.ping()
        tables = c.get_tables()
        bt = tables[tables["table_schema"].isin(BIZ)]
        cols = c.get_columns()
        bc = cols[cols["table_schema"].isin(BIZ)]
        pks = c.get_pks()
        bp = pks[pks["table_schema"].isin(BIZ)] if len(pks) else pks
        fks = c.get_fks()
        bf = fks[fks["table_schema"].isin(BIZ)] if len(fks) else fks
        hub = (
            bf[
                (bf["referenced_schema"] == "identity")
                & (bf["referenced_table"] == "players")
            ]
            if len(bf)
            else bf
        )
        result = {
            "database_name": c.database_name,
            "dialect": getattr(c, "dialect", None),
            "business_table_count": int(len(bt)),
            "tables_by_schema": {
                k: int(v) for k, v in bt.groupby("table_schema").size().items()
            },
            "business_column_count": int(len(bc)),
            "pk_rows": int(len(bp)),
            "fk_rows": int(len(bf)),
            "cross_schema_fk_rows": int(
                len(bf[bf["table_schema"] != bf["referenced_schema"]]) if len(bf) else 0
            ),
            "core_entities_present": {
                f"{s}.{t}": bool(
                    len(bt[(bt.table_schema == s) & (bt.table_name == t)])
                )
                for s, t in CORE
            },
            "bridges_present": {
                f"{s}.{t}": bool(
                    len(bt[(bt.table_schema == s) & (bt.table_name == t)])
                )
                for s, t in BRIDGES
            },
            "fks_to_players": hub[
                ["table_schema", "table_name", "column_name"]
            ]
            .drop_duplicates()
            .sort_values(["table_schema", "table_name"])
            .to_dict(orient="records")
            if len(hub)
            else [],
            "checks": {
                "player_hub_cross_domain": len(hub) >= 6,
                "all_core_entities": all(
                    len(bt[(bt.table_schema == s) & (bt.table_name == t)]) > 0
                    for s, t in CORE
                ),
                "bridges_found": all(
                    len(bt[(bt.table_schema == s) & (bt.table_name == t)]) > 0
                    for s, t in BRIDGES
                ),
                "money_columns_distinct": len(
                    bc[
                        bc["column_name"].isin(
                            [
                                "order_amount",
                                "paid_amount",
                                "payable_amount",
                                "balance",
                                "change_amount",
                                "refund_amount",
                                "entry_type",
                                "attribution_type",
                            ]
                        )
                    ]
                )
                >= 8,
                "pk_discovered": len(bp) >= 40,
                "fk_discovered": len(bf) >= 80,
            },
        }
    finally:
        c.close()

    out_json = Path("/opt/cursor/artifacts/starsea-stage6-discovery-signals.json")
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    doc = ROOT / "docs" / "stage6-discovery-probe.json"
    doc.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["checks"], ensure_ascii=False, indent=2))
    print(f"wrote {out_json}")
    print(f"wrote {doc}")
    failed = [k for k, v in result["checks"].items() if not v]
    if failed:
        print("PROBE FAILED", failed)
        return 1
    print("PROBE OK")
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
