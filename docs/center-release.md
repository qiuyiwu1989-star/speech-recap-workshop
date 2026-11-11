# 实录工坊接入 MCP 管家：上线记录

统一入口 https://qiuyiwu.com/mcp；管理入口 /admin/mcp/。已定向修改线上 extra_domains.py、center.py、http_server.py 并安装 recap_adapter.py，保留 vault_ontology_adapter 注册及其他领域。

网关与管理服务均 active。存储位于 /opt/livepage/state/mcp/recap-data，服务用户拥有0700权限。复用原 MCP_CENTER_OWNER 绑定，不输出其值。仅增加本域环境配置，不改既有密钥、不自动扩大个人授权。

首次写入因 ProtectSystem=strict 与目录不在 ReadWritePaths 内失败；已将目录移入现有获准写入的中心 state/mcp 下，未放宽安全限制。重启后首次探测遇短暂502，服务就绪后完整重测通过。

公网验收使用服务器内临时受限钥匙和合成资料：initialize、工具发现、创建、同请求幂等、旧revision拒绝、同钥匙vault_archive_rules调用、知识底座工具存在、撤回写权后隐藏与直接调用拒绝、撤销钥匙401。测试钥匙、合成稿件、历史与收据已清理。没有读取真实私人稿件。

旧文件备份：/opt/livepage/state/mcp/recap-backup-20261111-224456。回退应先对比当前线上文件以避免覆盖后续变更；恢复本次三份旧源码、撤下recap环境配置并重启两项服务，保留领域数据库。

限制：未验收登录后的管理页点击及具体Agent客户端；现有个人钥匙仍需在管家显式授权read/create/revise。中心首版提供5项工具，不含网页发布、确认、历史读取或旧本地稿件自动迁移。旧本地stdio暂作开发兼容入口，不是生产推荐入口。
