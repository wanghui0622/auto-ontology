#!/usr/bin/env python3
"""Generate reproducible StarSea Gaming demo datasets (Stage 3).

Fixed seed + fixed NOW produce identical UUID/time sequences across runs.
Business consistency: wallet ledgers reconcile balances; mall wallet spends
require sufficient balance; attributions and tickets reference real entities.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

SEED = 42
NOW = datetime(2026, 11, 22, 12, 0, 0, tzinfo=timezone.utc)
START = NOW - timedelta(days=365)

TARGETS = {
    "players": 2000,
    "player_accounts": 2500,
    "games": 2,
    "game_servers": 10,
    "characters": 3000,
    "player_sessions": 30000,
    "game_events": 50000,
    "mission_records": 15000,
    "battles": 10000,
    "products": 100,
    "mall_orders": 8000,
    "mall_order_items": 15000,
    "recharge_orders": 6000,
    "payment_transactions": 6000,
    "wallet_ledgers": 20000,
    "tickets": 3000,
    "ticket_messages": 12000,
    "campaigns": 30,
    "ad_costs": 3000,
    "player_attributions": 2000,  # at least first_touch per player; may exceed
    "campaign_participations": 8000,
}

COUNTRIES = ["CN", "US", "JP", "KR", "SG", "TW", "HK", "TH", "VN", "MY"]
NICK_PREFIX = [
    "星海", "远征", "暗影", "烈焰", "霜语", "苍穹", "银翼", "赤潮", "玄铁", "流光",
]
NICK_SUFFIX = [
    "旅人", "猎手", "剑客", "法师", "统帅", "行者", "守护", "先锋", "浪客", "贤者",
]


def D(value: float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def uid(rng: random.Random) -> uuid.UUID:
    return uuid.UUID(int=rng.getrandbits(128))


def clamp_dt(dt: datetime) -> datetime:
    if dt < START:
        return START
    if dt > NOW:
        return NOW
    return dt


def rand_dt(rng: random.Random, start: datetime | None = None, end: datetime | None = None) -> datetime:
    a = start or START
    b = end or NOW
    if b <= a:
        return a
    span = int((b - a).total_seconds())
    return a + timedelta(seconds=rng.randint(0, max(span, 0)))


def weighted_choice(rng: random.Random, items: list[Any], weights: list[float]) -> Any:
    return rng.choices(items, weights=weights, k=1)[0]


@dataclass
class Dataset:
    tables: dict[str, list[tuple]] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)


TICKET_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "gameplay": [
        ("我想问一下主线任务卡在第三章怎么过？", "您好，请确认角色等级是否达到要求，并检查任务追踪面板是否有红色提示。"),
        ("副本匹配一直失败，是不是服务器问题？", "您好，当前高峰期匹配队列较长，建议切换线路或稍后再试。"),
    ],
    "account": [
        ("我的账号突然无法登录，提示异常。", "您好，请提供最近登录的设备和大致时间，我们协助核查风控状态。"),
        ("角色不见了，登录后列表是空的。", "您好，请确认区服选择是否正确，我们会帮您核对角色存档。"),
    ],
    "recharge_missing": [
        ("我昨天充值了648元，支付成功了，但是钻石一直没有到账。", "您好，请提供您的充值订单号，我们帮您核实支付状态。"),
        ("微信已经扣款，游戏里余额没变化。", "您好，请补充支付渠道交易号，我们会与支付流水进行核对。"),
    ],
    "mall_issue": [
        ("商城买的月卡道具没有发到角色身上。", "您好，请提供商城订单号和角色名，我们核查发放记录。"),
        ("礼包里少了皮肤，订单显示已完成。", "您好，我们先核对商品配置与发放明细，请稍等。"),
    ],
    "refund": [
        ("我想申请退款，买错充值套餐了。", "您好，请说明订单号与原因，我们按退款规则评估处理。"),
        ("孩子误充值，能否退回？", "您好，请提供监护人联系方式与订单号，我们转专项流程。"),
    ],
    "bug": [
        ("打 Boss 时客户端闪退，重进进度丢失。", "您好，请提供发生时间、区服和客户端版本，我们提交程序排查。"),
        ("技能冷却显示异常，一直转圈。", "您好，建议先清理缓存重登；若仍复现请录屏反馈。"),
    ],
    "campaign_reward": [
        ("活动说有双倍钻石，我参与了但没到账。", "您好，请确认是否满足活动条件，我们核对奖励发放状态。"),
        ("签到奖励领取失败。", "您好，请提供角色与领取时间，我们检查活动参与记录。"),
    ],
    "appeal": [
        ("我觉得禁言处罚过重，想申诉。", "您好，请说明事发时间与聊天记录，我们复核违规判定。"),
        ("账号被封，我认为是误判。", "您好，请补充申诉理由，我们提交安全组复审。"),
    ],
}


def build_dataset(seed: int = SEED) -> Dataset:
    rng = random.Random(seed)
    ds = Dataset()

    # ------------------------------------------------------------------ dims
    reg_sources = []
    mkt_channels = []
    channel_defs = [
        ("official_website", "官方网站", "official_website", 0.08, D("12.00")),
        ("app_store", "应用商店", "app_store", 0.22, D("18.00")),
        ("feed_ads", "信息流广告", "feed_ads", 0.25, D("35.00")),
        ("short_video", "短视频平台", "short_video", 0.20, D("42.00")),
        ("community", "社区推广", "community", 0.10, D("15.00")),
        ("kol", "KOL 推广", "kol", 0.08, D("55.00")),
        ("affiliate", "联盟推广", "affiliate", 0.07, D("28.00")),
    ]
    for code, name, family, _w, _cac in channel_defs:
        sid = uid(rng)
        mid = uid(rng)
        reg_sources.append(
            (sid, code, name, family, f"{name}注册来源", NOW, NOW)
        )
        mkt_channels.append(
            (mid, code, name, family, "active", NOW, NOW)
        )
    ds.tables["identity.registration_sources"] = reg_sources
    ds.tables["marketing.marketing_channels"] = mkt_channels
    source_by_code = {r[1]: r[0] for r in reg_sources}
    channel_by_code = {r[1]: r[0] for r in mkt_channels}
    channel_weight = {c: w for c, _n, _f, w, _cac in channel_defs}
    channel_cac = {c: cac for c, _n, _f, _w, cac in channel_defs}

    pay_channels = []
    for code, name, ctype in [
        ("alipay", "支付宝", "alipay"),
        ("wechat", "微信支付", "wechat"),
        ("apple", "Apple IAP", "apple"),
        ("google", "Google Play", "google"),
        ("unionpay", "云闪付", "unionpay"),
    ]:
        pay_channels.append((uid(rng), code, name, ctype, "active", NOW, NOW))
    ds.tables["payment.payment_channels"] = pay_channels

    tags = []
    for code, name, cat in [
        ("high_value", "高价值玩家", "value"),
        ("returning", "回流玩家", "lifecycle"),
        ("risk", "风险关注", "risk"),
        ("social", "社交活跃", "behavior"),
        ("pve_lover", "PVE 偏好", "behavior"),
        ("pvp_lover", "PVP 偏好", "behavior"),
    ]:
        tags.append((uid(rng), code, name, cat, name, NOW, NOW))
    ds.tables["identity.player_tags"] = tags

    agents = []
    for i in range(1, 21):
        agents.append(
            (
                uid(rng),
                f"CS{i:03d}",
                f"客服{i:02d}",
                "VIP组" if i <= 5 else "综合组",
                "active",
                NOW,
                NOW,
            )
        )
    ds.tables["support.agents"] = agents

    ticket_cats = []
    cat_map = {}
    for code, name in [
        ("gameplay", "游戏玩法咨询"),
        ("account", "账号异常"),
        ("recharge_missing", "充值未到账"),
        ("mall_issue", "商城商品问题"),
        ("refund", "退款申请"),
        ("bug", "游戏 BUG"),
        ("campaign_reward", "活动奖励问题"),
        ("appeal", "违规处罚申诉"),
    ]:
        cid = uid(rng)
        cat_map[code] = cid
        ticket_cats.append((cid, code, name, name, NOW, NOW))
    ds.tables["support.ticket_categories"] = ticket_cats

    # games / servers
    game_era = uid(rng)
    game_exp = uid(rng)
    games = [
        (game_era, "STARSEA_ERA", "星海纪元", "mmorpg", "online", START, NOW, NOW),
        (game_exp, "STARSEA_EXPEDITION", "星海远征", "strategy", "online", START, NOW, NOW),
    ]
    ds.tables["game.games"] = games

    servers = []
    era_servers, exp_servers = [], []
    for i in range(1, 7):
        sid = uid(rng)
        servers.append(
            (sid, game_era, f"ERA-{i:02d}", f"纪元{i}服", "CN", "open", START + timedelta(days=i * 7), NOW, NOW)
        )
        era_servers.append(sid)
    for i in range(1, 5):
        sid = uid(rng)
        servers.append(
            (sid, game_exp, f"EXP-{i:02d}", f"远征{i}服", "CN", "open", START + timedelta(days=i * 10), NOW, NOW)
        )
        exp_servers.append(sid)
    ds.tables["game.game_servers"] = servers
    servers_by_game = {game_era: era_servers, game_exp: exp_servers}

    # missions / items
    missions = []
    missions_by_game: dict[uuid.UUID, list[uuid.UUID]] = {game_era: [], game_exp: []}
    for gid, prefix, names in [
        (game_era, "ERA", ["新手套装", "主线启程", "日常清剿", "周常试炼", "秘境探索", "装备强化", "公会委托", "世界Boss"]),
        (game_exp, "EXP", ["基地建设", "首战告捷", "资源采集", "联盟集结", "竞技挑战", "战役推进", "科技研究", "防守反击"]),
    ]:
        for idx, name in enumerate(names, start=1):
            mid = uid(rng)
            mtype = ["main", "side", "daily", "weekly", "event"][idx % 5]
            missions.append(
                (mid, gid, f"{prefix}_M{idx:02d}", name, mtype, 1 + (idx % 20), f"{name}任务", NOW, NOW)
            )
            missions_by_game[gid].append(mid)
    ds.tables["game.missions"] = missions

    game_items = []
    items_by_game: dict[uuid.UUID, list[uuid.UUID]] = {game_era: [], game_exp: []}
    item_types = ["consumable", "equipment", "cosmetic", "material", "currency_pack"]
    rarities = ["common", "rare", "epic", "legendary"]
    for gid, prefix in [(game_era, "ERA"), (game_exp, "EXP")]:
        for i in range(1, 41):
            iid = uid(rng)
            game_items.append(
                (
                    iid,
                    gid,
                    f"{prefix}_ITEM_{i:03d}",
                    f"{prefix}道具{i}",
                    item_types[i % len(item_types)],
                    rarities[i % len(rarities)],
                    f"{prefix}游戏道具{i}",
                    NOW,
                    NOW,
                )
            )
            items_by_game[gid].append(iid)
    ds.tables["game.game_items"] = game_items

    # recharge products
    recharge_products = []
    recharge_by_game: dict[uuid.UUID, list[tuple]] = {game_era: [], game_exp: []}
    packs = [
        ("60", D("6.00"), D("60")),
        ("300", D("30.00"), D("300")),
        ("980", D("98.00"), D("980")),
        ("1980", D("198.00"), D("1980")),
        ("3280", D("328.00"), D("3280")),
        ("6480", D("648.00"), D("6480")),
    ]
    for gid, prefix in [(game_era, "ERA"), (game_exp, "EXP")]:
        for code, price, credit in packs:
            pid = uid(rng)
            row = (
                pid,
                gid,
                f"{prefix}_R_{code}",
                f"{prefix}充值{code}钻",
                price,
                "DIAMOND",
                credit,
                "on_sale",
                NOW,
                NOW,
            )
            recharge_products.append(row)
            recharge_by_game[gid].append(row)
    ds.tables["payment.recharge_products"] = recharge_products

    # mall categories / products
    categories = []
    cat_root = uid(rng)
    categories.append((cat_root, "ROOT", "全部商品", None, NOW, NOW))
    cat_ids = []
    for code, name in [
        ("growth", "成长礼包"),
        ("cosmetic", "外观装扮"),
        ("monthly", "月卡订阅"),
        ("resource", "资源补给"),
        ("limited", "限时特惠"),
    ]:
        cid = uid(rng)
        cat_ids.append(cid)
        categories.append((cid, code.upper(), name, cat_root, NOW, NOW))
    ds.tables["mall.product_categories"] = categories

    products = []
    product_items = []
    products_meta: list[dict[str, Any]] = []
    for i in range(TARGETS["products"]):
        pid = uid(rng)
        gid = game_era if i % 2 == 0 else game_exp
        currency = "DIAMOND" if i % 5 != 0 else "CNY"
        if currency == "DIAMOND":
            price = D(rng.choice([60, 120, 300, 680, 1280, 3280]))
        else:
            price = D(rng.choice([6, 18, 30, 68, 98]))
        cat = cat_ids[i % len(cat_ids)]
        products.append(
            (
                pid,
                cat,
                gid,
                f"PROD_{i+1:03d}",
                f"商品{i+1}",
                currency,
                price,
                "on_sale",
                f"星海商城商品{i+1}",
                NOW,
                NOW,
            )
        )
        # 1-3 items
        n_items = 1 + (i % 3)
        chosen = rng.sample(items_by_game[gid], k=min(n_items, len(items_by_game[gid])))
        for gi in chosen:
            product_items.append((uid(rng), pid, gi, rng.randint(1, 5), NOW, NOW))
        products_meta.append(
            {"product_id": pid, "game_id": gid, "currency": currency, "price": price}
        )
    ds.tables["mall.products"] = products
    ds.tables["mall.product_items"] = product_items
    product_items_by_product: dict[uuid.UUID, list[tuple[uuid.UUID, int]]] = {}
    for _pi, prod, gi, qty, *_ in product_items:
        product_items_by_product.setdefault(prod, []).append((gi, qty))

    # campaigns
    campaigns = []
    campaign_channels = []
    campaign_rows: list[dict[str, Any]] = []
    for i in range(TARGETS["campaigns"]):
        cid = uid(rng)
        gid = game_era if i % 2 == 0 else game_exp
        start = START + timedelta(days=rng.randint(0, 300))
        end = min(start + timedelta(days=rng.randint(7, 45)), NOW)
        ctype = ["acquisition", "retention", "reactivation", "spend_boost", "seasonal"][i % 5]
        status = "ended" if end < NOW - timedelta(days=1) else "running"
        campaigns.append(
            (
                cid,
                f"CP_{i+1:02d}",
                f"活动{i+1}",
                gid,
                ctype,
                status,
                start,
                end,
                f"运营活动{i+1}",
                NOW,
                NOW,
            )
        )
        ch_codes = rng.sample([c[0] for c in channel_defs], k=rng.randint(2, 4))
        for code in ch_codes:
            campaign_channels.append(
                (cid, channel_by_code[code], f"投放于{code}", NOW, NOW)
            )
        campaign_rows.append({"id": cid, "game_id": gid, "start": start, "end": end, "channels": ch_codes})
    ds.tables["marketing.campaigns"] = campaigns
    ds.tables["marketing.campaign_channels"] = campaign_channels

    # ad costs ~3000
    ad_costs = []
    days = (NOW.date() - START.date()).days
    while len(ad_costs) < TARGETS["ad_costs"]:
        ch = weighted_choice(rng, channel_defs, [c[3] for c in channel_defs])
        code = ch[0]
        d = START.date() + timedelta(days=rng.randint(0, days))
        camp = rng.choice(campaign_rows) if rng.random() < 0.7 else None
        impressions = rng.randint(1000, 80000)
        clicks = rng.randint(10, max(11, impressions // 20))
        # cost roughly CAC-ish * clicks / 10
        cost = (channel_cac[code] * D(clicks) / D(30)).quantize(Decimal("0.01"))
        ad_costs.append(
            (
                uid(rng),
                channel_by_code[code],
                camp["id"] if camp else None,
                d,
                cost,
                "CNY",
                impressions,
                clicks,
                NOW,
                NOW,
            )
        )
    ds.tables["marketing.ad_costs"] = ad_costs

    # ------------------------------------------------------------------ players
    players = []
    player_accounts = []
    player_devices = []
    player_tag_rels = []
    wallets = []
    attributions = []
    attribution_keys: set[tuple[uuid.UUID, str, datetime]] = set()
    players_meta: list[dict[str, Any]] = []

    def add_attribution(
        player_id: uuid.UUID,
        channel_id: uuid.UUID,
        campaign_id: uuid.UUID | None,
        attribution_type: str,
        attributed_at: datetime,
    ) -> None:
        ts = attributed_at
        key = (player_id, attribution_type, ts)
        # unique (player_id, attribution_type, attributed_at)
        while key in attribution_keys:
            ts = ts + timedelta(seconds=1)
            if ts > NOW:
                ts = NOW - timedelta(seconds=rng.randint(1, 1000))
            key = (player_id, attribution_type, ts)
        attribution_keys.add(key)
        attributions.append(
            (
                uid(rng),
                player_id,
                channel_id,
                campaign_id,
                attribution_type,
                ts,
                "rule_based",
                ts,
                ts,
            )
        )

    tier_plan = (
        ["free"] * 1400
        + ["light_payer"] * 400
        + ["mid_payer"] * 160
        + ["whale"] * 40
    )
    rng.shuffle(tier_plan)

    for i in range(TARGETS["players"]):
        pid = uid(rng)
        tier = tier_plan[i]
        ch = weighted_choice(rng, channel_defs, [c[3] for c in channel_defs])
        ch_code = ch[0]
        reg_time = rand_dt(rng)
        vip = {"free": 0, "light_payer": rng.randint(0, 2), "mid_payer": rng.randint(2, 5), "whale": rng.randint(6, 10)}[tier]
        nick = f"{rng.choice(NICK_PREFIX)}{rng.choice(NICK_SUFFIX)}{i:04d}"
        status = weighted_choice(rng, ["active", "churned", "banned"], [0.88, 0.10, 0.02])
        players.append(
            (
                pid,
                nick,
                reg_time,
                ch[1],
                source_by_code[ch_code],
                rng.choice(COUNTRIES),
                status,
                tier,
                vip,
                reg_time,
                reg_time,
            )
        )
        wid = uid(rng)
        wallets.append((wid, pid, "DIAMOND", D(0), "active", reg_time, reg_time))
        add_attribution(pid, channel_by_code[ch_code], None, "first_touch", reg_time)
        # device
        player_devices.append(
            (
                uid(rng),
                pid,
                f"DEV-{i:05d}-{rng.randint(1000,9999)}",
                rng.choice(["ios", "android", "android", "ios", "other"]),
                rng.choice(["iPhone15", "Pixel8", "Mi14", "Honor90", "Unknown"]),
                reg_time,
                rand_dt(rng, reg_time, NOW),
                reg_time,
                reg_time,
            )
        )
        # tags
        if tier in {"mid_payer", "whale"}:
            tag = next(t for t in tags if t[1] == "high_value")
            player_tag_rels.append((pid, tag[0], reg_time, "system", reg_time, reg_time))
        if status == "churned" and rng.random() < 0.3:
            tag = next(t for t in tags if t[1] == "returning")
            player_tag_rels.append((pid, tag[0], reg_time, "system", reg_time, reg_time))

        players_meta.append(
            {
                "player_id": pid,
                "tier": tier,
                "reg_time": reg_time,
                "channel_code": ch_code,
                "vip": vip,
                "wallet_id": wid,
                "balance": D(0),
                "status": status,
                "characters": [],
                "activity": {"free": 0.35, "light_payer": 0.55, "mid_payer": 0.75, "whale": 0.95}[tier],
            }
        )

    # accounts: 2500 => 500 players get second game account
    for meta in players_meta:
        # always one account for preferred game
        primary_game = game_era if rng.random() < 0.55 else game_exp
        player_accounts.append(
            (
                uid(rng),
                meta["player_id"],
                primary_game,
                f"acc_{str(meta['player_id'])[:8]}_1",
                "active" if meta["status"] == "active" else "locked",
                meta["reg_time"],
                meta["reg_time"],
            )
        )
        meta["games"] = [primary_game]
    extras = TARGETS["player_accounts"] - len(player_accounts)
    extra_players = players_meta[:extras]
    for meta in extra_players:
        other = game_exp if meta["games"][0] == game_era else game_era
        player_accounts.append(
            (
                uid(rng),
                meta["player_id"],
                other,
                f"acc_{str(meta['player_id'])[:8]}_2",
                "active",
                    clamp_dt(meta["reg_time"] + timedelta(days=rng.randint(1, 60))),
                NOW,
            )
        )
        meta["games"].append(other)

    ds.tables["identity.players"] = players
    ds.tables["identity.player_accounts"] = player_accounts
    ds.tables["identity.player_devices"] = player_devices
    ds.tables["identity.player_tag_relations"] = player_tag_rels
    ds.tables["payment.wallets"] = wallets
    # attributions continue later for last_touch / conversion

    # ------------------------------------------------------------------ characters
    characters = []
    char_attrs = []
    # distribute 3000 chars across players (avg 1.5)
    char_target = TARGETS["characters"]
    # ensure each player with account gets >=1 char for first game
    for meta in players_meta:
        for gi, gid in enumerate(meta["games"]):
            if len(characters) >= char_target:
                break
            sid = rng.choice(servers_by_game[gid])
            level = _level_for_tier(rng, meta["tier"], meta["activity"])
            play_minutes = int(level * rng.uniform(40, 90) * meta["activity"])
            created = clamp_dt(meta["reg_time"] + timedelta(hours=rng.randint(0, 72)))
            cid = uid(rng)
            characters.append(
                (
                    cid,
                    meta["player_id"],
                    gid,
                    sid,
                    f"C{str(cid)[:6]}",
                    level,
                    D(level * rng.uniform(80, 140)),
                    play_minutes,
                    rand_dt(rng, created, NOW),
                    "active",
                    created,
                    created,
                )
            )
            meta["characters"].append(
                {"character_id": cid, "game_id": gid, "server_id": sid, "level": level, "created": created}
            )
            char_attrs.append(
                (uid(rng), cid, "class" if gid == game_era else "faction", rng.choice(["战士", "法师", "刺客", "辅助"] if gid == game_era else ["联邦", "帝国", "海盗"]), created, created, created)
            )
        if len(characters) >= char_target:
            break
    # fill remaining characters on active players
    while len(characters) < char_target:
        meta = weighted_choice(
            rng,
            players_meta,
            [m["activity"] for m in players_meta],
        )
        gid = rng.choice(meta["games"] if meta["games"] else [game_era, game_exp])
        sid = rng.choice(servers_by_game[gid])
        level = _level_for_tier(rng, meta["tier"], meta["activity"])
        play_minutes = int(level * rng.uniform(40, 90) * meta["activity"])
        created = clamp_dt(meta["reg_time"] + timedelta(days=rng.randint(0, 200)))
        cid = uid(rng)
        characters.append(
            (
                cid,
                meta["player_id"],
                gid,
                sid,
                f"C{str(cid)[:6]}",
                level,
                D(level * rng.uniform(80, 140)),
                play_minutes,
                rand_dt(rng, created, NOW),
                "active",
                created,
                created,
            )
        )
        meta["characters"].append(
            {"character_id": cid, "game_id": gid, "server_id": sid, "level": level, "created": created}
        )
    ds.tables["game.characters"] = characters
    ds.tables["game.character_attributes"] = char_attrs

    char_by_id = {c[0]: c for c in characters}

    # ------------------------------------------------------------------ sessions / events / missions / battles
    sessions = []
    events = []
    mission_records = []
    battles = []
    battle_parts = []

    # sessions 30k
    while len(sessions) < TARGETS["player_sessions"]:
        meta = weighted_choice(rng, players_meta, [m["activity"] for m in players_meta])
        if not meta["characters"]:
            continue
        ch = rng.choice(meta["characters"])
        earliest = max(meta["reg_time"], ch["created"])
        if earliest >= NOW:
            continue
        login = rand_dt(rng, earliest, NOW)
        dur = int(rng.gauss(1800, 900) * meta["activity"])
        dur = max(120, min(dur, 6 * 3600))
        logout = min(login + timedelta(seconds=dur), NOW)
        if logout < login:
            logout = login
        sessions.append(
            (
                uid(rng),
                meta["player_id"],
                ch["game_id"],
                ch["character_id"],
                login,
                logout,
                int((logout - login).total_seconds()),
                f"1.{rng.randint(0,9)}.{rng.randint(0,9)}",
                login,
                login,
            )
        )
    ds.tables["game.player_sessions"] = sessions

    event_types = ["login", "level_up", "purchase_intent", "dungeon_enter", "pvp_match", "quest_accept", "chat", "logout"]
    while len(events) < TARGETS["game_events"]:
        meta = weighted_choice(rng, players_meta, [m["activity"] for m in players_meta])
        if not meta["characters"]:
            continue
        ch = rng.choice(meta["characters"])
        et = rng.choice(event_types)
        etime = rand_dt(rng, ch["created"], NOW)
        events.append(
            (
                uid(rng),
                meta["player_id"],
                ch["character_id"],
                ch["game_id"],
                et,
                et,
                {"source": "generator", "tier": meta["tier"]},
                etime,
                etime,
                etime,
            )
        )
    ds.tables["game.game_events"] = events

    while len(mission_records) < TARGETS["mission_records"]:
        meta = weighted_choice(rng, players_meta, [m["activity"] for m in players_meta])
        if not meta["characters"]:
            continue
        ch = rng.choice(meta["characters"])
        mid = rng.choice(missions_by_game[ch["game_id"]])
        started = rand_dt(rng, ch["created"], NOW)
        status = weighted_choice(rng, ["completed", "in_progress", "failed", "abandoned"], [0.7, 0.15, 0.1, 0.05])
        completed = started + timedelta(minutes=rng.randint(10, 180)) if status == "completed" else None
        if completed and completed > NOW:
            completed = NOW
        mission_records.append(
            (uid(rng), mid, ch["character_id"], status, started, completed, started, started)
        )
    ds.tables["game.mission_records"] = mission_records

    while len(battles) < TARGETS["battles"]:
        meta = weighted_choice(rng, players_meta, [m["activity"] for m in players_meta])
        if not meta["characters"]:
            continue
        ch = rng.choice(meta["characters"])
        bid = uid(rng)
        started = rand_dt(rng, ch["created"], NOW)
        ended = min(started + timedelta(minutes=rng.randint(3, 40)), NOW)
        btype = rng.choice(["pve", "pvp", "dungeon", "campaign", "arena"])
        battles.append(
            (bid, ch["game_id"], ch["server_id"], btype, "auto", started, ended, started, started)
        )
        # 1-3 participants from same server preferably
        same_server = [c for c in characters if c[3] == ch["server_id"]]
        participants = rng.sample(same_server, k=min(rng.randint(1, 3), len(same_server)))
        if ch["character_id"] not in {p[0] for p in participants}:
            participants[0] = char_by_id[ch["character_id"]]
        for pi, p in enumerate(participants):
            battle_parts.append(
                (
                    bid,
                    p[0],
                    "attacker" if pi == 0 else "ally",
                    rng.choice(["win", "lose", "draw"]),
                    D(rng.uniform(100, 50000)),
                    started,
                    started,
                )
            )
    ds.tables["game.battles"] = battles
    ds.tables["game.battle_participants"] = battle_parts

    # ------------------------------------------------------------------ recharge + wallet
    recharge_orders = []
    payment_txns = []
    payment_refunds = []
    wallet_ledgers = []
    success_recharges_by_player: dict[uuid.UUID, list[uuid.UUID]] = {}
    all_success_recharge_meta: list[dict[str, Any]] = []

    # build intended recharge counts by tier
    def recharge_count(tier: str) -> int:
        if tier == "free":
            return 1 if rng.random() < 0.08 else 0  # rare failed/attempt
        if tier == "light_payer":
            return rng.randint(1, 4)
        if tier == "mid_payer":
            return rng.randint(4, 12)
        return rng.randint(15, 40)

    # generate until ~6000 orders
    order_no = 0
    # first pass: ensure tier behavior
    pending_players = players_meta[:]
    rng.shuffle(pending_players)
    for meta in pending_players:
        n = recharge_count(meta["tier"])
        for _ in range(n):
            if len(recharge_orders) >= TARGETS["recharge_orders"]:
                break
            gid = rng.choice(meta["games"] if meta["games"] else [game_era])
            product = rng.choice(recharge_by_game[gid])
            ordered = rand_dt(rng, meta["reg_time"], NOW)
            order_no += 1
            oid = uid(rng)
            # status mix
            if meta["tier"] == "free":
                status = weighted_choice(rng, ["failed", "paying", "closed", "success"], [0.55, 0.2, 0.15, 0.1])
            else:
                status = weighted_choice(
                    rng,
                    ["success", "failed", "paying", "closed", "refunded"],
                    [0.82, 0.08, 0.04, 0.02, 0.04],
                )
            completed = ordered + timedelta(minutes=rng.randint(1, 30)) if status in {"success", "refunded", "partial_refunded"} else None
            if completed and completed > NOW:
                completed = NOW
            recharge_orders.append(
                (
                    oid,
                    f"RO{order_no:08d}",
                    meta["player_id"],
                    gid,
                    product[0],
                    product[4],
                    product[6],
                    "DIAMOND",
                    status,
                    ordered,
                    completed,
                    ordered,
                    ordered,
                )
            )
            # transaction
            channel = rng.choice(pay_channels)
            paid = product[4] if status in {"success", "refunded", "partial_refunded"} else (
                product[4] if status == "paying" else D(0) if status == "closed" else product[4]
            )
            txn_status = {
                "success": "success",
                "refunded": "success",
                "partial_refunded": "success",
                "failed": "failed",
                "paying": "pending",
                "closed": "cancelled",
                "created": "pending",
            }.get(status, "pending")
            if status == "failed":
                paid = product[4]  # attempted amount recorded
            tid = uid(rng)
            payment_txns.append(
                (
                    tid,
                    oid,
                    channel[0],
                    f"TXN{order_no:08d}" if txn_status == "success" else None,
                    paid if txn_status != "cancelled" else D(0),
                    "CNY",
                    txn_status,
                    completed if txn_status == "success" else None,
                    "channel_reject" if txn_status == "failed" else None,
                    ordered,
                    ordered,
                )
            )
            if status in {"success", "refunded"}:
                # credit wallet
                credit = product[6]
                meta["balance"] += credit
                ledger_id = uid(rng)
                wallet_ledgers.append(
                    (
                        ledger_id,
                        meta["wallet_id"],
                        "recharge_credit",
                        credit,
                        meta["balance"],
                        oid,
                        None,
                        None,
                        "充值到账",
                        completed or ordered,
                        completed or ordered,
                        completed or ordered,
                    )
                )
                success_recharges_by_player.setdefault(meta["player_id"], []).append(oid)
                all_success_recharge_meta.append(
                    {"order_id": oid, "player": meta, "ordered": ordered, "amount": product[4], "game_id": gid}
                )
                if status == "refunded":
                    refund_amt = product[4]
                    payment_refunds.append(
                        (
                            uid(rng),
                            oid,
                            tid,
                            refund_amt,
                            "completed",
                            "user_request",
                            "玩家申请退款",
                            completed,
                            completed or ordered,
                            completed or ordered,
                        )
                    )
                    # claw back diamonds if enough
                    claw = min(meta["balance"], credit)
                    if claw > 0:
                        meta["balance"] -= claw
                        wallet_ledgers.append(
                            (
                                uid(rng),
                                meta["wallet_id"],
                                "payment_refund_debit",
                                -claw,
                                meta["balance"],
                                oid,
                                None,
                                None,
                                "充值退款扣回",
                                completed or ordered,
                                completed or ordered,
                                completed or ordered,
                            )
                        )
        if len(recharge_orders) >= TARGETS["recharge_orders"]:
            break

    # pad remaining recharge orders with light random attempts
    while len(recharge_orders) < TARGETS["recharge_orders"]:
        meta = rng.choice(players_meta)
        gid = rng.choice(meta["games"] if meta["games"] else [game_era])
        product = rng.choice(recharge_by_game[gid])
        ordered = rand_dt(rng, meta["reg_time"], NOW)
        order_no += 1
        oid = uid(rng)
        status = weighted_choice(rng, ["success", "failed", "paying", "closed"], [0.5, 0.25, 0.15, 0.1])
        completed = ordered + timedelta(minutes=5) if status == "success" else None
        recharge_orders.append(
            (
                oid,
                f"RO{order_no:08d}",
                meta["player_id"],
                gid,
                product[0],
                product[4],
                product[6],
                "DIAMOND",
                status,
                ordered,
                completed,
                ordered,
                ordered,
            )
        )
        channel = rng.choice(pay_channels)
        tid = uid(rng)
        txn_status = "success" if status == "success" else ("failed" if status == "failed" else "pending")
        payment_txns.append(
            (
                tid,
                oid,
                channel[0],
                f"TXN{order_no:08d}" if txn_status == "success" else None,
                product[4] if status != "closed" else D(0),
                "CNY",
                txn_status if status != "closed" else "cancelled",
                completed,
                None,
                ordered,
                ordered,
            )
        )
        if status == "success":
            meta["balance"] += product[6]
            wallet_ledgers.append(
                (
                    uid(rng),
                    meta["wallet_id"],
                    "recharge_credit",
                    product[6],
                    meta["balance"],
                    oid,
                    None,
                    None,
                    "充值到账",
                    completed or ordered,
                    completed or ordered,
                    completed or ordered,
                )
            )
            success_recharges_by_player.setdefault(meta["player_id"], []).append(oid)
            all_success_recharge_meta.append(
                {"order_id": oid, "player": meta, "ordered": ordered, "amount": product[4], "game_id": gid}
            )

    ds.tables["payment.recharge_orders"] = recharge_orders
    ds.tables["payment.payment_transactions"] = payment_txns
    ds.tables["payment.payment_refunds"] = payment_refunds

    # ------------------------------------------------------------------ mall orders
    mall_orders = []
    mall_order_items = []
    mall_refunds = []
    deliveries = []
    mall_no = 0

    # prefer spenders with balance / CNY products
    while len(mall_orders) < TARGETS["mall_orders"] or len(mall_order_items) < TARGETS["mall_order_items"]:
        if len(mall_orders) >= TARGETS["mall_orders"] and len(mall_order_items) >= TARGETS["mall_order_items"]:
            break
        if len(mall_orders) >= TARGETS["mall_orders"] * 2:
            break
        meta = weighted_choice(
            rng,
            players_meta,
            [
                0.2 if m["tier"] == "free" else 0.8 if m["tier"] == "light_payer" else 1.5 if m["tier"] == "mid_payer" else 3.0
                for m in players_meta
            ],
        )
        if not meta["characters"]:
            continue
        ch = rng.choice(meta["characters"])
        # pick products for same game
        candidates = [p for p in products_meta if p["game_id"] == ch["game_id"]]
        if not candidates:
            continue
        n_lines = rng.randint(1, 3)
        chosen = [rng.choice(candidates) for _ in range(n_lines)]
        # simplify: one currency per order
        currency = chosen[0]["currency"]
        chosen = [p for p in chosen if p["currency"] == currency] or chosen[:1]
        currency = chosen[0]["currency"]
        quantities = [rng.randint(1, 3) for _ in chosen]
        payable = sum((p["price"] * q for p, q in zip(chosen, quantities)), D(0))
        ordered = rand_dt(rng, max(meta["reg_time"], ch["created"]), NOW)

        payment_method = "wallet" if currency == "DIAMOND" else "direct_cny"
        status = "paid"
        paid_amount = payable
        if currency == "DIAMOND":
            if meta["balance"] < payable:
                # skip or create cancelled
                if rng.random() < 0.4:
                    status = "cancelled"
                    paid_amount = D(0)
                    payment_method = "wallet"
                else:
                    continue
            else:
                status = weighted_choice(rng, ["delivered", "paid", "refunded"], [0.85, 0.1, 0.05])
                paid_amount = payable
        else:
            status = weighted_choice(rng, ["delivered", "paid", "refunded", "cancelled"], [0.8, 0.1, 0.05, 0.05])
            if status == "cancelled":
                paid_amount = D(0)

        mall_no += 1
        oid = uid(rng)
        paid_at = ordered + timedelta(minutes=1) if status != "cancelled" else None
        mall_orders.append(
            (
                oid,
                f"MO{mall_no:08d}",
                meta["player_id"],
                ch["character_id"],
                ch["game_id"],
                currency,
                payable,
                paid_amount,
                payment_method,
                status,
                ordered,
                paid_at,
                ordered,
                ordered,
            )
        )
        line_rows = []
        for p, q in zip(chosen, quantities):
            line_id = uid(rng)
            line_amt = p["price"] * q
            mall_order_items.append(
                (line_id, oid, p["product_id"], q, p["price"], line_amt, ordered, ordered)
            )
            line_rows.append((line_id, p, q))
            if len(mall_order_items) >= TARGETS["mall_order_items"] and len(mall_orders) >= TARGETS["mall_orders"]:
                break

        if status in {"paid", "delivered", "refunded"} and currency == "DIAMOND" and paid_amount > 0:
            meta["balance"] -= paid_amount
            wallet_ledgers.append(
                (
                    uid(rng),
                    meta["wallet_id"],
                    "mall_debit",
                    -paid_amount,
                    meta["balance"],
                    None,
                    oid,
                    None,
                    "商城消费扣款",
                    paid_at or ordered,
                    paid_at or ordered,
                    paid_at or ordered,
                )
            )

        if status in {"paid", "delivered", "refunded"}:
            for line_id, p, q in line_rows:
                for gi, iq in product_items_by_product.get(p["product_id"], []):
                    deliveries.append(
                        (
                            uid(rng),
                            oid,
                            line_id,
                            meta["player_id"],
                            ch["character_id"],
                            gi,
                            iq * q,
                            "success" if status != "refunded" else "revoked",
                            paid_at or ordered,
                            ordered,
                            ordered,
                        )
                    )

        if status == "refunded" and paid_amount > 0:
            mall_refunds.append(
                (
                    uid(rng),
                    oid,
                    paid_amount,
                    currency,
                    "completed",
                    "user_request",
                    "商城退款",
                    paid_at or ordered,
                    ordered,
                    ordered,
                )
            )
            if currency == "DIAMOND":
                meta["balance"] += paid_amount
                wallet_ledgers.append(
                    (
                        uid(rng),
                        meta["wallet_id"],
                        "mall_refund_credit",
                        paid_amount,
                        meta["balance"],
                        None,
                        oid,
                        None,
                        "商城退款退回",
                        paid_at or ordered,
                        paid_at or ordered,
                        paid_at or ordered,
                    )
                )

        if len(mall_orders) >= TARGETS["mall_orders"] and len(mall_order_items) >= TARGETS["mall_order_items"]:
            break

    ds.tables["mall.mall_orders"] = mall_orders
    ds.tables["mall.mall_order_items"] = mall_order_items
    ds.tables["mall.mall_refunds"] = mall_refunds
    ds.tables["mall.item_delivery_records"] = deliveries

    # ------------------------------------------------------------------ marketing participations / rewards / last touch
    participations = []
    rewards = []
    while len(participations) < TARGETS["campaign_participations"]:
        meta = weighted_choice(rng, players_meta, [m["activity"] for m in players_meta])
        camp = rng.choice(campaign_rows)
        # unique (campaign, player) — skip duplicates
        key_exists = any(p[1] == camp["id"] and p[2] == meta["player_id"] for p in participations)
        if key_exists:
            continue
        joined = rand_dt(rng, max(meta["reg_time"], camp["start"]), min(NOW, camp["end"]))
        ch = None
        if meta["characters"]:
            same = [c for c in meta["characters"] if c["game_id"] == camp["game_id"]]
            ch = rng.choice(same or meta["characters"])
        status = weighted_choice(rng, ["joined", "completed", "converted", "expired"], [0.35, 0.35, 0.2, 0.1])
        conv_order = None
        conv_at = None
        if status == "converted" and success_recharges_by_player.get(meta["player_id"]):
            conv_order = rng.choice(success_recharges_by_player[meta["player_id"]])
            conv_at = joined + timedelta(days=rng.randint(0, 14))
            if conv_at > NOW:
                conv_at = NOW
            add_attribution(
                meta["player_id"],
                channel_by_code[rng.choice(camp["channels"])],
                camp["id"],
                "campaign_conversion",
                conv_at,
            )
        pid_part = uid(rng)
        participations.append(
            (
                pid_part,
                camp["id"],
                meta["player_id"],
                ch["character_id"] if ch else None,
                joined,
                status,
                conv_order,
                conv_at,
                joined,
                joined,
            )
        )
        if status in {"completed", "converted"} and rng.random() < 0.7:
            rid = uid(rng)
            reward_amt = D(rng.choice([10, 30, 60, 120]))
            rewards.append(
                (
                    rid,
                    pid_part,
                    meta["player_id"],
                    "currency",
                    "DIAMOND",
                    reward_amt,
                    None,
                    None,
                    "granted",
                    joined,
                    joined,
                    joined,
                )
            )
            meta["balance"] += reward_amt
            wallet_ledgers.append(
                (
                    uid(rng),
                    meta["wallet_id"],
                    "campaign_reward_credit",
                    reward_amt,
                    meta["balance"],
                    None,
                    None,
                    rid,
                    "活动奖励入账",
                    joined,
                    joined,
                    joined,
                )
            )

    # last_touch for subset of players
    for meta in players_meta:
        if rng.random() < 0.45:
            code = weighted_choice(rng, channel_defs, [c[3] for c in channel_defs])[0]
            at = rand_dt(rng, meta["reg_time"], NOW)
            add_attribution(meta["player_id"], channel_by_code[code], None, "last_touch", at)

    ds.tables["marketing.campaign_participations"] = participations
    ds.tables["marketing.campaign_rewards"] = rewards
    ds.tables["marketing.player_attributions"] = attributions

    # pad wallet ledgers if below target with tiny adjusts that net zero-ish
    # Prefer not breaking balances: create pairs or skip
    # If still short, add small campaign-like adjusts only for whales with positive balance
    guard = 0
    while len(wallet_ledgers) < TARGETS["wallet_ledgers"] and guard < 100000:
        guard += 1
        meta = rng.choice([m for m in players_meta if m["tier"] in {"mid_payer", "whale"}] or players_meta)
        if meta["balance"] <= 0:
            continue
        amt = D(rng.choice([1, 2, 5, 10]))
        if amt > meta["balance"]:
            continue
        # debit then credit adjust to keep balance same? That would add 2 ledgers.
        ts = rand_dt(rng, meta["reg_time"], NOW)
        meta["balance"] -= amt
        wallet_ledgers.append(
            (uid(rng), meta["wallet_id"], "adjust", -amt, meta["balance"], None, None, None, "运营调减", ts, ts, ts)
        )
        meta["balance"] += amt
        wallet_ledgers.append(
            (uid(rng), meta["wallet_id"], "adjust", amt, meta["balance"], None, None, None, "运营调增", ts + timedelta(seconds=1), ts, ts)
        )

    # update wallet balances in wallet rows
    balance_by_wallet = {m["wallet_id"]: m["balance"] for m in players_meta}
    wallets_updated = []
    for w in wallets:
        wallets_updated.append(
            (w[0], w[1], w[2], balance_by_wallet.get(w[0], D(0)), w[4], w[5], w[6])
        )
    ds.tables["payment.wallets"] = wallets_updated
    ds.tables["payment.wallet_ledgers"] = wallet_ledgers

    # ------------------------------------------------------------------ support tickets
    tickets = []
    messages = []
    assignments = []
    resolutions = []
    csats = []
    ticket_no = 0
    cat_codes = list(cat_map.keys())
    while len(tickets) < TARGETS["tickets"]:
        meta = weighted_choice(
            rng,
            players_meta,
            [1.0 + m["vip"] * 0.3 for m in players_meta],
        )
        code = rng.choice(cat_codes)
        # bias recharge tickets for payers
        if meta["tier"] in {"mid_payer", "whale"} and rng.random() < 0.25:
            code = "recharge_missing"
        ticket_no += 1
        tid = uid(rng)
        opened = rand_dt(rng, meta["reg_time"], NOW)
        priority = "vip" if meta["vip"] >= 6 else ("high" if meta["vip"] >= 3 else rng.choice(["low", "normal", "normal"]))
        status = weighted_choice(rng, ["resolved", "closed", "open", "pending", "reopened"], [0.45, 0.3, 0.1, 0.1, 0.05])
        closed = opened + timedelta(hours=rng.randint(1, 72)) if status in {"resolved", "closed"} else None
        if closed and closed > NOW:
            closed = NOW
        ch = rng.choice(meta["characters"]) if meta["characters"] else None
        ro = None
        mo = None
        camp = None
        if code == "recharge_missing" and success_recharges_by_player.get(meta["player_id"]):
            # sometimes attach failed orders instead; pick any recharge of player
            player_orders = [r for r in recharge_orders if r[2] == meta["player_id"]]
            if player_orders:
                ro = rng.choice(player_orders)[0]
        if code in {"mall_issue", "refund"}:
            player_malls = [m for m in mall_orders if m[2] == meta["player_id"]]
            if player_malls:
                mo = rng.choice(player_malls)[0]
        if code == "campaign_reward":
            camp = rng.choice(campaign_rows)["id"]
        subject = {
            "gameplay": "玩法咨询",
            "account": "账号异常",
            "recharge_missing": "充值未到账",
            "mall_issue": "商城问题",
            "refund": "退款申请",
            "bug": "游戏缺陷反馈",
            "campaign_reward": "活动奖励异常",
            "appeal": "处罚申诉",
        }[code]
        tickets.append(
            (
                tid,
                f"TK{ticket_no:08d}",
                meta["player_id"],
                cat_map[code],
                ch["character_id"] if ch and code in {"gameplay", "bug", "account"} else (ch["character_id"] if ch and rng.random() < 0.4 else None),
                ro,
                mo,
                camp,
                subject,
                priority,
                status,
                opened,
                closed,
                opened,
                opened,
            )
        )
        # messages  avg 4 => 12000/3000
        pair = rng.choice(TICKET_TEMPLATES[code])
        agent = rng.choice(agents)
        msg_time = opened
        messages.append(
            (uid(rng), tid, "player", meta["player_id"], None, pair[0], msg_time, msg_time, msg_time)
        )
        msg_time += timedelta(minutes=rng.randint(5, 90))
        messages.append(
            (uid(rng), tid, "agent", None, agent[0], pair[1], msg_time, msg_time, msg_time)
        )
        # extra back-and-forth
        extra = rng.randint(1, 3)
        for i in range(extra):
            msg_time += timedelta(minutes=rng.randint(5, 120))
            if i % 2 == 0:
                messages.append(
                    (
                        uid(rng),
                        tid,
                        "player",
                        meta["player_id"],
                        None,
                        "好的，我补充一下信息，麻烦尽快处理。",
                        msg_time,
                        msg_time,
                        msg_time,
                    )
                )
            else:
                messages.append(
                    (
                        uid(rng),
                        tid,
                        "agent",
                        None,
                        agent[0],
                        "已收到，我们正在核查相关订单与角色状态，请稍候。",
                        msg_time,
                        msg_time,
                        msg_time,
                    )
                )
        # assignment
        assignments.append(
            (uid(rng), tid, agent[0], "初次分配", opened, closed, opened, opened)
        )
        if meta["vip"] >= 6 and rng.random() < 0.3:
            agent2 = rng.choice(agents[:5])
            assignments.append(
                (
                    uid(rng),
                    tid,
                    agent2[0],
                    "VIP升级处理",
                    opened + timedelta(hours=1),
                    closed,
                    opened,
                    opened,
                )
            )
        if status in {"resolved", "closed"}:
            resolutions.append(
                (
                    uid(rng),
                    tid,
                    agent[0],
                    "resolved_ok",
                    f"已处理{subject}，核查完毕并回复玩家。",
                    closed or opened,
                    opened,
                    opened,
                )
            )
            if rng.random() < 0.7:
                csats.append(
                    (
                        uid(rng),
                        tid,
                        meta["player_id"],
                        rng.randint(3, 5) if meta["tier"] != "whale" else rng.randint(2, 5),
                        "处理及时，感谢。" if rng.random() < 0.6 else "希望加快到账处理。",
                        closed or opened,
                        opened,
                        opened,
                    )
                )

    # pad messages if needed
    while len(messages) < TARGETS["ticket_messages"]:
        if not tickets:
            break
        t = rng.choice(tickets)
        agent = rng.choice(agents)
        ts = t[11] + timedelta(minutes=rng.randint(1, 500))
        if ts > NOW:
            ts = NOW
        messages.append(
            (
                uid(rng),
                t[0],
                "system",
                None,
                None,
                "系统提醒：工单仍在处理中，请关注最新回复。",
                ts,
                ts,
                ts,
            )
        )

    ds.tables["support.tickets"] = tickets
    ds.tables["support.ticket_messages"] = messages
    ds.tables["support.ticket_assignments"] = assignments
    ds.tables["support.ticket_resolution_records"] = resolutions
    ds.tables["support.customer_satisfaction"] = csats

    # finalize counts
    for name, rows in ds.tables.items():
        short = name.split(".", 1)[1]
        ds.counts[short] = len(rows)

    return ds


def _level_for_tier(rng: random.Random, tier: str, activity: float) -> int:
    base = {"free": 12, "light_payer": 25, "mid_payer": 45, "whale": 70}[tier]
    level = int(rng.gauss(base * activity / 0.7, 8))
    return max(1, min(100, level))


def summarize(ds: Dataset) -> str:
    lines = ["Generated table counts:"]
    for k in sorted(ds.counts):
        target = TARGETS.get(k)
        mark = ""
        if target is not None:
            mark = " OK" if ds.counts[k] >= target else f" < target {target}"
        lines.append(f"  {k}: {ds.counts[k]}{mark}")
    return "\n".join(lines)


if __name__ == "__main__":
    dataset = build_dataset()
    print(summarize(dataset))
