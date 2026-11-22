# 自然语言分析问题（≥25）

每题给出统计口径；对应可执行 SQL 见 `sql/analytics-workload.sql`（编号 Q01–Q35）。  
金额口径遵循 `docs/metric-definitions.md`：**充值收入 ≠ 商城 GMV ≠ 钱包消费 ≠ 退款 ≠ 广告花费**。

锚定日：`as_of = max(game.player_sessions.login_at::date)`。

## 游戏运营

| ID | 问题 | 口径摘要 |
|---|---|---|
| Q01 | 锚定日的 DAU 是多少？ | 当日去重 `player_id` |
| Q02 | 近 7 日 WAU、近 30 日 MAU 是多少？ | 窗口去重玩家 |
| Q03 | 最近 30 日每日新增玩家数？ | `register_time::date` |
| Q04 | 角色等级分布（分段）？ | `characters.level` 分桶 |
| Q05 | 平均会话时长（秒）？ | `avg(duration_seconds)` |
| Q06 | 任务完成率？ | completed / 全部 mission_records |
| Q07 | 两款游戏各自的 MAU？ | 会话关联 `game_id` |

## 商城

| ID | 问题 | 口径摘要 |
|---|---|---|
| Q08 | 商城钻石 GMV 与人民币 GMV？ | `paid_amount` 按 `price_currency` |
| Q09 | 商品销量 Top 10？ | order_items 数量合计 |
| Q10 | 各商品分类销售额（钻石）？ | 分类 × DIAMOND line |
| Q11 | 商城退款率？ | 有退款订单 / 已支付订单 |
| Q12 | 有会话玩家中的商城购买转化率？ | 近 30 日有登录且有商城支付 |

## 充值

| ID | 问题 | 口径摘要 |
|---|---|---|
| Q13 | 充值成功总金额（CNY）？ | `order_amount` 且 success |
| Q14 | 充值成功率？ | success 类 / 全部订单 |
| Q15 | ARPU 与 ARPPU？ | 成功金额 / 全玩家 与 / 付费玩家 |
| Q16 | 付费率？ | 成功充值玩家 / 全玩家 |
| Q17 | 充值金额分布（套餐档位）？ | 按 order_amount 分组 |
| Q18 | 各支付渠道成功交易笔数与实收？ | transactions success |
| Q19 | 玩家累计充值 Top 20？ | 成功订单按玩家汇总 |

## 客服

| ID | 问题 | 口径摘要 |
|---|---|---|
| Q20 | 工单总量与解决率？ | resolved/closed 占比 |
| Q21 | 平均处理时长（小时）？ | closed_at − opened_at |
| Q22 | 平均满意度？ | csat.score |
| Q23 | 充值类工单占比？ | category=recharge_missing |
| Q24 | 高价值（whale）玩家投诉率？ | whale 中有工单占比 |
| Q25 | 各游戏相关工单量（经角色关联）？ | tickets→characters→games |

## 推广

| ID | 问题 | 口径摘要 |
|---|---|---|
| Q26 | 各渠道 first_touch 新增玩家？ | attributions |
| Q27 | 各渠道 CAC？ | ad_costs / first_touch 人数 |
| Q28 | 各活动参与人数与转化人数？ | participations |
| Q29 | 渠道充值转化率（注册 30 日内）？ | first_touch × 30 日成功充值 |

## 跨域

| ID | 问题 | 口径摘要 |
|---|---|---|
| Q30 | 哪个 first_touch 渠道带来的充值成功金额最高？ | 归因 × 充值 |
| Q31 | 高等级 vs 低等级玩家平均充值？ | max(level) 分桶 × 充值 |
| Q32 | 高价值玩家工单主要问题类型？ | whale × ticket category |
| Q33 | 玩家充值金额与累计在线时长是否同向？ | 相关分层对比 |
| Q34 | 高付费玩家最爱买的商品 Top 10？ | whale × mall items |
| Q35 | 推广费用较高的渠道是否 LTV（累计充值）更高？ | CAC 渠道 × 人均充值 |
