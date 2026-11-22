# StarSea Gaming Data Platform（星海互动游戏数据平台）

面向 NVIDIA Auto-Ontology 的游戏行业自动本体化示范数据库。

本项目**只构建业务数据库与说明文档**，不修改 Auto-Ontology 源码或配置。Auto-Ontology 通过只读连接发现 Schema、外键与 COMMENT，再自动生成本体。

## 当前阶段

**Stage 1：业务建模（待确认）**

已产出：

| 文档 | 说明 |
|---|---|
| [`docs/business-overview.md`](./docs/business-overview.md) | 业务背景与主流程 |
| [`docs/domain-model.md`](./docs/domain-model.md) | 六大业务域与核心实体 |
| [`docs/business-relationships.md`](./docs/business-relationships.md) | 跨域关系与标识约定 |
| [`docs/er-diagram.mmd`](./docs/er-diagram.mmd) | 完整 ER 图（Mermaid） |
| [`docs/stage1-review.md`](./docs/stage1-review.md) | Stage 1 确认清单与开放决策点 |

确认本阶段模型后，再进入 Stage 2（DDL）与后续数据生成。

## 目标数据库

- 引擎：PostgreSQL 17
- 库名：`starsea_gaming`
- Schema：`identity` / `game` / `mall` / `payment` / `support` / `marketing`

## 原则

1. 不以手工 Terms / Relationships / SQL Attributes 预置本体。
2. 以原生主键、外键、约束、COMMENT 与一致性数据承载语义。
3. 金额一律 `NUMERIC`，时间一律 UTC。
4. 与 Auto-Ontology 主项目隔离：独立 Compose、独立库、独立用户。
