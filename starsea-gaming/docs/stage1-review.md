# Stage 1 确认清单

> **状态（Stage 2）**：已按「建议默认」列进入 DDL 实现（用户指令：进入 Stage 2）。若需调整 D1–D8，请在后续迭代说明。

请在进入 Stage 2（DDL / Docker / 数据生成）前确认下列内容。回复「确认」或标注需修改的决策点即可。

## A. 已定模型摘要

1. 单库 `starsea_gaming`，六 Schema：`identity` / `game` / `mall` / `payment` / `support` / `marketing`。
2. **45 张业务表**（见 `domain-model.md`），Player 为跨域枢纽，但不强制所有表直连 Player。
3. 金额概念分离：充值标价、渠道实付、虚拟币到账、商城应付/实付、钱包余额、退款、广告花费。
4. 归因三口径：`first_touch` / `last_touch` / `campaign_conversion`。
5. 推广渠道 ≠ 支付渠道；钱包属于玩家，道具落到角色。
6. 跨 Schema 原生 FK + COMMENT 承载语义，**不预置 Auto-Ontology 本体**。

## B. 请确认的开放决策

| ID | 决策点 | 建议默认 | 备选 |
|---|---|---|---|
| D1 | 主键形态 | 全部 `UUID` | `BIGSERIAL`；业务单号另设 `order_no` |
| D2 | 虚拟币代码 | 统一 `DIAMOND`（两游戏共用钱包币种） | 分游戏币种（`ERA_DIAMOND` / `EXP_COIN`），一玩家多钱包 |
| D3 | `player_type` 维护方式 | 生成时按付费分层写入，并可被累计充值规则回写 | 仅衍生视图，不落表 |
| D4 | `identity.registration_sources` 与 `marketing.marketing_channels` | 两表并存，用 `source_code`≈`channel_code` 对齐 | 合并为单一渠道表（削弱域边界） |
| D5 | 商城人民币直购 | 支持 `price_currency in (CNY, DIAMOND)` | 仅虚拟币商城 |
| D6 | 钱包流水回指活动奖励 | `wallet_ledgers.campaign_reward_id` 可空 FK | 仅用 `remark` 文本追溯 |
| D7 | 区服数量 | 两游戏共 10 服（如 6+4） | 平均 5+5 |
| D8 | 项目在本仓库中的位置 | `starsea-gaming/` 子目录，不改 Auto-Ontology 代码 | 独立仓库（需另开 repo） |

## C. Stage 2 将交付（确认后）

- `docker-compose.yml`（独立 PG17，库名 `starsea_gaming`）
- `sql/01_create_schemas.sql` / `02_create_tables.sql` / `03_constraints_indexes.sql`
- 表/列 COMMENT、只读用户示例
- 尚不生成全量模拟数据（Stage 3）

## D. 文档索引

| 文件 | 用途 |
|---|---|
| `business-overview.md` | 公司、产品、术语、主链路 |
| `domain-model.md` | 六域实体与边界 |
| `business-relationships.md` | 跨域边、桥接、禁止关系 |
| `er-diagram.mmd` | 完整逻辑 ER（Mermaid） |

## E. 建议回复模板

```text
确认 Stage 1。
D1=UUID, D2=分游戏币种, D3=落表, D4=两表并存, D5=支持双计价, D6=FK, D7=6+4, D8=子目录
另改：……
```

若无特殊说明，将按「建议默认」列进入 Stage 2。
