# 业务背景：星海互动（StarSea Gaming）

## 1. 公司与产品

星海互动是一家手游研发与运营公司，旗下运营两款游戏：

| 游戏代码 | 中文名 | 品类 | 核心玩法 |
|---|---|---|---|
| `STARSEA_ERA` | 星海纪元 | 幻想 MMORPG | 角色成长、装备、任务、副本、战斗 |
| `STARSEA_EXPEDITION` | 星海远征 | 策略手游 | 基地、战役、联盟、资源、竞技 |

商业模式：**免费游玩 + 虚拟货币充值 + 道具商城 + 活动运营 + 广告获客**。

模拟数据时间窗口：**最近 12 个月（UTC）**。

## 2. 核心角色（业务术语）

| 术语 | 含义 | 落地表 | 勿与混淆 |
|---|---|---|---|
| 玩家（Player） | 跨游戏统一自然人/账号主体 | `identity.players` | 不是游戏角色 |
| 游戏账号（Player Account） | 玩家在某个游戏平台侧的登录账号 | `identity.player_accounts` | 不是角色 |
| 账号持有人（Account Holder） | 与玩家同义，偏客服/法务口径 | 同 `players` | 文档同义词，非第二实体 |
| 用户（User） | 营销/分析口径下对玩家的称呼 | 同 `players` | 不单独建用户表 |
| 角色（Character） | 某游戏某区服内的可玩实体 | `game.characters` | 隶属玩家 |
| 客服坐席（Agent） | 客服人员 | `support.agents` | 非玩家 |
| 支付渠道 | 支付宝/微信/应用商店等收款通道 | `payment.payment_channels` | 非推广渠道 |
| 推广渠道 | 获客与归因通道 | `marketing.marketing_channels` | 非支付渠道 |

## 3. 端到端业务主链路

```text
推广曝光/点击
    → 注册（identity + marketing 首次归因）
    → 创建游戏账号 / 创建角色（identity + game）
    → 登录会话与游戏行为（game）
    → 充值下单与支付（payment）
    → 钱包入账（payment.wallets / wallet_ledgers）
    → 商城下单与道具发放（mall，钱包或 RMB 计价）
    → 活动参与与奖励（marketing）
    → 异常时发起客服工单（support，可挂充值单/商城单/角色）
```

## 4. 金额与计价体系（必须区分）

| 概念 | 含义 | 典型字段 |
|---|---|---|
| 充值订单金额 | 玩家选择套餐的标价（人民币） | `recharge_orders.order_amount` |
| 实际支付金额 | 渠道实收（可能含优惠后金额） | `payment_transactions.paid_amount` |
| 到账虚拟币数量 | 充值成功写入钱包的钻石等 | `recharge_orders.credit_currency_amount` |
| 商城订单应付 | 商城侧应付总额 | `mall_orders.payable_amount` |
| 商城实付 | 实际扣款（虚拟币或 RMB） | `mall_orders.paid_amount` |
| 钱包余额 | 当前可用虚拟币 | `wallets.balance` |
| 退款金额 | 冲减原订单的金额 | `payment_refunds` / `mall_refunds` |
| 广告花费 | 获客投放成本 | `ad_costs.cost_amount` |

**GMV、充值收入、钱包消费、退款不是同一指标。** 口径见后续 `metric-definitions.md`（Stage 2 后补全计算 SQL）。

## 5. 玩家分层（数据生成约束，非独立表）

| 分层 | 大致占比 | 特征 |
|---|---:|---|
| 免费玩家 | ~70% | 无成功充值或极低活跃付费 |
| 小额付费 | ~20% | 累计充值较低、偶发购买 |
| 中额付费 | ~8% | 稳定月充、中高活跃 |
| 高额付费 | ~2% | 高 ARPPU、高等级、优先客服 |

等级与在线时长正相关；高付费玩家客服优先级可更高；渠道 CAC、转化率、付费质量存在差异。

## 6. 六大业务域一览

| Schema | 中文名 | 职责边界 |
|---|---|---|
| `identity` | 身份域 | 玩家、账号、设备、标签、注册来源 |
| `game` | 游戏运营域 | 游戏、区服、角色、会话、任务、战斗、道具定义、行为事件 |
| `mall` | 商城域 | 商品、订单、退款、道具发放 |
| `payment` | 支付充值域 | 渠道、充值套餐/订单、支付流水、钱包与账本、退款 |
| `support` | 客服域 | 坐席、工单、消息、分配、结案、满意度 |
| `marketing` | 运营推广域 | 推广渠道、活动、投放成本、归因、参与、奖励 |

域内高内聚；跨域通过稳定业务主键（尤其 `player_id`）与必要外键/桥接表连接，**不把所有表直接挂到 players**。
