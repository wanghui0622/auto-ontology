# Auto-Ontology 本体自动化验证（Stage 6）

## 1. 验证范围与约束

- 源库：`starsea_gaming`（只读账号 `starsea_readonly`）
- **不修改** Auto-Ontology 源码、根配置或其 catalog 数据库
- 本阶段用 Auto-Ontology **Postgres 连接器库**对示范库做只读探测（`scripts/probe_ao_discovery.py`），并提供 35 道分析题 + 可执行 SQL 作为 NLQ/SQL 金标准
- 在操作者自己的 Auto-Ontology UI 完成 Settings→Connections→Ingest 后，将实际 Terms/Relationships/NLQ 结果填入第 6 节

## 2. 连接器探测结果（已执行）

命令：

```bash
python3 scripts/verify_readonly_access.py
# 需 Auto-Ontology 依赖（pandas 等）
uv run python scripts/probe_ao_discovery.py
bash scripts/run_analytics_workload.sh
```

探测摘要（见 `docs/stage6-discovery-probe.json`）：

| 信号 | 结果 |
|---|---|
| 业务表 | 45（六 Schema） |
| 列 | 406 |
| FK（`pg_constraint`） | 84（跨 Schema 32） |
| PK（`information_schema`，需 REFERENCES） | 48 行可见 |
| 指向 `identity.players` 的 FK | 16 条边（跨 game/mall/payment/support/marketing） |
| 核心实体表 | Player/Game/Character/MallOrder/RechargeOrder/Wallet/Ticket/Campaign 等均存在 |
| 桥接表 | 标签、战斗参与、商品道具、活动渠道、工单分配均存在 |
| 金额/归因语义列 | `order_amount` / `paid_amount` / `payable_amount` / `balance` / `change_amount` / `entry_type` / `refund_amount` / `attribution_type` 可发现 |

### 2.1 只读权限修正（Stage 6）

PostgreSQL 对 **仅 SELECT** 角色会在 `information_schema.table_constraints` 中隐藏 PRIMARY KEY。  
Auto-Ontology Postgres 连接器的 FK 已改读 `pg_constraint`，但 **PK 仍读 information_schema**。

因此只读角色额外授予 `REFERENCES`（**不能** INSERT/UPDATE/DELETE 数据，已用 42501 验证），以便自动发现主键。授权脚本：`sql/04_grants_readonly.sql`。

## 3. 八项能力检查表

| # | 检查项 | 结构/数据侧证据 | 状态 |
|---|---|---|---|
| 1 | 识别 Player/Game/Character/Order/Recharge/Ticket/Campaign | 核心表名+COMMENT+PK 可发现 | **结构 PASS**；UI Terms 待填 |
| 2 | 跨 Schema 同一玩家实体 | 多表 `player_id` → `identity.players` FK | **结构 PASS** |
| 3 | 推断跨表关系 | 84 FK / 32 跨 Schema | **结构 PASS** |
| 4 | 发现多对多/桥接 | 5+ 桥接表存在 | **结构 PASS** |
| 5 | 区分充值/商城消费/退款 | 分表+分列名+`entry_type`+COMMENT | **结构 PASS** |
| 6 | 识别关键经营指标 | 口径文档 + Q13–Q16/Q08 SQL 可算 | **SQL PASS**；SQL Attributes 待 UI |
| 7 | 跨六域自然语言查询 | 35 题覆盖六域与跨域 | **金标准就绪**；NLQ 待 UI |
| 8 | 正确 SQL/JOIN 路径 | `analytics-workload.sql` 全部可执行 | **SQL PASS** |

## 4. 预期自动发现的实体与关系（人工对照清单）

### 实体（期望 Terms / catalog nodes）

| 概念 | 主要物理表 |
|---|---|
| Player | `identity.players` |
| PlayerAccount | `identity.player_accounts` |
| Game / GameServer / Character | `game.games` / `game_servers` / `characters` |
| MallOrder / Product | `mall.mall_orders` / `products` |
| RechargeOrder / PaymentTransaction / Wallet | `payment.recharge_orders` / `payment_transactions` / `wallets` |
| Ticket / Agent | `support.tickets` / `agents` |
| Campaign / MarketingChannel | `marketing.campaigns` / `marketing_channels` |

### 关系（期望）

- Player 1—N Character / Session / MallOrder / RechargeOrder / Ticket / Attribution
- RechargeOrder 1—N PaymentTransaction；Wallet 1—N WalletLedger
- MallOrder 1—N MallOrderItem；Campaign M—N Channel（`campaign_channels`）
- Ticket 可选关联 RechargeOrder / MallOrder / Character / Campaign

### SQL Attributes / 指标（期望能区分）

| 名称 | 勿与混淆 |
|---|---|
| 充值成功金额 `recharge_orders.order_amount` | 渠道实收 `payment_transactions.paid_amount` |
| 商城 GMV `mall_orders.paid_amount` | 充值收入 |
| 钱包余额 / `entry_type` 流水 | 标价金额 |
| 退款 | 收入 |
| 广告 `cost_amount` | 玩家付费 |
| `attribution_type` | 单一 channel_id |

## 5. 分析题 SQL 验证

- 问题列表：`docs/analysis-questions.md`（Q01–Q35）
- SQL：`sql/analytics-workload.sql`
- 本地执行：`bash scripts/run_analytics_workload.sh` → **35/35 PASS**（日志见 `/opt/cursor/artifacts/starsea-stage6-analytics.log`）

抽样金标准（seed=42，锚定日 `2026-11-22`）：

| 题 | 结果摘要 |
|---|---|
| Q01 DAU | 205 |
| Q08 商城 GMV | CNY 272294.00；DIAMOND 7426620.00 |
| Q13 充值成功金额 | 869068.00 CNY |
| Q27 CAC（花费/ first_touch） | official_website 435.28 … kol 1803.97 |
| Q33 在线时长四分位 × 人均充值 | Q1 162.59 → Q4 1213.68（同向） |
| Q35 渠道花费 vs 人均充值 LTV | 高花费渠道人均 LTV 未必更高（community 469 vs short_video 428） |

金标准用途：对比 Auto-Ontology 生成 SQL 的 JOIN 路径与指标口径（尤其 GMV vs 充值 vs 退款；CAC 勿把 `ad_costs` 与 attributions 笛卡尔积）。

## 6. UI 实测记录模板（操作者填写）

在已部署 Auto-Ontology 中按 `docs/auto-ontology-connection.md` 接入后填写：

| 项 | 结果 | 备注 |
|---|---|---|
| Connection test |  | Postgres 可能返回空 schema 列表（连接器无 `get_schemas`），属预期；ingest 仍扫全部非系统 schema |
| Ingest 表数量 |  | 期望 45 |
| 识别到的 Player 相关 Terms |  |  |
| 跨 Schema player 关系 |  |  |
| 桥接表关系 |  |  |
| 金额类 Attributes 是否混淆 |  |  |
| NLQ 抽样（建议 Q01/Q08/Q13/Q30） |  | 粘贴生成 SQL |
| 识别错误 |  |  |
| 人工修正 |  | **仅作记录；本示范流程要求尽量不预置本体** |

### 建议 NLQ 抽样题

1. 锚定日 DAU 是多少？  
2. 商城钻石 GMV 和人民币 GMV 分别是多少？  
3. 充值成功总金额、ARPU、付费率？  
4. 哪个 first_touch 渠道带来的充值金额最高？  
5. 高价值玩家的客服工单主要是哪些类型？  

## 7. 已知限制

1. **未在本 Cloud Agent 中写入 Auto-Ontology catalog**：避免违反「不修改 AO 数据库」约束；UI Ingest/NLQ 需操作者在自有实例完成。  
2. Postgres `POST /connections/test` 对无 `get_schemas` 的驱动返回 `schemas: []`，不代表连不通。  
3. 若未授予 `REFERENCES`，只读角色看不到 PK（已在 Stage 6 修复授权）。  
4. 同义词（玩家/用户/账号持有人）主要靠 COMMENT 与文档；自动消歧效果因模型/版本而异。

## 8. 结论

| 层 | 结论 |
|---|---|
| 数据与结构就绪 | **PASS**（Stage 2–5） |
| 连接器可发现信号 | **PASS**（表/FK/PK/跨域 Player/金额列/桥接） |
| 分析 SQL 金标准 | **PASS**（35 题可执行） |
| AO UI 自动成本体 + NLQ | **待操作者实例实测**（模板已备） |

示范库已具备「不手工预置本体即可开始自动本体化实验」的条件；剩余工作是在目标 Auto-Ontology 部署上完成连接与 ingest，并用第 5–6 节金标准验收生成 SQL。
