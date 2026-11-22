# StarSea Gaming Data Platform（星海互动游戏数据平台）

面向 NVIDIA Auto-Ontology 的游戏行业自动本体化示范数据库。

本项目**只构建业务数据库与说明文档**，不修改 Auto-Ontology 源码或配置。Auto-Ontology 通过只读连接发现 Schema、外键与 COMMENT，再自动生成本体。

## 当前阶段

**Stage 4：数据质量验证已通过**

| 产物 | 路径 |
|---|---|
| Compose / DDL | `docker-compose.yml`, `sql/01`–`04` |
| 数据生成 / 灌库 | `scripts/generate_data.py`, `scripts/seed_database.py` |
| 质量校验 | `scripts/validate_data.py`（规模/FK/钱包/充值/商城/归因/指标） |
| 质量报告 | `docs/data-quality-report.md` |
| 指标口径 | `docs/metric-definitions.md` |
| SQL 探针 | `sql/quality-checks.sql` |
| 测试 | `tests/test_*.py` |
| 接入说明 | `docs/auto-ontology-connection.md` |

## 快速启动

```bash
cd starsea-gaming
cp -n .env.example .env
docker compose up -d
# 等待 healthy 后初始化结构（首次 compose 已自动执行 DDL）：
python3 -m pip install -r requirements.txt
python3 scripts/seed_database.py
python3 scripts/validate_data.py
```

默认端口 **5433**，库名 **`starsea_gaming`**。数据时间窗口锚定 `2025-11-22`～`2026-11-22` UTC（生成器固定 `NOW`）。

结构重置：

```bash
./scripts/reset_database.sh   # DROP SCHEMA CASCADE 后重建空表
python3 scripts/seed_database.py
```

## 目标数据库

- 引擎：PostgreSQL 17
- Schema：`identity` / `game` / `mall` / `payment` / `support` / `marketing`（45 表）
- 金额：`NUMERIC`；时间：UTC `TIMESTAMPTZ`
- 主键：UUID；跨域枢纽：`identity.players.player_id`

## Auto-Ontology

使用只读账号连接，见 [`docs/auto-ontology-connection.md`](./docs/auto-ontology-connection.md)。

**不要**在 Auto-Ontology 中手工预置 Terms / Relationships / SQL Attributes。

## 原则

1. 不以手工本体预置替代自动发现。
2. 以原生 FK、约束、COMMENT 与后续一致性数据承载语义。
3. 与 Auto-Ontology 主项目隔离：独立 Compose、独立库、独立用户。
