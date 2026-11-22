# 数据质量报告（Stage 4）

- generated_at (UTC): `2026-11-22T14:45:47.450743+00:00`
- checks: 74
- PASS: 74
- FAIL: 0
- WARN: 0
- overall: **PASS**

## 1. 数据规模

| 表 | 行数 | 下限 |
|---|---:|---:|
| `identity.players` | 2000 | 2000 |
| `identity.player_accounts` | 2500 | 2500 |
| `game.games` | 2 | 2 |
| `game.game_servers` | 10 | 10 |
| `game.characters` | 3000 | 3000 |
| `game.player_sessions` | 30000 | 30000 |
| `game.game_events` | 50000 | 50000 |
| `game.mission_records` | 15000 | 15000 |
| `game.battles` | 10000 | 10000 |
| `mall.products` | 100 | 100 |
| `mall.mall_orders` | 9537 | 8000 |
| `mall.mall_order_items` | 15000 | 15000 |
| `payment.recharge_orders` | 6000 | 6000 |
| `payment.payment_transactions` | 6000 | 6000 |
| `payment.wallet_ledgers` | 20001 | 20000 |
| `support.tickets` | 3000 | 3000 |
| `support.ticket_messages` | 12038 | 12000 |
| `marketing.campaigns` | 30 | 30 |
| `marketing.ad_costs` | 3000 | 3000 |
| `marketing.player_attributions` | 3974 | 2000 |
| `marketing.campaign_participations` | 8000 | 8000 |

## 2. 检查明细

### attribution

| 检查项 | 状态 | 说明 |
|---|---|---|
| `attribution:every_player_first_touch` | PASS | missing=0 |
| `attribution:first_touch_matches_registration_source` | PASS | mismatches=0 |
| `attribution:has_three_types` | PASS | distribution={'campaign_conversion': 1100, 'first_touch': 2000, 'last_touch': 874} |

### distribution

| 检查项 | 状态 | 说明 |
|---|---|---|
| `distribution:player_type_long_tail` | PASS | distribution={'free': 1400, 'light_payer': 400, 'mid_payer': 160, 'whale': 40} |

### foreign_key

| 检查项 | 状态 | 说明 |
|---|---|---|
| `fk_orphan:game.characters.player_id` | PASS | orphans=0 |
| `fk_orphan:mall.mall_orders.player_id` | PASS | orphans=0 |
| `fk_orphan:payment.recharge_orders.player_id` | PASS | orphans=0 |
| `fk_orphan:support.tickets.player_id` | PASS | orphans=0 |
| `fk_orphan:marketing.player_attributions.player_id` | PASS | orphans=0 |
| `fk_orphan:payment.wallet_ledgers.wallet_id` | PASS | orphans=0 |
| `fk_orphan:mall.mall_order_items.mall_order_id` | PASS | orphans=0 |
| `fk_orphan:payment.payment_transactions.recharge_order_id` | PASS | orphans=0 |
| `fk:catalog_count` | PASS | fk_constraints=84 |

### mall

| 检查项 | 状态 | 说明 |
|---|---|---|
| `mall:paid_has_delivery` | PASS | missing_delivery=0 |
| `mall:line_amount_math` | PASS | bad_lines=0 |
| `mall:diamond_paid_has_wallet_debit` | PASS | missing_debit=0 |

### metrics

| 检查项 | 状态 | 说明 |
|---|---|---|
| `metric:dau_positive` | PASS | dau_last_day=205 |
| `metric:mau_ge_wau_ge_dau` | PASS | dau=205, wau=1044, mau=1767 |
| `metric:recharge_gmv_distinct_from_mall_gmv` | PASS | recharge CNY revenue and mall GMV use different measures |
| `metric:arpu_le_arppu` | PASS | arpu=434.53, arppu=704.27 |
| `metric:pay_rate_in_0_1` | PASS | pay_rate=0.617 |
| `metric:ticket_resolve_rate_in_0_1` | PASS | ticket_resolve_rate=0.7573 |
| `metric:cac_channels_computed` | PASS | channels=['affiliate', 'app_store', 'community', 'feed_ads', 'kol', 'official_website', 'short_video'] |

### nullability

| 检查项 | 状态 | 说明 |
|---|---|---|
| `null:identity.players.nickname` | PASS | null_rows=0 |
| `null:identity.players.register_time` | PASS | null_rows=0 |
| `null:game.characters.player_id` | PASS | null_rows=0 |
| `null:mall.mall_orders.player_id` | PASS | null_rows=0 |
| `null:mall.mall_orders.payable_amount` | PASS | null_rows=0 |
| `null:payment.recharge_orders.order_amount` | PASS | null_rows=0 |
| `null:payment.wallets.balance` | PASS | null_rows=0 |
| `null:payment.wallet_ledgers.change_amount` | PASS | null_rows=0 |
| `null:support.tickets.player_id` | PASS | null_rows=0 |
| `null:support.ticket_messages.message_body` | PASS | null_rows=0 |
| `null:marketing.player_attributions.attribution_type` | PASS | null_rows=0 |

### primary_key

| 检查项 | 状态 | 说明 |
|---|---|---|
| `pk:identity.players.player_id` | PASS | total=2000, distinct=2000 |
| `pk:game.characters.character_id` | PASS | total=3000, distinct=3000 |
| `pk:mall.mall_orders.mall_order_id` | PASS | total=9537, distinct=9537 |
| `pk:payment.recharge_orders.recharge_order_id` | PASS | total=6000, distinct=6000 |
| `pk:payment.wallets.wallet_id` | PASS | total=2000, distinct=2000 |
| `pk:payment.wallet_ledgers.ledger_id` | PASS | total=20001, distinct=20001 |
| `pk:support.tickets.ticket_id` | PASS | total=3000, distinct=3000 |
| `pk:marketing.campaigns.campaign_id` | PASS | total=30, distinct=30 |
| `pk:marketing.player_attributions.attribution_id` | PASS | total=3974, distinct=3974 |

### recharge

| 检查项 | 状态 | 说明 |
|---|---|---|
| `recharge:success_has_success_txn` | PASS | missing_txn=0 |
| `recharge:paid_amount_equals_order_amount` | PASS | mismatches=0 (demo generator sets them equal; promotions may differ later) |
| `recharge:success_has_credit_ledger` | PASS | missing_ledger=0 |

### scale

| 检查项 | 状态 | 说明 |
|---|---|---|
| `scale:identity.players` | PASS | count=2000, minimum=2000 |
| `scale:identity.player_accounts` | PASS | count=2500, minimum=2500 |
| `scale:game.games` | PASS | count=2, minimum=2 |
| `scale:game.game_servers` | PASS | count=10, minimum=10 |
| `scale:game.characters` | PASS | count=3000, minimum=3000 |
| `scale:game.player_sessions` | PASS | count=30000, minimum=30000 |
| `scale:game.game_events` | PASS | count=50000, minimum=50000 |
| `scale:game.mission_records` | PASS | count=15000, minimum=15000 |
| `scale:game.battles` | PASS | count=10000, minimum=10000 |
| `scale:mall.products` | PASS | count=100, minimum=100 |
| `scale:mall.mall_orders` | PASS | count=9537, minimum=8000 |
| `scale:mall.mall_order_items` | PASS | count=15000, minimum=15000 |
| `scale:payment.recharge_orders` | PASS | count=6000, minimum=6000 |
| `scale:payment.payment_transactions` | PASS | count=6000, minimum=6000 |
| `scale:payment.wallet_ledgers` | PASS | count=20001, minimum=20000 |
| `scale:support.tickets` | PASS | count=3000, minimum=3000 |
| `scale:support.ticket_messages` | PASS | count=12038, minimum=12000 |
| `scale:marketing.campaigns` | PASS | count=30, minimum=30 |
| `scale:marketing.ad_costs` | PASS | count=3000, minimum=3000 |
| `scale:marketing.player_attributions` | PASS | count=3974, minimum=2000 |
| `scale:marketing.campaign_participations` | PASS | count=8000, minimum=8000 |

### status

| 检查项 | 状态 | 说明 |
|---|---|---|
| `status:cancelled_mall_unpaid` | PASS | bad_rows=0 |
| `status:closed_tickets_have_closed_at` | PASS | bad_rows=0 |
| `status:completed_missions_have_completed_at` | PASS | bad_rows=0 |
| `support:message_body_meaningful` | PASS | short_messages=0 |

### wallet

| 检查项 | 状态 | 说明 |
|---|---|---|
| `wallet:balance_equals_ledger_sum` | PASS | mismatches=0 |
| `wallet:no_negative_balance` | PASS | negative=0 |
| `wallet:last_ledger_matches_balance` | PASS | mismatches=0 |

## 3. 经营指标抽检（口径见下）

- 统计锚定日 `as_of_date` = `2026-11-22`（取会话最大登录日）
- DAU = 205
- WAU(7d) = 1044
- MAU(30d) = 1767
- 充值成功金额（CNY，`status=success`）= 869068.00
- 商城 GMV CNY / DIAMOND = 272294.00 / 7426620.00
- ARPU / ARPPU = 434.53 / 704.27
- 付费率 = 0.617
- 充值成功率 = 0.697
- 工单解决率 = 0.7573
- 平均会话时长(秒) = 876.52

### CAC by first_touch channel

| channel | cost_cny | new_players | CAC |
|---|---:|---:|---:|
| `affiliate` | 22371005.16 | 153 | 146215.72 |
| `app_store` | 127272667.50 | 425 | 299465.10 |
| `community` | 22034344.50 | 210 | 104925.45 |
| `feed_ads` | 314222084.75 | 505 | 622221.95 |
| `kol` | 54617042.70 | 174 | 313891.05 |
| `official_website` | 9151773.60 | 145 | 63115.68 |
| `short_video` | 242756949.12 | 388 | 625662.24 |

## 4. 指标口径摘要

| 指标 | 口径 |
|---|---|
| DAU | `game.player_sessions` 在锚定日去重 `player_id` |
| WAU / MAU | 锚定日前 7 / 30 天去重玩家 |
| 充值成功金额 | `payment.recharge_orders.order_amount` 且 `status='success'`（人民币标价） |
| 商城 GMV | `mall.mall_orders.paid_amount`，按 `price_currency` 分开；不含充值收入 |
| ARPU | 充值成功金额 / 全部玩家 |
| ARPPU | 充值成功金额 / 至少一笔成功充值的玩家 |
| 付费率 | 成功充值玩家数 / 全部玩家 |
| CAC | 渠道广告成本 / 该渠道 `first_touch` 玩家数 |

## 5. 结论

PASS — 外键/主键/空值、钱包核对、充值与支付、商城发放、归因注册对齐、状态一致性与核心经营指标抽检均通过。
