# Auto-Ontology 接入说明（Stage 2）

本数据库与 Auto-Ontology **进程/库完全隔离**。请勿修改 Auto-Ontology 仓库内原有 `docker-compose.yml`、`.env` 或 Postgres。

## 1. 启动示范库

```bash
cd starsea-gaming
cp -n .env.example .env
docker compose up -d
docker compose ps
```

默认映射：`127.0.0.1:5433` → 容器 `5432`，避免与 Auto-Ontology 自用 Postgres 抢 5432。

首次启动会自动执行 `sql/01`–`03` 并创建只读用户。

## 2. 连接信息

| 用途 | 用户 | 库 | 端口 |
|---|---|---|---|
| 管理 / 灌数 | `starsea` | `starsea_gaming` | `5433` |
| Auto-Ontology 只读 | `starsea_readonly` | `starsea_gaming` | `5433` |

只读 URL 示例：

```text
postgresql://starsea_readonly:starsea_readonly_password@127.0.0.1:5433/starsea_gaming
```

只读角色已授予六大 Schema 的 `USAGE` + 全表 `SELECT`。

## 3. 在 Auto-Ontology UI 中配置

1. 打开已部署的 Auto-Ontology。
2. 新增 Datasource / Database connection（名称建议：`StarSea Gaming`）。
3. 填写 Host=`127.0.0.1`（或 Docker 网络可达主机名）、Port=`5433`、Database=`starsea_gaming`。
4. 使用 **`starsea_readonly`**，不要用写权限账号做自动本体化扫描。
5. 确认能列出 Schema：`identity`、`game`、`mall`、`payment`、`support`、`marketing`。
6. 启动自动发现 / 编译；**不要手工预置 Terms / Relationships / SQL Attributes**。

若 Auto-Ontology 跑在另一容器网络，将 Host 改为可达地址（例如宿主机网关或 `host.docker.internal`），并保证安全组/防火墙放行 5433。

## 4. 校验 SQL

```sql
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('identity','game','mall','payment','support','marketing')
ORDER BY 1;

SELECT table_schema, count(*) AS table_count
FROM information_schema.tables
WHERE table_schema IN ('identity','game','mall','payment','support','marketing')
  AND table_type = 'BASE TABLE'
GROUP BY 1
ORDER BY 1;
```

期望：6 个 Schema，合计 45 张表。

## 5. 重置

```bash
./scripts/reset_database.sh
# 或销毁卷后重建：
docker compose down -v && docker compose up -d
```
