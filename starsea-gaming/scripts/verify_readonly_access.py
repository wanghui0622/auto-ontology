#!/usr/bin/env python3
"""Stage 5: verify Auto-Ontology-ready readonly access to all six schemas."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ("identity", "game", "mall", "payment", "support", "marketing")
SMOKE_TABLES = (
    "identity.players",
    "game.characters",
    "mall.mall_orders",
    "payment.recharge_orders",
    "support.tickets",
    "marketing.campaigns",
)


def connect_readonly() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("STARSEA_PG_HOST", "127.0.0.1"),
        port=int(os.getenv("STARSEA_PG_PORT", "5433")),
        dbname=os.getenv("STARSEA_PG_DB", "starsea_gaming"),
        user=os.getenv("STARSEA_READONLY_USER", "starsea_readonly"),
        password=os.getenv(
            "STARSEA_READONLY_PASSWORD", "starsea_readonly_password"
        ),
    )


def main() -> int:
    errors: list[str] = []
    conn = connect_readonly()
    with conn.cursor() as cur:
        cur.execute("SELECT current_user, current_database()")
        user, db = cur.fetchone()
        print(f"connected as {user}@{db}")

        cur.execute(
            """
            SELECT nspname FROM pg_namespace
            WHERE nspname = ANY(%s)
            ORDER BY 1
            """,
            (list(SCHEMAS),),
        )
        found = [r[0] for r in cur.fetchall()]
        if set(found) != set(SCHEMAS):
            errors.append(f"schemas visible={found}, expected={list(SCHEMAS)}")
        else:
            print(f"OK schemas={found}")

        cur.execute(
            """
            SELECT table_schema, count(*)
            FROM information_schema.tables
            WHERE table_schema = ANY(%s) AND table_type = 'BASE TABLE'
            GROUP BY 1 ORDER BY 1
            """,
            (list(SCHEMAS),),
        )
        counts = dict(cur.fetchall())
        total = sum(counts.values())
        print(f"OK table_counts={counts} total={total}")
        if total != 45:
            errors.append(f"expected 45 tables, got {total}")

        for table in SMOKE_TABLES:
            cur.execute(f"SELECT count(*) FROM {table}")
            n = cur.fetchone()[0]
            print(f"OK SELECT {table} rows={n}")
            if n <= 0:
                errors.append(f"{table} empty")

        # Auto-Ontology postgres connector reads FKs from pg_constraint
        cur.execute(
            """
            SELECT count(*)
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE c.contype = 'f' AND n.nspname = ANY(%s)
            """,
            (list(SCHEMAS),),
        )
        fk_n = cur.fetchone()[0]
        print(f"OK pg_constraint foreign_keys={fk_n}")
        if fk_n < 80:
            errors.append(f"too few FKs visible via pg_constraint: {fk_n}")

        cur.execute(
            """
            SELECT count(*)
            FROM pg_description d
            JOIN pg_class c ON d.objoid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = ANY(%s) AND c.relkind = 'r' AND d.objsubid = 0
            """,
            (list(SCHEMAS),),
        )
        comments = cur.fetchone()[0]
        print(f"OK table_comments={comments}")
        if comments < 45:
            errors.append(f"table comments visible={comments}")

        # writes must fail
        try:
            cur.execute(
                """
                INSERT INTO identity.player_tags(tag_code, tag_name, tag_category)
                VALUES ('stage5_probe', 'probe', 'probe')
                """
            )
            conn.commit()
            errors.append("readonly user was able to INSERT (expected denial)")
        except psycopg.Error as exc:
            conn.rollback()
            print(f"OK write denied: {exc.sqlstate}")

        # privilege inventory: SELECT only
        cur.execute(
            """
            SELECT privilege_type, count(*)
            FROM information_schema.role_table_grants
            WHERE grantee = current_user
              AND table_schema = ANY(%s)
            GROUP BY 1
            """,
            (list(SCHEMAS),),
        )
        privs = dict(cur.fetchall())
        print(f"OK privileges={privs}")
        # SELECT for reads; REFERENCES so information_schema exposes PKs to AO connector
        allowed = {"SELECT", "REFERENCES"}
        if set(privs) - allowed:
            errors.append(f"unexpected privileges: {privs}")
        if privs.get("SELECT", 0) < 45:
            errors.append(f"SELECT grants={privs.get('SELECT')}")
        if privs.get("REFERENCES", 0) < 45:
            errors.append(
                f"REFERENCES grants={privs.get('REFERENCES')} "
                "(needed for PK discovery via information_schema)"
            )

        # PK visibility for Auto-Ontology postgres connector
        cur.execute(
            """
            SELECT count(*)
            FROM information_schema.table_constraints
            WHERE constraint_type = 'PRIMARY KEY'
              AND table_schema = ANY(%s)
            """,
            (list(SCHEMAS),),
        )
        pk_n = cur.fetchone()[0]
        print(f"OK information_schema primary_keys={pk_n}")
        if pk_n < 40:
            errors.append(f"PK constraints visible via information_schema={pk_n}")

    conn.close()

    report = ROOT / "docs" / "stage5-readiness-report.md"
    status = "PASS" if not errors else "FAIL"
    lines = [
        "# Stage 5 只读接入就绪报告",
        "",
        f"- status: **{status}**",
        f"- user: `{os.getenv('STARSEA_READONLY_USER', 'starsea_readonly')}`",
        f"- database: `{os.getenv('STARSEA_PG_DB', 'starsea_gaming')}`",
        f"- host/port: `{os.getenv('STARSEA_PG_HOST', '127.0.0.1')}:{os.getenv('STARSEA_PG_PORT', '5433')}`",
        "",
        "## Checks",
        "",
        "- 六大 Schema 可见",
        "- 45 张业务表可读",
        "- 各域冒烟 SELECT 有数据",
        "- `pg_constraint` 可见跨表外键（Auto-Ontology Postgres 连接器使用该目录）",
        "- 表 COMMENT 可读",
        "- INSERT 被拒绝（只读）",
        "- 表级权限仅为 SELECT",
        "",
    ]
    if errors:
        lines.append("## Failures")
        lines.extend(f"- {e}" for e in errors)
    else:
        lines.append("## Result")
        lines.append(
            "PASS — 可用 `starsea_readonly` 作为 Auto-Ontology 源库连接，"
            "无需修改 Auto-Ontology 代码；请按 `docs/auto-ontology-connection.md` 在 UI 或 "
            "`CONNECTION_STRINGS` 中配置，并选择六个业务 Schema 后启动 ingest。"
        )
    lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {report}")

    if errors:
        print("VERIFY FAILED")
        for e in errors:
            print(" -", e)
        return 1
    print("VERIFY OK")
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
