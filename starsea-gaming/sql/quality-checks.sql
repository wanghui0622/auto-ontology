-- Stage 4 manual / CI-friendly quality probes (read-only).

-- Scale sample
SELECT 'players' AS metric, count(*)::text AS value FROM identity.players
UNION ALL
SELECT 'wallet_mismatches', count(*)::text FROM (
  SELECT w.wallet_id
  FROM payment.wallets w
  LEFT JOIN payment.wallet_ledgers l ON l.wallet_id = w.wallet_id
  GROUP BY w.wallet_id, w.balance
  HAVING w.balance <> COALESCE(SUM(l.change_amount), 0)
) s
UNION ALL
SELECT 'missing_first_touch', count(*)::text
FROM identity.players p
WHERE NOT EXISTS (
  SELECT 1 FROM marketing.player_attributions a
  WHERE a.player_id = p.player_id AND a.attribution_type = 'first_touch'
);

-- DAU/WAU/MAU on max session date
WITH as_of AS (
  SELECT max(login_at::date) AS d FROM game.player_sessions
)
SELECT
  (SELECT d FROM as_of) AS as_of_date,
  (SELECT count(DISTINCT player_id) FROM game.player_sessions s, as_of a
    WHERE s.login_at::date = a.d) AS dau,
  (SELECT count(DISTINCT player_id) FROM game.player_sessions s, as_of a
    WHERE s.login_at::date > a.d - 7 AND s.login_at::date <= a.d) AS wau,
  (SELECT count(DISTINCT player_id) FROM game.player_sessions s, as_of a
    WHERE s.login_at::date > a.d - 30 AND s.login_at::date <= a.d) AS mau;
