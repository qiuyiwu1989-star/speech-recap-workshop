# MCP 管家接入候选

service_id：recap；部署归个人网站 MCP 管家维护。统一用户入口仍是 https://qiuyiwu.com/mcp，使用既有个人钥匙。

## 已实现与限制

- 固定本地适配器，提供 recap_list/read/create/revise/evidence；read、create、revise 分开授权。无确认、发布、删除、付费模型动作。
- owner 从中心可信身份解析；服务器 RECAP_CENTER_OWNER 必须等于 MCP_CENTER_OWNER。调用参数不能传 owner/actor。
- 私有 SQLite 以 owner 哈希隔离；版本前置条件、事务历史和 request_id 幂等收据。request_id 重用但参数不同拒绝。错误不返回正文或凭据。
- 上限：请求 1MB、结果 2MB、正文/原文各10万字符、证据1000项、列表100条。当前列表无翻页，历史已保存但中心尚无历史读取工具。
- 配置 RECAP_CENTER_DATA 为服务器私有绝对目录、RECAP_CENTER_OWNER 为既有中心 owner。目录由服务用户所有，部署时设置0700。不复制本机原稿或旧SQLite；这是新的中心存储，迁移需另行核对。
- 中心审计沿用服务/工具/主体/结果元数据；原文及幂等结果仅存在私有领域库，不进入审计日志。

## 验证

领域适配与原有工作坊7项测试通过。管家注册/跨域/owner回归5项通过。gateway_smoke.py 验证SDK工具发现、写操作标注、实际创建分发和即时撤权。

## 部署流程

1. 取得最新生产中心代码，特别保留2026-11-09已上线的vault ontology插件；不能直接推送本机LivePage脏工作区。
2. 用install_adapter.py在独立候选目录定向加入适配，安装jsonschema，运行隔离测试。脚本遇到不匹配的锚点停止。
3. 核对存储目录及owner配置；显式部署授权后发布，不重签现有钥匙。
4. 用户在管家对现有钥匙明确启用recap read/create/revise，再做公网同钥匙验收；默认不自动扩权。
5. 中心验收后再移除临时本地stdio注册。回退撤销recap授权、撤下适配；保留私有库和版本历史。

生产适配已上线并通过公网临时受限钥匙验收，见 center-release.md。现有个人钥匙未自动扩权；需在管家启用相应动作后发现工具。Skill仍以实际 tools/list 为准。
