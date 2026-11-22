# Stage 5 只读接入就绪报告

- status: **PASS**
- user: `starsea_readonly`
- database: `starsea_gaming`
- host/port: `127.0.0.1:5433`

## Checks

- 六大 Schema 可见
- 45 张业务表可读
- 各域冒烟 SELECT 有数据
- `pg_constraint` 可见跨表外键（Auto-Ontology Postgres 连接器使用该目录）
- 表 COMMENT 可读
- INSERT 被拒绝（只读）
- 表级权限仅为 SELECT

## Result
PASS — 可用 `starsea_readonly` 作为 Auto-Ontology 源库连接，无需修改 Auto-Ontology 代码；请按 `docs/auto-ontology-connection.md` 在 UI 或 `CONNECTION_STRINGS` 中配置，并选择六个业务 Schema 后启动 ingest。
