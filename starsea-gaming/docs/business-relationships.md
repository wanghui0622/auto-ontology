# 跨业务域关系设计

## 1. 设计原则

1. **Player 是跨域枢纽**，但不是万能外键：角色玩法走 `character_id`，资金走订单/账本，客服挂单据，营销挂归因与参与。
2. **优先数据库原生 FOREIGN KEY**（含跨 Schema FK）。PostgreSQL 支持 `REFERENCES identity.players(player_id)`。
3. **字段类型与语义一致**：凡 `player_id` / `character_id` / `order_id` 等同名引用，类型与含义统一。
4. **不为复杂度而造边**：每条关系必须对应可叙述的业务事实。
5. **保留中间层**：充值 → 支付流水 → 钱包入账；商城订单 → 明细 → 发放；工单 → 分配 → 结案。

## 2. 统一标识约定

| 标识 | 定义域 | 被引用域 | 说明 |
|---|---|---|---|
| `player_id` | identity | game, mall, payment, support, marketing | 统一玩家 |
| `character_id` | game | mall, support, game 子表 | 可选挂载角色 |
| `game_id` / `server_id` | game | game 内 | 角色与任务归属 |
| `recharge_order_id` | payment | payment, support, marketing（转化） | 充值单据 |
| `mall_order_id` | mall | mall, payment（账本）, support | 商城单据 |
| `wallet_id` | payment | payment | 账本归属 |
| `ticket_id` | support | support | 客服会话 |
| `campaign_id` | marketing | marketing, support（可选） | 活动 |
| `marketing_channel_id` | marketing | marketing, 可对齐 identity 来源 | 推广渠道 |
| `game_item_id` | game | mall.product_items / delivery | 道具定义 |

订单号策略建议：

- 充值：`recharge_orders.recharge_order_id`（UUID 或雪花）+ `order_no`（业务可读单号）
- 商城：`mall_orders.mall_order_id` + `order_no`
- **两域订单 ID 不共用序列**，避免语义混淆；客服/账本用明确列名区分。

## 3. 必须实现的跨域边（验收清单）

| # | 从 | 到 | 基数 | 业务含义 |
|---|---|---|---|---|
| 1 | `identity.players` | `game.characters` | 1:N | 玩家拥有角色 |
| 2 | `identity.players` | `game.player_sessions` | 1:N | 玩家登录会话 |
| 3 | `identity.players` | `mall.mall_orders` | 1:N | 玩家商城下单 |
| 4 | `identity.players` | `payment.recharge_orders` | 1:N | 玩家充值 |
| 5 | `identity.players` | `support.tickets` | 1:N | 玩家提单 |
| 6 | `identity.players` | `marketing.player_attributions` | 1:N | 玩家多口径归因 |
| 7 | `game.characters` | `game.mission_records` / `battle_participants` | 1:N | 角色任务与战斗 |
| 8 | `payment.recharge_orders` | `payment.payment_transactions` | 1:N | 订单支付流水 |
| 9 | `payment.wallets` | `payment.wallet_ledgers` | 1:N | 余额可核对 |
| 10 | `mall.mall_orders` | `mall.mall_order_items` | 1:N | 订单明细 |
| 11 | `support.tickets` | `support.ticket_messages` | 1:N | 工单消息 |
| 12 | `marketing.campaigns` | `marketing.campaign_channels` | 1:N | 活动渠道桥 |

## 4. 重要桥接 / 多对多

| 桥接表 | 连接 | 说明 |
|---|---|---|
| `identity.player_tag_relations` | players ↔ player_tags | 运营标签 |
| `game.battle_participants` | battles ↔ characters | 多角色同场 |
| `mall.product_items` | products ↔ game_items | 礼包内容 |
| `marketing.campaign_channels` | campaigns ↔ marketing_channels | 投放组合 |
| `support.ticket_assignments` | tickets ↔ agents | 多次分配历史 |

## 5. 跨域可选外键（推荐实现）

这些边支撑客服与资金闭环，建议建 FK（允许 NULL）：

| 从表.列 | 引用 | 何时非空 |
|---|---|---|
| `mall.mall_orders.character_id` | `game.characters` | 道具发往指定角色 |
| `mall.item_delivery_records.character_id` | `game.characters` | 发放目标 |
| `mall.product_items.game_item_id` | `game.game_items` | 商品含道具 |
| `payment.wallet_ledgers.recharge_order_id` | `payment.recharge_orders` | 充值入账 |
| `payment.wallet_ledgers.mall_order_id` | `mall.mall_orders` | 消费/商城退款 |
| `payment.wallet_ledgers.campaign_reward_id` | `marketing.campaign_rewards` | 活动奖励入账 |
| `support.tickets.character_id` | `game.characters` | 角色相关问题 |
| `support.tickets.recharge_order_id` | `payment.recharge_orders` | 充值未到账等 |
| `support.tickets.mall_order_id` | `mall.mall_orders` | 商城/退款类 |
| `support.tickets.campaign_id` | `marketing.campaigns` | 活动奖励类 |
| `marketing.campaign_participations.converted_recharge_order_id` | `payment.recharge_orders` | 活动内充值转化 |
| `game.player_sessions.character_id` | `game.characters` | 已进入角色 |
| `game.game_events.character_id` | `game.characters` | 角色行为 |

## 6. 关系分层示意

```text
                    ┌──────────── identity.players ────────────┐
                    │                     │                      │
          ┌─────────┴──────┐    ┌─────────┴────────┐   ┌────────┴────────┐
          ▼                ▼    ▼                  ▼   ▼                 ▼
        game.*           mall.*              payment.*              support.*
   (角色/会话/玩法)   (订单/发放)         (充值/钱包/流水)         (工单/满意度)
          │                │                  ▲   │                    │
          │                └──── mall_order ──┘   │                    │
          │                     ledger.debit      │                    │
          │                                       │                    │
          └──────── character_id 可选挂载 ────────┴────────────────────┘

 marketing.* ── first/last/campaign 归因与参与 ──► players
      │
      └── campaign 转化 ──► recharge_orders（可选）
```

## 7. 明确不做的关系

| 不做 | 原因 |
|---|---|
| `ad_costs` 直接 FK 到每个 `player_id` | 成本在渠道/活动日粒度，用归因间接分析 |
| 所有 game 事件直接 FK 支付订单 | 无业务必然性 |
| `marketing_channels` 与 `payment_channels` 合并 | 获客 ≠ 收款 |
| 角色直接持有钱包 | 钱包属于玩家主体，道具才落到角色 |
| 用同一 `order_id` 混充值与商城 | 语义冲突，阻碍自动本体消歧 |

## 8. Auto-Ontology 发现预期

理想自动识别结果（Stage 6 再实测，此处仅作设计意图）：

1. 发现 `Player` 作为多 Schema 共享概念（同名 `player_id` + FK）。
2. 发现 `Character`、`RechargeOrder`、`MallOrder`、`Ticket`、`Campaign` 等实体。
3. 发现 M:N 桥：标签、战斗参与、商品道具、活动渠道。
4. 通过账本 `entry_type` 与金额字段 COMMENT 区分充值入账 vs 商城消费 vs 退款。
5. 归因表 `attribution_type` 支撑多口径，而非单一 channel 边。
