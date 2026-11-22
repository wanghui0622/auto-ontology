# 经营指标定义（Stage 4 抽检口径）

本文件定义 StarSea 示范库中用于质量校验与后续分析的核心指标。  
**充值收入、商城 GMV、钱包消费、退款、广告花费不是同一指标。**

统计时间若未特别声明，以数据内最大会话日为锚定日 `as_of_date`。

## 活跃

| 指标 | 分子 | 分母 / 粒度 | SQL 要点 |
|---|---|---|---|
| DAU | 锚定日有登录会话的去重 `player_id` | 日 | `game.player_sessions.login_at::date` |
| WAU | 锚定日前 7 日（含当日）去重玩家 | 7 日窗 | 同上 |
| MAU | 锚定日前 30 日去重玩家 | 30 日窗 | 同上 |
| 平均在线时长 | 会话 `duration_seconds` 均值 | 会话 | 排除 NULL |

## 充值

| 指标 | 口径 |
|---|---|
| 充值成功金额 | `recharge_orders.order_amount`，`status = 'success'`（人民币套餐标价） |
| 渠道实收 | `payment_transactions.paid_amount`，`status = 'success'` |
| 到账钻石 | 成功订单的 `credit_currency_amount` 或 `wallet_ledgers` 中 `recharge_credit` |
| 充值成功率 | 成功类订单数 / 全部充值订单（抽检用 success+refunded 可视需求调整） |
| ARPU | 充值成功金额 / 全部玩家 |
| ARPPU | 充值成功金额 / 至少一笔成功充值的玩家 |
| 付费率 | 成功充值玩家数 / 全部玩家 |

退款：`payment_refunds` + 可能的 `payment_refund_debit` 账本；净收入 = 成功实收 − 已完成退款。

## 商城

| 指标 | 口径 |
|---|---|
| 商城 GMV（CNY） | `mall_orders.paid_amount`，`price_currency='CNY'`，状态 ∈ paid/delivered/refunded/partial_refunded |
| 商城 GMV（DIAMOND） | 同上，`price_currency='DIAMOND'`（单位是钻石，不可与人民币直接相加） |
| 退款率 | 有退款订单数 / 已支付订单数 |

钱包扣款流水 `mall_debit` 对应钻石商城实付，不等于充值收入。

## 客服

| 指标 | 口径 |
|---|---|
| 工单量 | `support.tickets` 行数（可按 `opened_at` 过滤） |
| 解决率 | status ∈ resolved/closed 的工单 / 全部工单 |
| 满意度 | `customer_satisfaction.score` 均值 |

## 推广

| 指标 | 口径 |
|---|---|
| 渠道新增 | `player_attributions` 中 `attribution_type='first_touch'` 按渠道计数 |
| 推广费用 | `ad_costs.cost_amount` 求和（CNY） |
| CAC | 渠道费用 / 该渠道 first_touch 新增玩家 |
| ROI | 渠道带来玩家的充值成功金额 / 渠道费用（需声明归因口径） |

归因必须声明：`first_touch` / `last_touch` / `campaign_conversion`，不可混用。
