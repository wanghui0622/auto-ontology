# StarSea Gaming Data Platform（星海互动游戏数据平台）

面向 NVIDIA Auto-Ontology 的游戏行业自动本体化示范数据库。

本项目**只构建业务数据库与说明文档**，不修改 Auto-Ontology 源码或配置。Auto-Ontology 通过只读连接发现 Schema、外键与 COMMENT，再自动生成本体。

## 当前阶段

**Stage 2：数据库设计（进行中 / 已落地 DDL）**

| 产物 | 路径 |
|---|---|
| Compose | `docker-compose.yml` |
| DDL | `sql/01_create_schemas.sql` … `03_constraints_indexes.sql` |
| 只读授权 | `sql/04_grants_readonly.sql` + Compose 初始化脚本 |
| 接入说明 | `docs/auto-ontology-connection.md` |
| 数据字典 | `docs/data-dictionary.md` |
| Stage 1 模型 | `docs/domain-model.md` 等 |

Stage 3（模拟数据生成）尚未开始。

## 快速启动

```bash
cd starsea-gaming
cp -n .env.example .env
docker compose up -d
# 等待 healthy 后：
docker compose exec starsea-postgres \
  psql -U starsea -d starsea_gaming -c "\dn"
```

默认端口 **5433**，库名 **`starsea_gaming`**。

已有空库时也可：

```bash
./scripts/init_database.sh
./scripts/reset_database.sh   # 危险：DROP SCHEMA CASCADE 后重建
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
