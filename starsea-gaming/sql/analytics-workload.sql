-- StarSea Gaming analytics workload (Stage 6)
-- Run: psql ... -v ON_ERROR_STOP=1 -f sql/analytics-workload.sql
-- Each section prints a label then a result set.

\echo '=== Q01 DAU ==='
WITH as_of AS (SELECT max(login_at::date) AS d FROM game.player_sessions)
SELECT a.d AS as_of_date, count(DISTINCT s.player_id) AS dau
FROM game.player_sessions s CROSS JOIN as_of a
WHERE s.login_at::date = a.d
GROUP BY a.d;

\echo '=== Q02 WAU MAU ==='
WITH as_of AS (SELECT max(login_at::date) AS d FROM game.player_sessions)
SELECT
  (SELECT count(DISTINCT player_id) FROM game.player_sessions s, as_of a
    WHERE s.login_at::date > a.d - 7 AND s.login_at::date <= a.d) AS wau_7d,
  (SELECT count(DISTINCT player_id) FROM game.player_sessions s, as_of a
    WHERE s.login_at::date > a.d - 30 AND s.login_at::date <= a.d) AS mau_30d;

\echo '=== Q03 new players last 30d by day (sample 10) ==='
WITH as_of AS (SELECT max(login_at::date) AS d FROM game.player_sessions)
SELECT p.register_time::date AS reg_date, count(*) AS new_players
FROM identity.players p, as_of a
WHERE p.register_time::date > a.d - 30 AND p.register_time::date <= a.d
GROUP BY 1 ORDER BY 1 DESC LIMIT 10;

\echo '=== Q04 level distribution ==='
SELECT
  CASE
    WHEN level BETWEEN 1 AND 20 THEN '01-20'
    WHEN level BETWEEN 21 AND 40 THEN '21-40'
    WHEN level BETWEEN 41 AND 60 THEN '41-60'
    WHEN level BETWEEN 61 AND 80 THEN '61-80'
    ELSE '81-100'
  END AS level_bucket,
  count(*) AS characters
FROM game.characters
GROUP BY 1 ORDER BY 1;

\echo '=== Q05 avg session seconds ==='
SELECT round(avg(duration_seconds)::numeric, 2) AS avg_session_seconds
FROM game.player_sessions WHERE duration_seconds IS NOT NULL;

\echo '=== Q06 mission completion rate ==='
SELECT
  count(*) FILTER (WHERE status = 'completed') AS completed,
  count(*) AS total,
  round(count(*) FILTER (WHERE status = 'completed')::numeric / nullif(count(*),0), 4) AS completion_rate
FROM game.mission_records;

\echo '=== Q07 MAU by game ==='
WITH as_of AS (SELECT max(login_at::date) AS d FROM game.player_sessions)
SELECT g.game_code, count(DISTINCT s.player_id) AS mau_30d
FROM game.player_sessions s
JOIN game.games g ON g.game_id = s.game_id
CROSS JOIN as_of a
WHERE s.login_at::date > a.d - 30 AND s.login_at::date <= a.d
GROUP BY 1 ORDER BY 1;

\echo '=== Q08 mall GMV by currency ==='
SELECT price_currency,
       sum(paid_amount) AS gmv
FROM mall.mall_orders
WHERE status IN ('paid','delivered','refunded','partial_refunded')
GROUP BY 1 ORDER BY 1;

\echo '=== Q09 product sales top 10 ==='
SELECT p.product_code, p.product_name, sum(i.quantity) AS units, sum(i.line_amount) AS amount
FROM mall.mall_order_items i
JOIN mall.products p ON p.product_id = i.product_id
JOIN mall.mall_orders o ON o.mall_order_id = i.mall_order_id
WHERE o.status IN ('paid','delivered','refunded','partial_refunded')
GROUP BY 1,2 ORDER BY units DESC LIMIT 10;

\echo '=== Q10 category diamond sales ==='
SELECT c.category_name, sum(i.line_amount) AS diamond_amount
FROM mall.mall_order_items i
JOIN mall.products p ON p.product_id = i.product_id
JOIN mall.product_categories c ON c.category_id = p.category_id
JOIN mall.mall_orders o ON o.mall_order_id = i.mall_order_id
WHERE o.price_currency = 'DIAMOND'
  AND o.status IN ('paid','delivered','refunded','partial_refunded')
GROUP BY 1 ORDER BY 2 DESC;

\echo '=== Q11 mall refund rate ==='
SELECT
  count(DISTINCT o.mall_order_id) FILTER (
    WHERE o.status IN ('paid','delivered','refunded','partial_refunded')) AS paid_orders,
  count(DISTINCT r.mall_order_id) AS refunded_orders,
  round(
    count(DISTINCT r.mall_order_id)::numeric /
    nullif(count(DISTINCT o.mall_order_id) FILTER (
      WHERE o.status IN ('paid','delivered','refunded','partial_refunded')), 0), 4
  ) AS refund_rate
FROM mall.mall_orders o
LEFT JOIN mall.mall_refunds r ON r.mall_order_id = o.mall_order_id AND r.status = 'completed';

\echo '=== Q12 mall conversion among recent active players ==='
WITH as_of AS (SELECT max(login_at::date) AS d FROM game.player_sessions),
active AS (
  SELECT DISTINCT s.player_id
  FROM game.player_sessions s, as_of a
  WHERE s.login_at::date > a.d - 30 AND s.login_at::date <= a.d
),
buyers AS (
  SELECT DISTINCT player_id FROM mall.mall_orders
  WHERE status IN ('paid','delivered','refunded','partial_refunded')
)
SELECT count(*) AS active_players,
       count(*) FILTER (WHERE b.player_id IS NOT NULL) AS mall_buyers,
       round(count(*) FILTER (WHERE b.player_id IS NOT NULL)::numeric / nullif(count(*),0), 4) AS conversion_rate
FROM active a LEFT JOIN buyers b ON b.player_id = a.player_id;

\echo '=== Q13 recharge success amount ==='
SELECT sum(order_amount) AS recharge_success_cny
FROM payment.recharge_orders WHERE status = 'success';

\echo '=== Q14 recharge success rate ==='
SELECT
  count(*) FILTER (WHERE status IN ('success','refunded','partial_refunded')) AS success_like,
  count(*) AS total,
  round(count(*) FILTER (WHERE status IN ('success','refunded','partial_refunded'))::numeric
        / nullif(count(*),0), 4) AS success_rate
FROM payment.recharge_orders;

\echo '=== Q15 ARPU ARPPU ==='
WITH pay AS (
  SELECT player_id, sum(order_amount) AS amt
  FROM payment.recharge_orders WHERE status = 'success'
  GROUP BY 1
),
tot AS (SELECT count(*) AS players FROM identity.players)
SELECT
  round((SELECT coalesce(sum(amt),0) FROM pay) / nullif((SELECT players FROM tot),0), 2) AS arpu,
  round((SELECT coalesce(sum(amt),0) FROM pay) / nullif((SELECT count(*) FROM pay),0), 2) AS arppu;

\echo '=== Q16 pay rate ==='
SELECT round(
  (SELECT count(DISTINCT player_id) FROM payment.recharge_orders WHERE status='success')::numeric
  / nullif((SELECT count(*) FROM identity.players),0), 4
) AS pay_rate;

\echo '=== Q17 recharge amount distribution ==='
SELECT order_amount, count(*) AS orders
FROM payment.recharge_orders WHERE status = 'success'
GROUP BY 1 ORDER BY 1;

\echo '=== Q18 payment channel success ==='
SELECT c.channel_code, count(*) AS txns, sum(t.paid_amount) AS paid_cny
FROM payment.payment_transactions t
JOIN payment.payment_channels c ON c.payment_channel_id = t.payment_channel_id
WHERE t.status = 'success'
GROUP BY 1 ORDER BY paid_cny DESC;

\echo '=== Q19 top 20 cumulative recharge players ==='
SELECT p.nickname, p.player_type, sum(o.order_amount) AS recharge_cny
FROM payment.recharge_orders o
JOIN identity.players p ON p.player_id = o.player_id
WHERE o.status = 'success'
GROUP BY 1,2 ORDER BY recharge_cny DESC LIMIT 20;

\echo '=== Q20 ticket volume and resolve rate ==='
SELECT count(*) AS tickets,
       round(count(*) FILTER (WHERE status IN ('resolved','closed'))::numeric / nullif(count(*),0), 4) AS resolve_rate
FROM support.tickets;

\echo '=== Q21 avg handle hours ==='
SELECT round(avg(extract(epoch FROM (closed_at - opened_at))/3600.0)::numeric, 2) AS avg_handle_hours
FROM support.tickets WHERE closed_at IS NOT NULL;

\echo '=== Q22 avg csat ==='
SELECT round(avg(score)::numeric, 2) AS avg_csat FROM support.customer_satisfaction;

\echo '=== Q23 recharge ticket share ==='
SELECT round(
  count(*) FILTER (WHERE c.category_code = 'recharge_missing')::numeric / nullif(count(*),0), 4
) AS recharge_ticket_share
FROM support.tickets t
JOIN support.ticket_categories c ON c.category_id = t.category_id;

\echo '=== Q24 whale complaint rate ==='
SELECT round(
  count(DISTINCT t.player_id)::numeric / nullif((SELECT count(*) FROM identity.players WHERE player_type='whale'),0), 4
) AS whale_complaint_rate
FROM support.tickets t
JOIN identity.players p ON p.player_id = t.player_id
WHERE p.player_type = 'whale';

\echo '=== Q25 tickets by game via character ==='
SELECT g.game_code, count(*) AS tickets
FROM support.tickets t
JOIN game.characters ch ON ch.character_id = t.character_id
JOIN game.games g ON g.game_id = ch.game_id
GROUP BY 1 ORDER BY 2 DESC;

\echo '=== Q26 first_touch new players by channel ==='
SELECT mc.channel_code, count(DISTINCT a.player_id) AS new_players
FROM marketing.player_attributions a
JOIN marketing.marketing_channels mc ON mc.marketing_channel_id = a.marketing_channel_id
WHERE a.attribution_type = 'first_touch'
GROUP BY 1 ORDER BY 2 DESC;

\echo '=== Q27 CAC by channel ==='
WITH cost AS (
  SELECT marketing_channel_id, sum(cost_amount) AS cost_cny
  FROM marketing.ad_costs
  GROUP BY 1
),
acq AS (
  SELECT marketing_channel_id, count(DISTINCT player_id) AS new_players
  FROM marketing.player_attributions
  WHERE attribution_type = 'first_touch'
  GROUP BY 1
)
SELECT mc.channel_code,
       coalesce(c.cost_cny, 0) AS cost_cny,
       coalesce(a.new_players, 0) AS new_players,
       round(coalesce(c.cost_cny, 0) / nullif(a.new_players, 0), 2) AS cac
FROM marketing.marketing_channels mc
LEFT JOIN cost c ON c.marketing_channel_id = mc.marketing_channel_id
LEFT JOIN acq a ON a.marketing_channel_id = mc.marketing_channel_id
ORDER BY cac NULLS LAST;

\echo '=== Q28 campaign participation and conversion ==='
SELECT c.campaign_code,
       count(*) AS participants,
       count(*) FILTER (WHERE p.participation_status = 'converted') AS converted
FROM marketing.campaign_participations p
JOIN marketing.campaigns c ON c.campaign_id = p.campaign_id
GROUP BY 1 ORDER BY participants DESC LIMIT 15;

\echo '=== Q29 channel 30d pay conversion ==='
SELECT mc.channel_code,
       count(DISTINCT a.player_id) AS attributed_players,
       count(DISTINCT o.player_id) AS paid_within_30d,
       round(count(DISTINCT o.player_id)::numeric / nullif(count(DISTINCT a.player_id),0), 4) AS pay_conversion_30d
FROM marketing.player_attributions a
JOIN marketing.marketing_channels mc ON mc.marketing_channel_id = a.marketing_channel_id
JOIN identity.players p ON p.player_id = a.player_id
LEFT JOIN payment.recharge_orders o
  ON o.player_id = a.player_id
 AND o.status = 'success'
 AND o.ordered_at < p.register_time + interval '30 days'
WHERE a.attribution_type = 'first_touch'
GROUP BY 1 ORDER BY pay_conversion_30d DESC;

\echo '=== Q30 channel recharge amount ==='
SELECT mc.channel_code, coalesce(sum(o.order_amount),0) AS recharge_success_cny
FROM marketing.player_attributions a
JOIN marketing.marketing_channels mc ON mc.marketing_channel_id = a.marketing_channel_id
LEFT JOIN payment.recharge_orders o
  ON o.player_id = a.player_id AND o.status = 'success'
WHERE a.attribution_type = 'first_touch'
GROUP BY 1 ORDER BY 2 DESC;

\echo '=== Q31 avg recharge by max character level ==='
WITH lvl AS (
  SELECT player_id, max(level) AS max_level FROM game.characters GROUP BY 1
),
pay AS (
  SELECT player_id, sum(order_amount) AS amt
  FROM payment.recharge_orders WHERE status='success' GROUP BY 1
)
SELECT
  CASE WHEN l.max_level < 30 THEN 'low_<30' WHEN l.max_level < 60 THEN 'mid_30_59' ELSE 'high_60+' END AS level_band,
  count(*) AS players,
  round(avg(coalesce(p.amt,0)), 2) AS avg_recharge_cny
FROM lvl l
LEFT JOIN pay p ON p.player_id = l.player_id
GROUP BY 1 ORDER BY 1;

\echo '=== Q32 whale ticket categories ==='
SELECT c.category_name, count(*) AS tickets
FROM support.tickets t
JOIN identity.players p ON p.player_id = t.player_id
JOIN support.ticket_categories c ON c.category_id = t.category_id
WHERE p.player_type = 'whale'
GROUP BY 1 ORDER BY 2 DESC;

\echo '=== Q33 recharge vs playtime bands ==='
WITH play AS (
  SELECT player_id, sum(total_play_minutes) AS mins FROM game.characters GROUP BY 1
),
pay AS (
  SELECT player_id, sum(order_amount) AS amt
  FROM payment.recharge_orders WHERE status='success' GROUP BY 1
),
banded AS (
  SELECT
    p.player_id,
    ntile(4) OVER (ORDER BY coalesce(pl.mins, 0)) AS playtime_quartile,
    coalesce(py.amt, 0) AS amt
  FROM identity.players p
  LEFT JOIN play pl ON pl.player_id = p.player_id
  LEFT JOIN pay py ON py.player_id = p.player_id
)
SELECT
  playtime_quartile,
  round(avg(amt), 2) AS avg_recharge_cny,
  count(*) AS players
FROM banded
GROUP BY 1
ORDER BY 1;

\echo '=== Q34 whale favorite products ==='
SELECT pr.product_code, pr.product_name, sum(i.quantity) AS units
FROM mall.mall_order_items i
JOIN mall.mall_orders o ON o.mall_order_id = i.mall_order_id
JOIN identity.players p ON p.player_id = o.player_id
JOIN mall.products pr ON pr.product_id = i.product_id
WHERE p.player_type = 'whale'
  AND o.status IN ('paid','delivered','refunded','partial_refunded')
GROUP BY 1,2 ORDER BY units DESC LIMIT 10;

\echo '=== Q35 channel cost vs LTV ==='
WITH first_touch AS (
  SELECT a.player_id, mc.channel_code
  FROM marketing.player_attributions a
  JOIN marketing.marketing_channels mc ON mc.marketing_channel_id = a.marketing_channel_id
  WHERE a.attribution_type = 'first_touch'
),
ltv AS (
  SELECT player_id, sum(order_amount) AS recharge_cny
  FROM payment.recharge_orders WHERE status='success' GROUP BY 1
),
cost AS (
  SELECT mc.channel_code, sum(ac.cost_amount) AS cost_cny
  FROM marketing.ad_costs ac
  JOIN marketing.marketing_channels mc ON mc.marketing_channel_id = ac.marketing_channel_id
  GROUP BY 1
)
SELECT f.channel_code,
       c.cost_cny,
       count(*) AS players,
       round(avg(coalesce(l.recharge_cny,0)), 2) AS avg_ltv_recharge_cny
FROM first_touch f
LEFT JOIN ltv l ON l.player_id = f.player_id
LEFT JOIN cost c ON c.channel_code = f.channel_code
GROUP BY 1,2 ORDER BY c.cost_cny DESC NULLS LAST;
