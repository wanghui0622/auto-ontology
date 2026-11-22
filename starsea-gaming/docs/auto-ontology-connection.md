# Auto-Ontology 接入说明（Stage 5）

本示范库与 Auto-Ontology **进程、配置、目录库完全隔离**。  
**不要**修改 Auto-Ontology 仓库内的 `docker-compose.yml`、根目录 `.env`、Helm values 或 catalog Postgres。

目标：让已部署的 Auto-Ontology 以**只读**方式连接 `starsea_gaming`，自动发现六大业务 Schema 的表、外键与 COMMENT，再进行 ingest / 编译。**不要手工预置 Terms、Relationships 或 SQL Attributes。**

## 1. 启动示范库

```bash
cd starsea-gaming
cp -n .env.example .env
docker compose up -d
python3 -m pip install -r requirements.txt
python3 scripts/seed_database.py          # 若尚未灌数
python3 scripts/verify_readonly_access.py # Stage 5 就绪检查
```

默认映射：`127.0.0.1:5433` → 容器 `5432`，避免与 Auto-Ontology 自用 Postgres（常见 `5432`）冲突。

## 2. 连接参数

| 字段 | 值 |
|---|---|
| type | `postgresql` |
| host | `127.0.0.1`（容器网络见下文） |
| port | `5433` |
| database | `starsea_gaming` |
| user | `starsea_readonly` |
| password | `starsea_readonly_password`（见 `.env`） |
| schemas（建议显式勾选） | `identity`, `game`, `mall`, `payment`, `support`, `marketing` |

只读 URL：

```text
postgresql://starsea_readonly:starsea_readonly_password@127.0.0.1:5433/starsea_gaming
```

管理/灌数账号 `starsea` **不要**交给 Auto-Ontology。

示例文件：

- UI / API 请求体：[`config/auto-ontology-connection.example.json`](../config/auto-ontology-connection.example.json)
- 可选 env：[`config/connection-strings.example.env`](../config/connection-strings.example.env)

## 3. 推荐：在 Auto-Ontology UI 中接入

依据项目文档 [`docs/connections.md`](../../docs/connections.md)：

1. 使用管理员账号登录 Auto-Ontology（需 `connection:manage`）。
2. 打开 **Settings → Connections**。
3. 新增 PostgreSQL 连接，填写上表参数。
4. 先 **Test connection**，确认返回的 schema 列表包含六个业务 Schema。
5. 在 schema 选择器中勾选：`identity` / `game` / `mall` / `payment` / `support` / `marketing`  
   （也可留空表示全部；显式勾选可避免扫到无关 schema）。
6. 保存连接。
7. 触发 **Ingest / 编译**（按你环境的 UI 或 ingestion service）。
8. 在 Datasources 中确认 45 张表与外键被抽取。

### API 等价流程（可选）

```bash
# 1) 测试并列出 schemas
curl -sS -X POST "$APP_URL/api/connections/test" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @starsea-gaming/config/auto-ontology-connection.example.json

# 2) 创建连接（需管理员权限）
curl -sS -X POST "$APP_URL/api/connections" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @starsea-gaming/config/auto-ontology-connection.example.json
```

`$APP_URL` / `$TOKEN` 来自你已部署的 Auto-Ontology，本仓库不代填。

## 4. 可选：`CONNECTION_STRINGS`

仅当你**故意**用环境变量管理源库时使用。注意 Auto-Ontology 行为：

| 场景 | 行为 |
|---|---|
| 已有 UI 连接 | 问答优先用 UI 连接 |
| 设置了 `CONNECTION_STRINGS` | **Ingestion 优先用 env**，忽略 UI 源库 |
| 建议 | 示范场景优先只用 UI 连接，避免与 catalog 的其它源串线 |

若必须用 env：复制 `config/connection-strings.example.env` 中的一行到**你自己的**部署 `.env` / Helm `connectionStrings`，**不要**提交密钥到 git，也**不要**覆盖 Auto-Ontology 目录库连接。

## 5. 网络拓扑

| Auto-Ontology 运行位置 | Host 填写 |
|---|---|
| 本机进程 | `127.0.0.1` |
| Docker Compose（同机） | `host.docker.internal`（Linux 常需 `extra_hosts: host.docker.internal:host-gateway`） |
| 另一台机器 / K8s | 示范库可达的主机名或 NodePort/LB；放行 TCP `5433` |

健康检查：

```bash
pg_isready -h 127.0.0.1 -p 5433 -U starsea_readonly -d starsea_gaming
python3 scripts/verify_readonly_access.py
```

## 6. 只读权限与自动发现预期

已验证（见 `docs/stage5-readiness-report.md`）：

- 六 Schema、45 表 `SELECT`
- 表 COMMENT 可读
- 跨 Schema 外键可通过 `pg_constraint` 读取（Auto-Ontology Postgres 连接器**不用**会隐藏约束的 `information_schema.table_constraints`）
- `INSERT`/`UPDATE`/`DELETE` 被拒绝

自动本体化应能看到的结构信号（人工不预置）：

- 统一 `player_id` 枢纽与跨域 FK
- 商城 / 充值 / 钱包金额字段 COMMENT 区分
- 归因表 `attribution_type`（first_touch / last_touch / campaign_conversion）
- 桥接表：标签、战斗参与、商品道具、活动渠道

## 7. 明确不要做的事

1. 修改 Auto-Ontology 源码、根 compose、根 `.env`、目录库数据。  
2. 用写账号接入自动发现。  
3. 在发现前手工创建 Terms / Relationships / SQL Attributes。  
4. 把示范库端口改成与 Auto-Ontology catalog 冲突的 `5432`（除非你很清楚在做什么）。  
5. 同时混用 UI 连接与 `CONNECTION_STRINGS` 指向不同源却期望同一 ingest 结果。

## 8. 重置示范库

```bash
./scripts/reset_database.sh
python3 scripts/seed_database.py
python3 scripts/verify_readonly_access.py
```

或：`docker compose down -v && docker compose up -d` 后重新灌数。

## 9. Stage 5 完成标准

- [x] 独立 Postgres 可启动  
- [x] 只读用户可读六个业务 Schema  
- [x] 提供连接配置示例与操作说明  
- [x] 不修改 Auto-Ontology 项目  
- [ ] 在你的 Auto-Ontology 实例中实际 Test + Save + Ingest（需本地已部署 UI/服务；本阶段交付连接就绪，不代改对方配置）
