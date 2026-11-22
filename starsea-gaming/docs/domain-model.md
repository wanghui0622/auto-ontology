# 领域模型：六大业务域与核心实体

本文定义 Stage 1 的逻辑实体。物理类型、索引与 COMMENT 在 Stage 2 DDL 中落地。

约定：

- 主键：`*_id`，跨域引用时类型与含义保持一致。
- 审计：业务表均含 `created_at`、`updated_at`（UTC）。
- 软状态：用 `status` 枚举表达生命周期，删除以状态为主，少做物理删除。

---

## 1. identity — 玩家账户与身份域

### 1.1 实体清单

| 实体 | 表名 | 说明 |
|---|---|---|
| Player | `players` | **跨域统一玩家实体** |
| PlayerAccount | `player_accounts` | 玩家在某游戏下的登录账号（一玩家可多账号） |
| PlayerDevice | `player_devices` | 登录/注册设备指纹 |
| PlayerTag | `player_tags` | 标签字典（如高价值、回流、风险） |
| PlayerTagRelation | `player_tag_relations` | 玩家↔标签 M:N |
| RegistrationSource | `registration_sources` | 注册来源字典（渠道细分，可对齐营销渠道） |

### 1.2 Player（核心）

关键属性：

- `player_id`（PK）
- `nickname`
- `register_time`
- `register_channel`（展示用渠道名；结构化归因以 marketing 为准）
- `registration_source_id`（FK → `registration_sources`）
- `country`
- `status`（`active` / `banned` / `churned` / `deleted`）
- `player_type`（`free` / `light_payer` / `mid_payer` / `whale`，可由累计充值回写或生成时设定）
- `vip_level`（客服优先级参考）
- `created_at` / `updated_at`

### 1.3 域内关系

```text
players 1──* player_accounts
players 1──* player_devices
players *──* player_tags  (via player_tag_relations)
players *──1 registration_sources
```

### 1.4 边界

- **不存**角色等级、战斗、订单、钱包余额。
- 注册时刻可同时写入 `marketing.player_attributions`（`attribution_type = first_touch`）。

---

## 2. game — 游戏运营域

### 2.1 实体清单

| 实体 | 表名 | 说明 |
|---|---|---|
| Game | `games` | 两款游戏主数据 |
| GameServer | `game_servers` | 区服 |
| Character | `characters` | 游戏角色 |
| CharacterAttribute | `character_attributes` | 角色可变属性（等级、战力等） |
| PlayerSession | `player_sessions` | 登录/在线会话 |
| GameEvent | `game_events` | 行为事件流 |
| Mission | `missions` | 任务定义 |
| MissionRecord | `mission_records` | 角色任务完成记录 |
| Battle | `battles` | 战斗/副本场次 |
| BattleParticipant | `battle_participants` | 战斗参与者 |
| GameItem | `game_items` | 游戏道具定义（商城发放引用） |

### 2.2 关键业务规则

- 一游戏多区服。
- 一玩家多角色；一角色隶属**一个游戏 + 一个区服**。
- 会话挂玩家，可选挂角色（未进角前可为空）。
- 行为事件挂玩家，尽量挂角色。
- 任务记录、战斗参与挂角色（再经角色回到玩家）。
- 等级与累计在线时长正相关（数据生成约束）。

### 2.3 Character 关键属性

- `character_id`, `player_id`, `game_id`, `server_id`
- `character_name`, `level`, `combat_power`
- `last_login_at`, `total_play_minutes`
- `status`

### 2.4 域内关系

```text
games 1──* game_servers
games 1──* characters
game_servers 1──* characters
identity.players 1──* characters
characters 1──* character_attributes
identity.players 1──* player_sessions
characters 0..1──* player_sessions
identity.players 1──* game_events
characters 0..1──* game_events
games 1──* missions
characters 1──* mission_records ──* missions
battles 1──* battle_participants ──* characters
games 1──* game_items
```

### 2.5 边界

- 不存人民币流水；道具**定义**在 game，道具**售卖与发放**在 mall。
- 充值不到账等问题工单可引用 `character_id`，但工单主体在 support。

---

## 3. mall — 游戏商城域

### 3.1 实体清单

| 实体 | 表名 | 说明 |
|---|---|---|
| ProductCategory | `product_categories` | 商品分类 |
| Product | `products` | 可售商品 |
| ProductItem | `product_items` | 商品包含的游戏道具及数量 |
| MallOrder | `mall_orders` | 商城订单头 |
| MallOrderItem | `mall_order_items` | 订单明细 |
| MallRefund | `mall_refunds` | 商城退款 |
| ItemDeliveryRecord | `item_delivery_records` | 购买成功后的道具发放 |

### 3.2 计价体系

商品必须声明计价币种：

- `price_currency = CNY`：人民币直购（较少，或礼包）
- `price_currency = DIAMOND`（或游戏内虚拟币代码）：钱包扣款

订单头记录：

- `payable_amount` / `paid_amount` / `price_currency`
- `payment_method`（`wallet` / `direct_cny` / `mixed`）
- `player_id`（必填，可追溯购买人）
- 可选 `character_id`（道具发往哪个角色）
- 可选 `wallet_ledger_id`（若走钱包扣款，回指账本；或由 ledger 反指订单）

### 3.3 域内关系

```text
product_categories 1──* products
products 1──* product_items ──* game.game_items
identity.players 1──* mall_orders
game.characters 0..1──* mall_orders
mall_orders 1──* mall_order_items ──* products
mall_orders 0..1──* mall_refunds
mall_orders 1──* item_delivery_records
```

### 3.4 边界

- 商城 GMV ≠ 充值收入。
- 退款冲减商城侧；若曾扣钱包，需对应 `wallet_ledgers` 退回流水。

---

## 4. payment — 充值与支付域

### 4.1 实体清单

| 实体 | 表名 | 说明 |
|---|---|---|
| PaymentChannel | `payment_channels` | 支付渠道（支付宝、微信、Apple、Google…） |
| RechargeProduct | `recharge_products` | 充值套餐（标价 RMB → 虚拟币） |
| RechargeOrder | `recharge_orders` | 玩家充值订单 |
| PaymentTransaction | `payment_transactions` | 支付渠道交易流水 |
| PaymentRefund | `payment_refunds` | 充值退款 |
| Wallet | `wallets` | 玩家虚拟钱包（按币种） |
| WalletLedger | `wallet_ledgers` | 钱包变动流水（可核对余额） |

### 4.2 状态机（简化）

充值订单：`created` → `paying` → `success` | `failed` | `closed`；成功后可 `refunded` / `partial_refunded`。

支付交易：与订单 1:1 或 1:N（重试）；成功交易驱动入账。

### 4.3 钱包一致性

```text
wallet.balance == SUM(ledger.change_amount)  （按 wallet_id）
```

流水类型至少：

- `recharge_credit`：充值到账
- `mall_debit`：商城消费扣款
- `mall_refund_credit`：商城退款退回
- `payment_refund_debit`：充值退款扣回
- `campaign_reward_credit`：活动奖励
- `adjust`：客服/运营调账

### 4.4 域内关系

```text
payment_channels 1──* payment_transactions
recharge_products 1──* recharge_orders
identity.players 1──* recharge_orders
identity.players 1──* wallets
recharge_orders 1──* payment_transactions
recharge_orders 0..1──* payment_refunds
wallets 1──* wallet_ledgers
recharge_orders 0..1──* wallet_ledgers   (入账来源)
mall.mall_orders 0..1──* wallet_ledgers  (扣款/退回业务单据)
```

### 4.5 边界

- 不存商品 SKU；只关心钱与虚拟币账本。
- `paid_amount`（渠道实收）与 `order_amount`（套餐标价）允许因优惠而不等，需在指标中定义用哪一个。

---

## 5. support — 游戏客服域

### 5.1 实体清单

| 实体 | 表名 | 说明 |
|---|---|---|
| Agent | `agents` | 客服人员 |
| TicketCategory | `ticket_categories` | 工单分类 |
| Ticket | `tickets` | 客服工单 |
| TicketMessage | `ticket_messages` | 会话消息（含真实业务语义文本） |
| TicketAssignment | `ticket_assignments` | 分配历史（可多次） |
| TicketResolutionRecord | `ticket_resolution_records` | 结案结果 |
| CustomerSatisfaction | `customer_satisfaction` | 满意度评价 |

### 5.2 工单分类（至少）

1. 游戏玩法咨询  
2. 账号异常  
3. 充值未到账  
4. 商城商品问题  
5. 退款申请  
6. 游戏 BUG  
7. 活动奖励问题  
8. 违规处罚申诉  

### 5.3 可选业务挂载（工单头可空外键）

- `player_id`（必填）
- `character_id`（可选）
- `recharge_order_id`（可选）
- `mall_order_id`（可选）
- `campaign_id`（可选，活动奖励类）

高 VIP / 高付费玩家可映射更高 `priority` 或专属坐席组。

### 5.4 域内关系

```text
ticket_categories 1──* tickets
identity.players 1──* tickets
agents 1──* ticket_assignments ──* tickets
tickets 1──* ticket_messages
tickets 0..1──* ticket_resolution_records
tickets 0..1──* customer_satisfaction
```

### 5.5 边界

- 客服不改写钱包余额本身；调账通过 payment 账本并由结案说明引用。
- 消息文本必须可人工阅读、有业务语义。

---

## 6. marketing — 运营推广域

### 6.1 实体清单

| 实体 | 表名 | 说明 |
|---|---|---|
| MarketingChannel | `marketing_channels` | 推广渠道字典 |
| Campaign | `campaigns` | 营销/运营活动 |
| CampaignChannel | `campaign_channels` | 活动↔渠道 M:N |
| AdCost | `ad_costs` | 广告投放成本明细 |
| PlayerAttribution | `player_attributions` | 玩家归因（多口径） |
| CampaignParticipation | `campaign_participations` | 活动参与 |
| CampaignReward | `campaign_rewards` | 活动奖励发放 |

### 6.2 推广渠道（至少）

官方网站、应用商店、信息流广告、短视频平台、社区推广、KOL 推广、联盟推广。

### 6.3 归因口径（关键）

`player_attributions.attribution_type`：

| 类型 | 含义 | 典型写入时机 |
|---|---|---|
| `first_touch` | 首次注册归因 | 注册成功 |
| `last_touch` | 最近一次触点归因 | 回流/再归因窗口 |
| `campaign_conversion` | 活动转化归因 | 活动内充值/关键转化 |

**禁止**用单一 `channel_id` 混用三种口径。ROI/CAC 分析必须声明使用哪一种归因。

### 6.4 域内关系

```text
campaigns *──* marketing_channels  (via campaign_channels)
marketing_channels 1──* ad_costs
campaigns 0..1──* ad_costs
identity.players 1──* player_attributions ──* marketing_channels
identity.players 1──* campaign_participations ──* campaigns
campaign_participations 1──* campaign_rewards
campaign_participations 0..1──* payment.recharge_orders  (转化充值，可选)
```

### 6.5 边界

- 推广渠道 ≠ 支付渠道。
- `registration_sources`（identity）可与 `marketing_channels` 做编码对齐，但表职责分离：前者服务注册主数据，后者服务投放与 ROI。

---

## 7. 实体总览（按域计数）

| Schema | 表数量（Stage 1） |
|---|---:|
| identity | 6 |
| game | 11 |
| mall | 7 |
| payment | 7 |
| support | 7 |
| marketing | 7 |
| **合计** | **45** |

后续若确认需要，可在 Stage 2 微调增删（例如独立 `currencies` 字典表），但不得削弱跨域 `player_id` 枢纽与钱包可核对性。
