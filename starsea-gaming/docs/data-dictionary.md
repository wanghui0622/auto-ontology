# 数据字典（Stage 2）

字段级权威定义以数据库 `COMMENT` 与 DDL CHECK 为准。本文按 Schema 列出表职责与关键字段口径。

主键均为 `UUID`；业务表均含 `created_at` / `updated_at`（`TIMESTAMPTZ`，UTC）。金额字段均为 `NUMERIC(14,2)`。

## identity

| 表 | 说明 | 关键字段 |
|---|---|---|
| `registration_sources` | 注册来源字典 | `source_code`, `source_type` |
| `players` | 统一玩家 | `player_id`, `nickname`, `register_time`, `player_type`, `vip_level` |
| `player_accounts` | 游戏登录账号 | `account_id`, `player_id`, `game_id`, `account_name` |
| `player_devices` | 设备 | `device_id`, `device_os`, `first_seen_at`, `last_seen_at` |
| `player_tags` | 标签字典 | `tag_code`, `tag_category` |
| `player_tag_relations` | 玩家↔标签 | `(player_id, tag_id)` |

## game

| 表 | 说明 | 关键字段 |
|---|---|---|
| `games` | 游戏主数据 | `game_code`（`STARSEA_ERA` / `STARSEA_EXPEDITION`） |
| `game_servers` | 区服 | `server_code`, `region` |
| `characters` | 角色 | `level`, `combat_power`, `total_play_minutes` |
| `character_attributes` | 角色属性 KV | `attribute_key`, `attribute_value` |
| `player_sessions` | 登录会话 | `login_at`, `logout_at`, `duration_seconds` |
| `game_events` | 行为事件 | `event_type`, `event_time`, `event_payload` |
| `missions` | 任务定义 | `mission_type`, `min_level` |
| `mission_records` | 任务进度 | `status`, `completed_at` |
| `battles` | 战斗场次 | `battle_type`, `started_at` |
| `battle_participants` | 参战角色 | `side`, `result`, `damage_dealt` |
| `game_items` | 道具定义 | `item_code`, `item_type`, `rarity` |

## mall

| 表 | 说明 | 关键字段 |
|---|---|---|
| `product_categories` | 分类 | `parent_category_id` |
| `products` | 商品 | `price_currency`（CNY/DIAMOND）, `list_price` |
| `product_items` | 商品含道具 | `game_item_id`, `quantity` |
| `mall_orders` | 订单头 | `payable_amount`, `paid_amount`, `payment_method`, `status` |
| `mall_order_items` | 明细 | `unit_price`, `line_amount` |
| `mall_refunds` | 退款 | `refund_amount`, `reason_code` |
| `item_delivery_records` | 发放 | `delivery_status`, `delivered_at` |

## payment

| 表 | 说明 | 关键字段 |
|---|---|---|
| `payment_channels` | 支付渠道 | `channel_type` |
| `recharge_products` | 充值套餐 | `price_amount_cny`, `credit_currency_amount` |
| `recharge_orders` | 充值订单 | `order_amount`≠实付；`credit_currency_amount`=到账钻石 |
| `payment_transactions` | 支付流水 | `paid_amount`=渠道实收 |
| `payment_refunds` | 充值退款 | `refund_amount` |
| `wallets` | 钱包 | `balance`（DIAMOND） |
| `wallet_ledgers` | 账本 | `entry_type`, `change_amount`, `balance_after` |

## support

| 表 | 说明 | 关键字段 |
|---|---|---|
| `agents` | 坐席 | `team_name` |
| `ticket_categories` | 工单分类 | `category_code` |
| `tickets` | 工单 | 可选 `character_id` / `recharge_order_id` / `mall_order_id` / `campaign_id` |
| `ticket_messages` | 消息 | `sender_type`, `message_body` |
| `ticket_assignments` | 分配史 | `assigned_at`, `unassigned_at` |
| `ticket_resolution_records` | 结案 | `resolution_code`, `resolution_summary` |
| `customer_satisfaction` | 满意度 | `score`（1–5） |

## marketing

| 表 | 说明 | 关键字段 |
|---|---|---|
| `marketing_channels` | 推广渠道 | `channel_family` |
| `campaigns` | 活动 | `campaign_type`, `start_at`, `end_at` |
| `campaign_channels` | 活动↔渠道 | 复合主键 |
| `ad_costs` | 投放成本 | `cost_date`, `cost_amount`, `impressions`, `clicks` |
| `player_attributions` | 归因 | `attribution_type` ∈ first_touch/last_touch/campaign_conversion |
| `campaign_participations` | 参与 | `converted_recharge_order_id` |
| `campaign_rewards` | 奖励 | `reward_type`, `grant_status` |

## 表数量核对

| Schema | 表数 |
|---|---:|
| identity | 6 |
| game | 11 |
| mall | 7 |
| payment | 7 |
| support | 7 |
| marketing | 7 |
| **合计** | **45** |
