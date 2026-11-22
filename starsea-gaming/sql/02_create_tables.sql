-- StarSea Gaming Data Platform
-- Stage 2: tables (PK / NOT NULL / UNIQUE / CHECK). Foreign keys in 03_*.

-- ---------------------------------------------------------------------------
-- identity
-- ---------------------------------------------------------------------------

CREATE TABLE identity.registration_sources (
    registration_source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_code            TEXT NOT NULL,
    source_name            TEXT NOT NULL,
    source_type            TEXT NOT NULL,
    description            TEXT,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_registration_sources_code UNIQUE (source_code),
    CONSTRAINT ck_registration_sources_type CHECK (
        source_type IN (
            'official_website', 'app_store', 'feed_ads', 'short_video',
            'community', 'kol', 'affiliate', 'organic', 'other'
        )
    )
);

CREATE TABLE identity.players (
    player_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nickname               TEXT NOT NULL,
    register_time          TIMESTAMPTZ NOT NULL,
    register_channel       TEXT NOT NULL,
    registration_source_id UUID NOT NULL,
    country                CHAR(2) NOT NULL,
    status                 TEXT NOT NULL DEFAULT 'active',
    player_type            TEXT NOT NULL DEFAULT 'free',
    vip_level              INTEGER NOT NULL DEFAULT 0,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_players_status CHECK (
        status IN ('active', 'banned', 'churned', 'deleted')
    ),
    CONSTRAINT ck_players_type CHECK (
        player_type IN ('free', 'light_payer', 'mid_payer', 'whale')
    ),
    CONSTRAINT ck_players_vip_level CHECK (vip_level BETWEEN 0 AND 10)
);

CREATE TABLE identity.player_accounts (
    account_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id      UUID NOT NULL,
    game_id        UUID NOT NULL,
    account_name   TEXT NOT NULL,
    account_status TEXT NOT NULL DEFAULT 'active',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_player_accounts_name UNIQUE (account_name),
    CONSTRAINT uq_player_accounts_player_game UNIQUE (player_id, game_id),
    CONSTRAINT ck_player_accounts_status CHECK (
        account_status IN ('active', 'locked', 'deleted')
    )
);

CREATE TABLE identity.player_devices (
    device_record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id        UUID NOT NULL,
    device_id        TEXT NOT NULL,
    device_os        TEXT NOT NULL,
    device_model     TEXT,
    first_seen_at    TIMESTAMPTZ NOT NULL,
    last_seen_at     TIMESTAMPTZ NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_player_devices_player_device UNIQUE (player_id, device_id),
    CONSTRAINT ck_player_devices_os CHECK (
        device_os IN ('ios', 'android', 'windows', 'macos', 'other')
    ),
    CONSTRAINT ck_player_devices_seen CHECK (last_seen_at >= first_seen_at)
);

CREATE TABLE identity.player_tags (
    tag_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_code     TEXT NOT NULL,
    tag_name     TEXT NOT NULL,
    tag_category TEXT NOT NULL,
    description  TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_player_tags_code UNIQUE (tag_code)
);

CREATE TABLE identity.player_tag_relations (
    player_id  UUID NOT NULL,
    tag_id     UUID NOT NULL,
    tagged_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tagged_by  TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (player_id, tag_id)
);

-- ---------------------------------------------------------------------------
-- game
-- ---------------------------------------------------------------------------

CREATE TABLE game.games (
    game_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_code   TEXT NOT NULL,
    game_name   TEXT NOT NULL,
    genre       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'online',
    launched_at TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_games_code UNIQUE (game_code),
    CONSTRAINT ck_games_genre CHECK (genre IN ('mmorpg', 'strategy', 'other')),
    CONSTRAINT ck_games_status CHECK (status IN ('online', 'maintenance', 'offline'))
);

CREATE TABLE game.game_servers (
    server_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id     UUID NOT NULL,
    server_code TEXT NOT NULL,
    server_name TEXT NOT NULL,
    region      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open',
    opened_at   TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_game_servers_game_code UNIQUE (game_id, server_code),
    CONSTRAINT ck_game_servers_status CHECK (status IN ('open', 'full', 'closed'))
);

CREATE TABLE game.characters (
    character_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id          UUID NOT NULL,
    game_id            UUID NOT NULL,
    server_id          UUID NOT NULL,
    character_name     TEXT NOT NULL,
    level              INTEGER NOT NULL DEFAULT 1,
    combat_power       NUMERIC(14, 2) NOT NULL DEFAULT 0,
    total_play_minutes INTEGER NOT NULL DEFAULT 0,
    last_login_at      TIMESTAMPTZ,
    status             TEXT NOT NULL DEFAULT 'active',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_characters_server_name UNIQUE (server_id, character_name),
    CONSTRAINT ck_characters_level CHECK (level BETWEEN 1 AND 100),
    CONSTRAINT ck_characters_combat CHECK (combat_power >= 0),
    CONSTRAINT ck_characters_play CHECK (total_play_minutes >= 0),
    CONSTRAINT ck_characters_status CHECK (status IN ('active', 'deleted', 'banned'))
);

CREATE TABLE game.character_attributes (
    attribute_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id    UUID NOT NULL,
    attribute_key   TEXT NOT NULL,
    attribute_value TEXT NOT NULL,
    effective_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_character_attributes_key UNIQUE (character_id, attribute_key)
);

CREATE TABLE game.player_sessions (
    session_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id        UUID NOT NULL,
    game_id          UUID NOT NULL,
    character_id     UUID,
    login_at         TIMESTAMPTZ NOT NULL,
    logout_at        TIMESTAMPTZ,
    duration_seconds INTEGER,
    client_version   TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_player_sessions_duration CHECK (
        duration_seconds IS NULL OR duration_seconds >= 0
    ),
    CONSTRAINT ck_player_sessions_logout CHECK (
        logout_at IS NULL OR logout_at >= login_at
    )
);

CREATE TABLE game.game_events (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id     UUID NOT NULL,
    character_id  UUID,
    game_id       UUID NOT NULL,
    event_type    TEXT NOT NULL,
    event_name    TEXT NOT NULL,
    event_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    event_time    TIMESTAMPTZ NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE game.missions (
    mission_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id      UUID NOT NULL,
    mission_code TEXT NOT NULL,
    mission_name TEXT NOT NULL,
    mission_type TEXT NOT NULL,
    min_level    INTEGER NOT NULL DEFAULT 1,
    description  TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_missions_game_code UNIQUE (game_id, mission_code),
    CONSTRAINT ck_missions_type CHECK (
        mission_type IN ('main', 'side', 'daily', 'weekly', 'event')
    ),
    CONSTRAINT ck_missions_min_level CHECK (min_level BETWEEN 1 AND 100)
);

CREATE TABLE game.mission_records (
    mission_record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id        UUID NOT NULL,
    character_id      UUID NOT NULL,
    status            TEXT NOT NULL,
    started_at        TIMESTAMPTZ NOT NULL,
    completed_at      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_mission_records_status CHECK (
        status IN ('in_progress', 'completed', 'failed', 'abandoned')
    ),
    CONSTRAINT ck_mission_records_completed CHECK (
        (status = 'completed' AND completed_at IS NOT NULL)
        OR (status <> 'completed')
    )
);

CREATE TABLE game.battles (
    battle_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id         UUID NOT NULL,
    server_id       UUID NOT NULL,
    battle_type     TEXT NOT NULL,
    result_summary  TEXT,
    started_at      TIMESTAMPTZ NOT NULL,
    ended_at        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_battles_type CHECK (
        battle_type IN ('pve', 'pvp', 'dungeon', 'campaign', 'arena')
    ),
    CONSTRAINT ck_battles_ended CHECK (ended_at IS NULL OR ended_at >= started_at)
);

CREATE TABLE game.battle_participants (
    battle_id     UUID NOT NULL,
    character_id  UUID NOT NULL,
    side          TEXT NOT NULL,
    result        TEXT NOT NULL,
    damage_dealt  NUMERIC(14, 2) NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (battle_id, character_id),
    CONSTRAINT ck_battle_participants_side CHECK (side IN ('attacker', 'defender', 'ally')),
    CONSTRAINT ck_battle_participants_result CHECK (
        result IN ('win', 'lose', 'draw', 'flee')
    ),
    CONSTRAINT ck_battle_participants_damage CHECK (damage_dealt >= 0)
);

CREATE TABLE game.game_items (
    game_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id      UUID NOT NULL,
    item_code    TEXT NOT NULL,
    item_name    TEXT NOT NULL,
    item_type    TEXT NOT NULL,
    rarity       TEXT NOT NULL,
    description  TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_game_items_game_code UNIQUE (game_id, item_code),
    CONSTRAINT ck_game_items_type CHECK (
        item_type IN ('currency_pack', 'consumable', 'equipment', 'cosmetic', 'material', 'other')
    ),
    CONSTRAINT ck_game_items_rarity CHECK (
        rarity IN ('common', 'rare', 'epic', 'legendary')
    )
);

-- ---------------------------------------------------------------------------
-- mall
-- ---------------------------------------------------------------------------

CREATE TABLE mall.product_categories (
    category_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_code      TEXT NOT NULL,
    category_name      TEXT NOT NULL,
    parent_category_id UUID,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_product_categories_code UNIQUE (category_code)
);

CREATE TABLE mall.products (
    product_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id    UUID NOT NULL,
    game_id        UUID NOT NULL,
    product_code   TEXT NOT NULL,
    product_name   TEXT NOT NULL,
    price_currency TEXT NOT NULL,
    list_price     NUMERIC(14, 2) NOT NULL,
    status         TEXT NOT NULL DEFAULT 'on_sale',
    description    TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_products_code UNIQUE (product_code),
    CONSTRAINT ck_products_currency CHECK (price_currency IN ('CNY', 'DIAMOND')),
    CONSTRAINT ck_products_price CHECK (list_price >= 0),
    CONSTRAINT ck_products_status CHECK (status IN ('on_sale', 'off_sale', 'archived'))
);

CREATE TABLE mall.product_items (
    product_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id      UUID NOT NULL,
    game_item_id    UUID NOT NULL,
    quantity        INTEGER NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_product_items_product_item UNIQUE (product_id, game_item_id),
    CONSTRAINT ck_product_items_qty CHECK (quantity > 0)
);

CREATE TABLE mall.mall_orders (
    mall_order_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_no        TEXT NOT NULL,
    player_id       UUID NOT NULL,
    character_id    UUID,
    game_id         UUID NOT NULL,
    price_currency  TEXT NOT NULL,
    payable_amount  NUMERIC(14, 2) NOT NULL,
    paid_amount     NUMERIC(14, 2) NOT NULL DEFAULT 0,
    payment_method  TEXT NOT NULL,
    status          TEXT NOT NULL,
    ordered_at      TIMESTAMPTZ NOT NULL,
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_mall_orders_order_no UNIQUE (order_no),
    CONSTRAINT ck_mall_orders_currency CHECK (price_currency IN ('CNY', 'DIAMOND')),
    CONSTRAINT ck_mall_orders_payable CHECK (payable_amount >= 0),
    CONSTRAINT ck_mall_orders_paid CHECK (paid_amount >= 0),
    CONSTRAINT ck_mall_orders_payment_method CHECK (
        payment_method IN ('wallet', 'direct_cny', 'mixed')
    ),
    CONSTRAINT ck_mall_orders_status CHECK (
        status IN ('created', 'paid', 'delivered', 'cancelled', 'refunded', 'partial_refunded')
    )
);

CREATE TABLE mall.mall_order_items (
    mall_order_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mall_order_id      UUID NOT NULL,
    product_id         UUID NOT NULL,
    quantity           INTEGER NOT NULL,
    unit_price         NUMERIC(14, 2) NOT NULL,
    line_amount        NUMERIC(14, 2) NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_mall_order_items_qty CHECK (quantity > 0),
    CONSTRAINT ck_mall_order_items_unit CHECK (unit_price >= 0),
    CONSTRAINT ck_mall_order_items_line CHECK (line_amount >= 0)
);

CREATE TABLE mall.mall_refunds (
    mall_refund_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mall_order_id   UUID NOT NULL,
    refund_amount   NUMERIC(14, 2) NOT NULL,
    refund_currency TEXT NOT NULL,
    status          TEXT NOT NULL,
    reason_code     TEXT NOT NULL,
    reason_text     TEXT,
    refunded_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_mall_refunds_amount CHECK (refund_amount > 0),
    CONSTRAINT ck_mall_refunds_currency CHECK (refund_currency IN ('CNY', 'DIAMOND')),
    CONSTRAINT ck_mall_refunds_status CHECK (
        status IN ('requested', 'approved', 'rejected', 'completed')
    )
);

CREATE TABLE mall.item_delivery_records (
    delivery_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mall_order_id     UUID NOT NULL,
    mall_order_item_id UUID NOT NULL,
    player_id         UUID NOT NULL,
    character_id      UUID,
    game_item_id      UUID NOT NULL,
    quantity          INTEGER NOT NULL,
    delivery_status   TEXT NOT NULL,
    delivered_at      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_item_delivery_qty CHECK (quantity > 0),
    CONSTRAINT ck_item_delivery_status CHECK (
        delivery_status IN ('pending', 'success', 'failed', 'revoked')
    )
);

-- ---------------------------------------------------------------------------
-- payment
-- ---------------------------------------------------------------------------

CREATE TABLE payment.payment_channels (
    payment_channel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_code       TEXT NOT NULL,
    channel_name       TEXT NOT NULL,
    channel_type       TEXT NOT NULL,
    status             TEXT NOT NULL DEFAULT 'active',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_payment_channels_code UNIQUE (channel_code),
    CONSTRAINT ck_payment_channels_type CHECK (
        channel_type IN ('alipay', 'wechat', 'apple', 'google', 'unionpay', 'other')
    ),
    CONSTRAINT ck_payment_channels_status CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE payment.recharge_products (
    recharge_product_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id                UUID NOT NULL,
    product_code           TEXT NOT NULL,
    product_name           TEXT NOT NULL,
    price_amount_cny       NUMERIC(14, 2) NOT NULL,
    credit_currency_code   TEXT NOT NULL DEFAULT 'DIAMOND',
    credit_currency_amount NUMERIC(14, 2) NOT NULL,
    status                 TEXT NOT NULL DEFAULT 'on_sale',
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_recharge_products_code UNIQUE (product_code),
    CONSTRAINT ck_recharge_products_price CHECK (price_amount_cny > 0),
    CONSTRAINT ck_recharge_products_credit CHECK (credit_currency_amount > 0),
    CONSTRAINT ck_recharge_products_currency CHECK (credit_currency_code = 'DIAMOND'),
    CONSTRAINT ck_recharge_products_status CHECK (status IN ('on_sale', 'off_sale', 'archived'))
);

CREATE TABLE payment.recharge_orders (
    recharge_order_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_no               TEXT NOT NULL,
    player_id              UUID NOT NULL,
    game_id                UUID NOT NULL,
    recharge_product_id    UUID NOT NULL,
    order_amount           NUMERIC(14, 2) NOT NULL,
    credit_currency_amount NUMERIC(14, 2) NOT NULL,
    credit_currency_code   TEXT NOT NULL DEFAULT 'DIAMOND',
    status                 TEXT NOT NULL,
    ordered_at             TIMESTAMPTZ NOT NULL,
    completed_at           TIMESTAMPTZ,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_recharge_orders_order_no UNIQUE (order_no),
    CONSTRAINT ck_recharge_orders_amount CHECK (order_amount > 0),
    CONSTRAINT ck_recharge_orders_credit CHECK (credit_currency_amount > 0),
    CONSTRAINT ck_recharge_orders_currency CHECK (credit_currency_code = 'DIAMOND'),
    CONSTRAINT ck_recharge_orders_status CHECK (
        status IN (
            'created', 'paying', 'success', 'failed', 'closed',
            'refunded', 'partial_refunded'
        )
    )
);

CREATE TABLE payment.payment_transactions (
    payment_transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recharge_order_id      UUID NOT NULL,
    payment_channel_id     UUID NOT NULL,
    channel_txn_no         TEXT,
    paid_amount            NUMERIC(14, 2) NOT NULL,
    currency_code          TEXT NOT NULL DEFAULT 'CNY',
    status                 TEXT NOT NULL,
    paid_at                TIMESTAMPTZ,
    failure_reason         TEXT,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_payment_transactions_amount CHECK (paid_amount >= 0),
    CONSTRAINT ck_payment_transactions_currency CHECK (currency_code = 'CNY'),
    CONSTRAINT ck_payment_transactions_status CHECK (
        status IN ('pending', 'success', 'failed', 'cancelled')
    )
);

CREATE TABLE payment.payment_refunds (
    payment_refund_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recharge_order_id      UUID NOT NULL,
    payment_transaction_id UUID NOT NULL,
    refund_amount          NUMERIC(14, 2) NOT NULL,
    status                 TEXT NOT NULL,
    reason_code            TEXT NOT NULL,
    reason_text            TEXT,
    refunded_at            TIMESTAMPTZ,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_payment_refunds_amount CHECK (refund_amount > 0),
    CONSTRAINT ck_payment_refunds_status CHECK (
        status IN ('requested', 'approved', 'rejected', 'completed')
    )
);

CREATE TABLE payment.wallets (
    wallet_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id     UUID NOT NULL,
    currency_code TEXT NOT NULL DEFAULT 'DIAMOND',
    balance       NUMERIC(14, 2) NOT NULL DEFAULT 0,
    status        TEXT NOT NULL DEFAULT 'active',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_wallets_player_currency UNIQUE (player_id, currency_code),
    CONSTRAINT ck_wallets_currency CHECK (currency_code = 'DIAMOND'),
    CONSTRAINT ck_wallets_balance CHECK (balance >= 0),
    CONSTRAINT ck_wallets_status CHECK (status IN ('active', 'frozen', 'closed'))
);

CREATE TABLE payment.wallet_ledgers (
    ledger_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id          UUID NOT NULL,
    entry_type         TEXT NOT NULL,
    change_amount      NUMERIC(14, 2) NOT NULL,
    balance_after      NUMERIC(14, 2) NOT NULL,
    recharge_order_id  UUID,
    mall_order_id      UUID,
    campaign_reward_id UUID,
    remark             TEXT,
    occurred_at        TIMESTAMPTZ NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_wallet_ledgers_entry_type CHECK (
        entry_type IN (
            'recharge_credit', 'mall_debit', 'mall_refund_credit',
            'payment_refund_debit', 'campaign_reward_credit', 'adjust'
        )
    ),
    CONSTRAINT ck_wallet_ledgers_balance_after CHECK (balance_after >= 0),
    CONSTRAINT ck_wallet_ledgers_change_nonzero CHECK (change_amount <> 0)
);

-- ---------------------------------------------------------------------------
-- support
-- ---------------------------------------------------------------------------

CREATE TABLE support.agents (
    agent_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_code TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    team_name  TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_agents_code UNIQUE (agent_code),
    CONSTRAINT ck_agents_status CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE support.ticket_categories (
    category_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_code TEXT NOT NULL,
    category_name TEXT NOT NULL,
    description   TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ticket_categories_code UNIQUE (category_code)
);

CREATE TABLE support.tickets (
    ticket_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_no          TEXT NOT NULL,
    player_id          UUID NOT NULL,
    category_id        UUID NOT NULL,
    character_id       UUID,
    recharge_order_id  UUID,
    mall_order_id      UUID,
    campaign_id        UUID,
    subject            TEXT NOT NULL,
    priority           TEXT NOT NULL DEFAULT 'normal',
    status             TEXT NOT NULL,
    opened_at          TIMESTAMPTZ NOT NULL,
    closed_at          TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tickets_ticket_no UNIQUE (ticket_no),
    CONSTRAINT ck_tickets_priority CHECK (
        priority IN ('low', 'normal', 'high', 'vip')
    ),
    CONSTRAINT ck_tickets_status CHECK (
        status IN ('open', 'pending', 'resolved', 'closed', 'reopened')
    ),
    CONSTRAINT ck_tickets_closed CHECK (
        closed_at IS NULL OR closed_at >= opened_at
    )
);

CREATE TABLE support.ticket_messages (
    message_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id         UUID NOT NULL,
    sender_type       TEXT NOT NULL,
    sender_player_id  UUID,
    sender_agent_id   UUID,
    message_body      TEXT NOT NULL,
    sent_at           TIMESTAMPTZ NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_ticket_messages_sender_type CHECK (
        sender_type IN ('player', 'agent', 'system')
    ),
    CONSTRAINT ck_ticket_messages_body_nonempty CHECK (length(trim(message_body)) > 0)
);

CREATE TABLE support.ticket_assignments (
    assignment_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id         UUID NOT NULL,
    agent_id          UUID NOT NULL,
    assignment_reason TEXT,
    assigned_at       TIMESTAMPTZ NOT NULL,
    unassigned_at     TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_ticket_assignments_span CHECK (
        unassigned_at IS NULL OR unassigned_at >= assigned_at
    )
);

CREATE TABLE support.ticket_resolution_records (
    resolution_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id            UUID NOT NULL,
    resolved_by_agent_id UUID NOT NULL,
    resolution_code      TEXT NOT NULL,
    resolution_summary   TEXT NOT NULL,
    resolved_at          TIMESTAMPTZ NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ticket_resolution_ticket UNIQUE (ticket_id)
);

CREATE TABLE support.customer_satisfaction (
    csat_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id    UUID NOT NULL,
    player_id    UUID NOT NULL,
    score        INTEGER NOT NULL,
    comment_text TEXT,
    rated_at     TIMESTAMPTZ NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_csat_ticket UNIQUE (ticket_id),
    CONSTRAINT ck_csat_score CHECK (score BETWEEN 1 AND 5)
);

-- ---------------------------------------------------------------------------
-- marketing
-- ---------------------------------------------------------------------------

CREATE TABLE marketing.marketing_channels (
    marketing_channel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_code         TEXT NOT NULL,
    channel_name         TEXT NOT NULL,
    channel_family       TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'active',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_marketing_channels_code UNIQUE (channel_code),
    CONSTRAINT ck_marketing_channels_family CHECK (
        channel_family IN (
            'official_website', 'app_store', 'feed_ads', 'short_video',
            'community', 'kol', 'affiliate', 'other'
        )
    ),
    CONSTRAINT ck_marketing_channels_status CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE marketing.campaigns (
    campaign_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_code TEXT NOT NULL,
    campaign_name TEXT NOT NULL,
    game_id       UUID NOT NULL,
    campaign_type TEXT NOT NULL,
    status        TEXT NOT NULL,
    start_at      TIMESTAMPTZ NOT NULL,
    end_at        TIMESTAMPTZ NOT NULL,
    description   TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_campaigns_code UNIQUE (campaign_code),
    CONSTRAINT ck_campaigns_type CHECK (
        campaign_type IN (
            'acquisition', 'retention', 'reactivation', 'spend_boost', 'seasonal'
        )
    ),
    CONSTRAINT ck_campaigns_status CHECK (
        status IN ('draft', 'running', 'ended', 'cancelled')
    ),
    CONSTRAINT ck_campaigns_window CHECK (end_at >= start_at)
);

CREATE TABLE marketing.campaign_channels (
    campaign_id           UUID NOT NULL,
    marketing_channel_id  UUID NOT NULL,
    placement_note        TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (campaign_id, marketing_channel_id)
);

CREATE TABLE marketing.ad_costs (
    ad_cost_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    marketing_channel_id  UUID NOT NULL,
    campaign_id           UUID,
    cost_date             DATE NOT NULL,
    cost_amount           NUMERIC(14, 2) NOT NULL,
    currency_code         TEXT NOT NULL DEFAULT 'CNY',
    impressions           INTEGER NOT NULL DEFAULT 0,
    clicks                INTEGER NOT NULL DEFAULT 0,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_ad_costs_amount CHECK (cost_amount >= 0),
    CONSTRAINT ck_ad_costs_currency CHECK (currency_code = 'CNY'),
    CONSTRAINT ck_ad_costs_impressions CHECK (impressions >= 0),
    CONSTRAINT ck_ad_costs_clicks CHECK (clicks >= 0),
    CONSTRAINT ck_ad_costs_click_le_imp CHECK (clicks <= impressions)
);

CREATE TABLE marketing.player_attributions (
    attribution_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id             UUID NOT NULL,
    marketing_channel_id  UUID NOT NULL,
    campaign_id           UUID,
    attribution_type      TEXT NOT NULL,
    attributed_at         TIMESTAMPTZ NOT NULL,
    attribution_model     TEXT NOT NULL DEFAULT 'rule_based',
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_player_attributions_type CHECK (
        attribution_type IN ('first_touch', 'last_touch', 'campaign_conversion')
    ),
    CONSTRAINT uq_player_attributions_player_type_time UNIQUE (
        player_id, attribution_type, attributed_at
    )
);

CREATE TABLE marketing.campaign_participations (
    participation_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id                 UUID NOT NULL,
    player_id                   UUID NOT NULL,
    character_id                UUID,
    joined_at                   TIMESTAMPTZ NOT NULL,
    participation_status        TEXT NOT NULL,
    converted_recharge_order_id UUID,
    converted_at                TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_campaign_participations_campaign_player UNIQUE (campaign_id, player_id),
    CONSTRAINT ck_campaign_participations_status CHECK (
        participation_status IN ('joined', 'completed', 'converted', 'expired')
    )
);

CREATE TABLE marketing.campaign_rewards (
    campaign_reward_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participation_id     UUID NOT NULL,
    player_id            UUID NOT NULL,
    reward_type          TEXT NOT NULL,
    reward_currency_code TEXT,
    reward_amount        NUMERIC(14, 2),
    game_item_id         UUID,
    item_quantity        INTEGER,
    grant_status         TEXT NOT NULL,
    granted_at           TIMESTAMPTZ,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_campaign_rewards_type CHECK (
        reward_type IN ('currency', 'item', 'mixed')
    ),
    CONSTRAINT ck_campaign_rewards_status CHECK (
        grant_status IN ('pending', 'granted', 'failed', 'revoked')
    ),
    CONSTRAINT ck_campaign_rewards_amount CHECK (
        reward_amount IS NULL OR reward_amount >= 0
    ),
    CONSTRAINT ck_campaign_rewards_qty CHECK (
        item_quantity IS NULL OR item_quantity > 0
    )
);
