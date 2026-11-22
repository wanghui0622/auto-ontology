-- StarSea Gaming Data Platform
-- Stage 2: schemas and extensions
-- Database: starsea_gaming (created by Docker / createdb)

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS game;
CREATE SCHEMA IF NOT EXISTS mall;
CREATE SCHEMA IF NOT EXISTS payment;
CREATE SCHEMA IF NOT EXISTS support;
CREATE SCHEMA IF NOT EXISTS marketing;

COMMENT ON SCHEMA identity IS '玩家账户与身份域：统一玩家主体、游戏账号、设备、标签与注册来源';
COMMENT ON SCHEMA game IS '游戏运营域：游戏、区服、角色、会话、任务、战斗、道具定义与行为事件';
COMMENT ON SCHEMA mall IS '游戏商城域：商品、订单、退款与道具发放';
COMMENT ON SCHEMA payment IS '充值与支付域：支付渠道、充值订单、交易流水、钱包与账本';
COMMENT ON SCHEMA support IS '游戏客服域：坐席、工单、消息、分配、结案与满意度';
COMMENT ON SCHEMA marketing IS '运营推广域：推广渠道、活动、投放成本、归因、参与与奖励';
