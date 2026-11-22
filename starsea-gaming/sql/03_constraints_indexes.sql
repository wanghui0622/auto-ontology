-- StarSea Gaming Data Platform
-- Stage 2: foreign keys, indexes, and business COMMENTs

-- ---------------------------------------------------------------------------
-- Foreign keys
-- ---------------------------------------------------------------------------

ALTER TABLE identity.players
    ADD CONSTRAINT fk_players_registration_source
    FOREIGN KEY (registration_source_id)
    REFERENCES identity.registration_sources (registration_source_id);

ALTER TABLE identity.player_accounts
    ADD CONSTRAINT fk_player_accounts_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_player_accounts_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id);

ALTER TABLE identity.player_devices
    ADD CONSTRAINT fk_player_devices_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id);

ALTER TABLE identity.player_tag_relations
    ADD CONSTRAINT fk_player_tag_relations_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_player_tag_relations_tag
    FOREIGN KEY (tag_id) REFERENCES identity.player_tags (tag_id);

ALTER TABLE game.game_servers
    ADD CONSTRAINT fk_game_servers_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id);

ALTER TABLE game.characters
    ADD CONSTRAINT fk_characters_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_characters_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id),
    ADD CONSTRAINT fk_characters_server
    FOREIGN KEY (server_id) REFERENCES game.game_servers (server_id);

ALTER TABLE game.character_attributes
    ADD CONSTRAINT fk_character_attributes_character
    FOREIGN KEY (character_id) REFERENCES game.characters (character_id);

ALTER TABLE game.player_sessions
    ADD CONSTRAINT fk_player_sessions_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_player_sessions_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id),
    ADD CONSTRAINT fk_player_sessions_character
    FOREIGN KEY (character_id) REFERENCES game.characters (character_id);

ALTER TABLE game.game_events
    ADD CONSTRAINT fk_game_events_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_game_events_character
    FOREIGN KEY (character_id) REFERENCES game.characters (character_id),
    ADD CONSTRAINT fk_game_events_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id);

ALTER TABLE game.missions
    ADD CONSTRAINT fk_missions_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id);

ALTER TABLE game.mission_records
    ADD CONSTRAINT fk_mission_records_mission
    FOREIGN KEY (mission_id) REFERENCES game.missions (mission_id),
    ADD CONSTRAINT fk_mission_records_character
    FOREIGN KEY (character_id) REFERENCES game.characters (character_id);

ALTER TABLE game.battles
    ADD CONSTRAINT fk_battles_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id),
    ADD CONSTRAINT fk_battles_server
    FOREIGN KEY (server_id) REFERENCES game.game_servers (server_id);

ALTER TABLE game.battle_participants
    ADD CONSTRAINT fk_battle_participants_battle
    FOREIGN KEY (battle_id) REFERENCES game.battles (battle_id),
    ADD CONSTRAINT fk_battle_participants_character
    FOREIGN KEY (character_id) REFERENCES game.characters (character_id);

ALTER TABLE game.game_items
    ADD CONSTRAINT fk_game_items_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id);

ALTER TABLE mall.product_categories
    ADD CONSTRAINT fk_product_categories_parent
    FOREIGN KEY (parent_category_id)
    REFERENCES mall.product_categories (category_id);

ALTER TABLE mall.products
    ADD CONSTRAINT fk_products_category
    FOREIGN KEY (category_id) REFERENCES mall.product_categories (category_id),
    ADD CONSTRAINT fk_products_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id);

ALTER TABLE mall.product_items
    ADD CONSTRAINT fk_product_items_product
    FOREIGN KEY (product_id) REFERENCES mall.products (product_id),
    ADD CONSTRAINT fk_product_items_game_item
    FOREIGN KEY (game_item_id) REFERENCES game.game_items (game_item_id);

ALTER TABLE mall.mall_orders
    ADD CONSTRAINT fk_mall_orders_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_mall_orders_character
    FOREIGN KEY (character_id) REFERENCES game.characters (character_id),
    ADD CONSTRAINT fk_mall_orders_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id);

ALTER TABLE mall.mall_order_items
    ADD CONSTRAINT fk_mall_order_items_order
    FOREIGN KEY (mall_order_id) REFERENCES mall.mall_orders (mall_order_id),
    ADD CONSTRAINT fk_mall_order_items_product
    FOREIGN KEY (product_id) REFERENCES mall.products (product_id);

ALTER TABLE mall.mall_refunds
    ADD CONSTRAINT fk_mall_refunds_order
    FOREIGN KEY (mall_order_id) REFERENCES mall.mall_orders (mall_order_id);

ALTER TABLE mall.item_delivery_records
    ADD CONSTRAINT fk_item_delivery_order
    FOREIGN KEY (mall_order_id) REFERENCES mall.mall_orders (mall_order_id),
    ADD CONSTRAINT fk_item_delivery_order_item
    FOREIGN KEY (mall_order_item_id) REFERENCES mall.mall_order_items (mall_order_item_id),
    ADD CONSTRAINT fk_item_delivery_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_item_delivery_character
    FOREIGN KEY (character_id) REFERENCES game.characters (character_id),
    ADD CONSTRAINT fk_item_delivery_game_item
    FOREIGN KEY (game_item_id) REFERENCES game.game_items (game_item_id);

ALTER TABLE payment.recharge_products
    ADD CONSTRAINT fk_recharge_products_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id);

ALTER TABLE payment.recharge_orders
    ADD CONSTRAINT fk_recharge_orders_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_recharge_orders_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id),
    ADD CONSTRAINT fk_recharge_orders_product
    FOREIGN KEY (recharge_product_id)
    REFERENCES payment.recharge_products (recharge_product_id);

ALTER TABLE payment.payment_transactions
    ADD CONSTRAINT fk_payment_transactions_order
    FOREIGN KEY (recharge_order_id)
    REFERENCES payment.recharge_orders (recharge_order_id),
    ADD CONSTRAINT fk_payment_transactions_channel
    FOREIGN KEY (payment_channel_id)
    REFERENCES payment.payment_channels (payment_channel_id);

ALTER TABLE payment.payment_refunds
    ADD CONSTRAINT fk_payment_refunds_order
    FOREIGN KEY (recharge_order_id)
    REFERENCES payment.recharge_orders (recharge_order_id),
    ADD CONSTRAINT fk_payment_refunds_txn
    FOREIGN KEY (payment_transaction_id)
    REFERENCES payment.payment_transactions (payment_transaction_id);

ALTER TABLE payment.wallets
    ADD CONSTRAINT fk_wallets_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id);

ALTER TABLE payment.wallet_ledgers
    ADD CONSTRAINT fk_wallet_ledgers_wallet
    FOREIGN KEY (wallet_id) REFERENCES payment.wallets (wallet_id),
    ADD CONSTRAINT fk_wallet_ledgers_recharge_order
    FOREIGN KEY (recharge_order_id)
    REFERENCES payment.recharge_orders (recharge_order_id),
    ADD CONSTRAINT fk_wallet_ledgers_mall_order
    FOREIGN KEY (mall_order_id) REFERENCES mall.mall_orders (mall_order_id);

-- campaign_reward FK added after marketing.campaign_rewards exists (below)

ALTER TABLE support.tickets
    ADD CONSTRAINT fk_tickets_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_tickets_category
    FOREIGN KEY (category_id) REFERENCES support.ticket_categories (category_id),
    ADD CONSTRAINT fk_tickets_character
    FOREIGN KEY (character_id) REFERENCES game.characters (character_id),
    ADD CONSTRAINT fk_tickets_recharge_order
    FOREIGN KEY (recharge_order_id)
    REFERENCES payment.recharge_orders (recharge_order_id),
    ADD CONSTRAINT fk_tickets_mall_order
    FOREIGN KEY (mall_order_id) REFERENCES mall.mall_orders (mall_order_id);

ALTER TABLE support.ticket_messages
    ADD CONSTRAINT fk_ticket_messages_ticket
    FOREIGN KEY (ticket_id) REFERENCES support.tickets (ticket_id),
    ADD CONSTRAINT fk_ticket_messages_player
    FOREIGN KEY (sender_player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_ticket_messages_agent
    FOREIGN KEY (sender_agent_id) REFERENCES support.agents (agent_id);

ALTER TABLE support.ticket_assignments
    ADD CONSTRAINT fk_ticket_assignments_ticket
    FOREIGN KEY (ticket_id) REFERENCES support.tickets (ticket_id),
    ADD CONSTRAINT fk_ticket_assignments_agent
    FOREIGN KEY (agent_id) REFERENCES support.agents (agent_id);

ALTER TABLE support.ticket_resolution_records
    ADD CONSTRAINT fk_ticket_resolution_ticket
    FOREIGN KEY (ticket_id) REFERENCES support.tickets (ticket_id),
    ADD CONSTRAINT fk_ticket_resolution_agent
    FOREIGN KEY (resolved_by_agent_id) REFERENCES support.agents (agent_id);

ALTER TABLE support.customer_satisfaction
    ADD CONSTRAINT fk_csat_ticket
    FOREIGN KEY (ticket_id) REFERENCES support.tickets (ticket_id),
    ADD CONSTRAINT fk_csat_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id);

ALTER TABLE marketing.campaigns
    ADD CONSTRAINT fk_campaigns_game
    FOREIGN KEY (game_id) REFERENCES game.games (game_id);

ALTER TABLE marketing.campaign_channels
    ADD CONSTRAINT fk_campaign_channels_campaign
    FOREIGN KEY (campaign_id) REFERENCES marketing.campaigns (campaign_id),
    ADD CONSTRAINT fk_campaign_channels_channel
    FOREIGN KEY (marketing_channel_id)
    REFERENCES marketing.marketing_channels (marketing_channel_id);

ALTER TABLE marketing.ad_costs
    ADD CONSTRAINT fk_ad_costs_channel
    FOREIGN KEY (marketing_channel_id)
    REFERENCES marketing.marketing_channels (marketing_channel_id),
    ADD CONSTRAINT fk_ad_costs_campaign
    FOREIGN KEY (campaign_id) REFERENCES marketing.campaigns (campaign_id);

ALTER TABLE marketing.player_attributions
    ADD CONSTRAINT fk_player_attributions_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_player_attributions_channel
    FOREIGN KEY (marketing_channel_id)
    REFERENCES marketing.marketing_channels (marketing_channel_id),
    ADD CONSTRAINT fk_player_attributions_campaign
    FOREIGN KEY (campaign_id) REFERENCES marketing.campaigns (campaign_id);

ALTER TABLE marketing.campaign_participations
    ADD CONSTRAINT fk_campaign_participations_campaign
    FOREIGN KEY (campaign_id) REFERENCES marketing.campaigns (campaign_id),
    ADD CONSTRAINT fk_campaign_participations_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_campaign_participations_character
    FOREIGN KEY (character_id) REFERENCES game.characters (character_id),
    ADD CONSTRAINT fk_campaign_participations_recharge
    FOREIGN KEY (converted_recharge_order_id)
    REFERENCES payment.recharge_orders (recharge_order_id);

ALTER TABLE marketing.campaign_rewards
    ADD CONSTRAINT fk_campaign_rewards_participation
    FOREIGN KEY (participation_id)
    REFERENCES marketing.campaign_participations (participation_id),
    ADD CONSTRAINT fk_campaign_rewards_player
    FOREIGN KEY (player_id) REFERENCES identity.players (player_id),
    ADD CONSTRAINT fk_campaign_rewards_item
    FOREIGN KEY (game_item_id) REFERENCES game.game_items (game_item_id);

ALTER TABLE payment.wallet_ledgers
    ADD CONSTRAINT fk_wallet_ledgers_campaign_reward
    FOREIGN KEY (campaign_reward_id)
    REFERENCES marketing.campaign_rewards (campaign_reward_id);

ALTER TABLE support.tickets
    ADD CONSTRAINT fk_tickets_campaign
    FOREIGN KEY (campaign_id) REFERENCES marketing.campaigns (campaign_id);

-- ---------------------------------------------------------------------------
-- Indexes (non-PK / non-unique-constraint helpers)
-- ---------------------------------------------------------------------------

CREATE INDEX idx_players_register_time ON identity.players (register_time);
CREATE INDEX idx_players_status_type ON identity.players (status, player_type);
CREATE INDEX idx_players_registration_source ON identity.players (registration_source_id);

CREATE INDEX idx_player_accounts_player ON identity.player_accounts (player_id);
CREATE INDEX idx_player_devices_player ON identity.player_devices (player_id);

CREATE INDEX idx_characters_player ON game.characters (player_id);
CREATE INDEX idx_characters_game_server ON game.characters (game_id, server_id);
CREATE INDEX idx_characters_level ON game.characters (level);

CREATE INDEX idx_player_sessions_player_login ON game.player_sessions (player_id, login_at);
CREATE INDEX idx_player_sessions_game_login ON game.player_sessions (game_id, login_at);
CREATE INDEX idx_game_events_player_time ON game.game_events (player_id, event_time);
CREATE INDEX idx_game_events_type_time ON game.game_events (event_type, event_time);
CREATE INDEX idx_mission_records_character ON game.mission_records (character_id, status);
CREATE INDEX idx_battle_participants_character ON game.battle_participants (character_id);

CREATE INDEX idx_products_category ON mall.products (category_id);
CREATE INDEX idx_products_game_currency ON mall.products (game_id, price_currency);
CREATE INDEX idx_mall_orders_player_ordered ON mall.mall_orders (player_id, ordered_at);
CREATE INDEX idx_mall_orders_status_ordered ON mall.mall_orders (status, ordered_at);
CREATE INDEX idx_mall_order_items_order ON mall.mall_order_items (mall_order_id);
CREATE INDEX idx_mall_refunds_order ON mall.mall_refunds (mall_order_id);
CREATE INDEX idx_item_delivery_order ON mall.item_delivery_records (mall_order_id);
CREATE INDEX idx_item_delivery_player ON mall.item_delivery_records (player_id);

CREATE INDEX idx_recharge_orders_player_ordered
    ON payment.recharge_orders (player_id, ordered_at);
CREATE INDEX idx_recharge_orders_status_ordered
    ON payment.recharge_orders (status, ordered_at);
CREATE INDEX idx_payment_transactions_order
    ON payment.payment_transactions (recharge_order_id);
CREATE INDEX idx_payment_transactions_channel_status
    ON payment.payment_transactions (payment_channel_id, status);
CREATE INDEX idx_payment_refunds_order ON payment.payment_refunds (recharge_order_id);
CREATE INDEX idx_wallets_player ON payment.wallets (player_id);
CREATE INDEX idx_wallet_ledgers_wallet_time ON payment.wallet_ledgers (wallet_id, occurred_at);
CREATE INDEX idx_wallet_ledgers_entry_type ON payment.wallet_ledgers (entry_type);
CREATE INDEX idx_wallet_ledgers_recharge ON payment.wallet_ledgers (recharge_order_id);
CREATE INDEX idx_wallet_ledgers_mall ON payment.wallet_ledgers (mall_order_id);

CREATE INDEX idx_tickets_player_opened ON support.tickets (player_id, opened_at);
CREATE INDEX idx_tickets_category_status ON support.tickets (category_id, status);
CREATE INDEX idx_tickets_recharge ON support.tickets (recharge_order_id);
CREATE INDEX idx_tickets_mall ON support.tickets (mall_order_id);
CREATE INDEX idx_ticket_messages_ticket_sent ON support.ticket_messages (ticket_id, sent_at);
CREATE INDEX idx_ticket_assignments_agent ON support.ticket_assignments (agent_id, assigned_at);

CREATE INDEX idx_ad_costs_channel_date ON marketing.ad_costs (marketing_channel_id, cost_date);
CREATE INDEX idx_ad_costs_campaign_date ON marketing.ad_costs (campaign_id, cost_date);
CREATE INDEX idx_player_attributions_player_type
    ON marketing.player_attributions (player_id, attribution_type);
CREATE INDEX idx_player_attributions_channel_type
    ON marketing.player_attributions (marketing_channel_id, attribution_type);
CREATE INDEX idx_campaign_participations_player
    ON marketing.campaign_participations (player_id, joined_at);
CREATE INDEX idx_campaign_participations_campaign
    ON marketing.campaign_participations (campaign_id, participation_status);
CREATE INDEX idx_campaign_rewards_player ON marketing.campaign_rewards (player_id);

-- ---------------------------------------------------------------------------
-- Table comments
-- ---------------------------------------------------------------------------

COMMENT ON TABLE identity.registration_sources IS '玩家注册来源字典，与营销推广渠道编码对齐但职责分离';
COMMENT ON TABLE identity.players IS '跨业务域统一玩家实体（亦可称用户/账号持有人，同体不同口径）';
COMMENT ON TABLE identity.player_accounts IS '玩家在具体游戏下的登录账号，一玩家可拥有多个游戏账号';
COMMENT ON TABLE identity.player_devices IS '玩家设备信息与首次/最近出现时间';
COMMENT ON TABLE identity.player_tags IS '玩家运营标签字典';
COMMENT ON TABLE identity.player_tag_relations IS '玩家与标签多对多关联桥接表';

COMMENT ON TABLE game.games IS '游戏主数据，当前包含星海纪元与星海远征';
COMMENT ON TABLE game.game_servers IS '游戏区服';
COMMENT ON TABLE game.characters IS '游戏角色，隶属于一个玩家、一个游戏和一个区服';
COMMENT ON TABLE game.character_attributes IS '角色可变属性键值（如职业、阵营、基地等级）';
COMMENT ON TABLE game.player_sessions IS '玩家登录与在线会话记录';
COMMENT ON TABLE game.game_events IS '游戏行为事件流';
COMMENT ON TABLE game.missions IS '游戏任务定义';
COMMENT ON TABLE game.mission_records IS '角色任务完成与进度记录';
COMMENT ON TABLE game.battles IS '战斗/副本/战役场次';
COMMENT ON TABLE game.battle_participants IS '战斗参与者桥接表';
COMMENT ON TABLE game.game_items IS '游戏道具定义，供商城捆绑与发放引用';

COMMENT ON TABLE mall.product_categories IS '商城商品分类';
COMMENT ON TABLE mall.products IS '可售商品，支持人民币或钻石两种计价体系';
COMMENT ON TABLE mall.product_items IS '商品包含的游戏道具及数量';
COMMENT ON TABLE mall.mall_orders IS '商城订单头，可追溯购买玩家；GMV 统计以此为准而非充值收入';
COMMENT ON TABLE mall.mall_order_items IS '商城订单明细';
COMMENT ON TABLE mall.mall_refunds IS '商城退款记录，需关联原始商城订单';
COMMENT ON TABLE mall.item_delivery_records IS '购买成功后的道具发放记录';

COMMENT ON TABLE payment.payment_channels IS '支付收款渠道（支付宝/微信/应用商店等），与推广获客渠道不同';
COMMENT ON TABLE payment.recharge_products IS '充值套餐：人民币标价对应到账钻石数量';
COMMENT ON TABLE payment.recharge_orders IS '玩家充值订单；order_amount 为套餐标价，不等于渠道实付或商城消费';
COMMENT ON TABLE payment.payment_transactions IS '支付渠道交易流水；paid_amount 为实际支付金额';
COMMENT ON TABLE payment.payment_refunds IS '充值退款，关联原始充值订单与支付交易';
COMMENT ON TABLE payment.wallets IS '玩家虚拟钱包余额（钻石），一玩家一币种一行';
COMMENT ON TABLE payment.wallet_ledgers IS '钱包变动流水，余额应可通过流水核对';

COMMENT ON TABLE support.agents IS '客服坐席人员';
COMMENT ON TABLE support.ticket_categories IS '客服工单分类（玩法/账号/充值/商城/退款/BUG/活动/申诉等）';
COMMENT ON TABLE support.tickets IS '客服工单，可挂载角色、充值单、商城单或活动';
COMMENT ON TABLE support.ticket_messages IS '工单会话消息，含真实业务语义文本';
COMMENT ON TABLE support.ticket_assignments IS '工单分配历史，支持多次改派';
COMMENT ON TABLE support.ticket_resolution_records IS '工单结案结果';
COMMENT ON TABLE support.customer_satisfaction IS '玩家对工单处理的满意度评价';

COMMENT ON TABLE marketing.marketing_channels IS '推广获客渠道字典';
COMMENT ON TABLE marketing.campaigns IS '营销/运营活动';
COMMENT ON TABLE marketing.campaign_channels IS '活动与推广渠道多对多桥接表';
COMMENT ON TABLE marketing.ad_costs IS '广告投放成本明细（渠道/活动/日粒度）';
COMMENT ON TABLE marketing.player_attributions IS '玩家渠道归因，区分 first_touch/last_touch/campaign_conversion';
COMMENT ON TABLE marketing.campaign_participations IS '玩家活动参与记录，可关联转化充值订单';
COMMENT ON TABLE marketing.campaign_rewards IS '活动奖励发放记录';

-- Key column comments (money / identity / attribution)
COMMENT ON COLUMN identity.players.player_id IS '统一玩家主键，跨六大业务域引用';
COMMENT ON COLUMN identity.players.player_type IS '付费分层：free/light_payer/mid_payer/whale';
COMMENT ON COLUMN identity.players.register_channel IS '注册渠道展示名；结构化归因以 marketing.player_attributions 为准';

COMMENT ON COLUMN mall.products.price_currency IS '计价币种：CNY=人民币直购，DIAMOND=钻石钱包扣款';
COMMENT ON COLUMN mall.mall_orders.payable_amount IS '商城订单应付金额（按 price_currency）';
COMMENT ON COLUMN mall.mall_orders.paid_amount IS '商城订单实付金额，不等于充值收入';

COMMENT ON COLUMN payment.recharge_orders.order_amount IS '充值订单套餐标价（人民币）';
COMMENT ON COLUMN payment.recharge_orders.credit_currency_amount IS '充值成功后到账的虚拟货币数量（钻石）';
COMMENT ON COLUMN payment.payment_transactions.paid_amount IS '支付渠道实际收款金额（人民币）';
COMMENT ON COLUMN payment.wallets.balance IS '当前可用钻石余额，应等于对应钱包流水 change_amount 之和';
COMMENT ON COLUMN payment.wallet_ledgers.change_amount IS '账变金额，正数为入账，负数为出账';
COMMENT ON COLUMN payment.wallet_ledgers.entry_type IS '账变类型：充值入账/商城扣款/商城退款/充值退款扣回/活动奖励/调账';

COMMENT ON COLUMN marketing.player_attributions.attribution_type IS '归因口径：first_touch=首次注册，last_touch=最近触点，campaign_conversion=活动转化';
COMMENT ON COLUMN marketing.ad_costs.cost_amount IS '广告投放成本（人民币），用于 CAC/ROI，不是玩家付费';
