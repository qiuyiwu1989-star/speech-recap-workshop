# 实录工坊 · Speech Recap Workshop

将演讲、培训、读书会的逐字稿整理成忠实的现场实录。独立本地应用，提供稿件管理、AI 初稿、人工编辑、脱敏疑点提醒与 Markdown / HTML 导出。

## 快速开始

需要 Python 3.10 或更新版本。

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python workshop.py
```

打开 http://127.0.0.1:8770 。Windows 使用 `.venv\Scripts\activate` 激活环境。

1. 新建稿件，导入 `examples/transcript.md`（完全虚构）。
2. 选择“生成离线演示”，无需模型或费用；此模式只复制原文，不是真正的 AI 整理。
3. 采用初稿，在人工编辑区修改。
4. 对照原稿核对事实与脱敏疑点，勾选复核并保存。
5. 导出 Markdown 或安全处理后的 HTML。

## 连接模型

支持 OpenAI-compatible Chat Completions API。启动前设置环境变量：

```sh
export RECAP_API_BASE=https://your-provider.example/v1
export RECAP_MODEL=your-model-name
# 在本机安全设置 RECAP_API_KEY，不要提交凭证到 Git。
python workshop.py
```

仅在点击“发送至模型并整理”并确认后发送该篇标题和逐字稿。可能产生模型费用；请使用供应商侧预算限制。默认不读取其他项目的凭据，不自动加载 `.env`。调用超时为 180 秒，输出上限 16000 tokens；输出截断会报错，不保存残稿。长篇稿件目前需要人工分段导入，不具备自动分块合并。

## 数据与运行边界

- 稿件保存在 `~/.speech-recap-workshop/drafts.sqlite3`，备份该文件即可。可用 `RECAP_DATA_DIR` 指定目录。
- `RECAP_PORT` 默认为 8770。仅监听本机；无多用户身份系统，不适合直接暴露公网。
- 原始逐字稿、引擎初稿、人工正文分开保存；重新生成不覆盖人工正文。
- 编辑后需重新复核；导出仅使用已保存且已复核的人工正文。
- 脱敏规则仅提示手机号、身份证、邮箱、机构名与职务指代，无法证明“已经无敏感内容”。
- HTML 导出禁用脚本、图片、链接及样式等外部资源，仅保留文章基础排版。
- 不自带录音转写、PPT 配图、多人协作或自动发布。个人网站发布适配未包含在首版。

## 测试

```sh
python -m unittest discover -s tests -v
```

真实模型请求需使用者配置服务验证；自动化测试不调用外部模型。

## 来源

从 [qiuyiwu-site](https://github.com/qiuyiwu1989-star/qiuyiwu-site) 的实录工坊工作流拆分，重新实现独立存储、界面与模型接入。保留“忠实记录、人工终审、引擎不覆盖人工正文”的原则。无个人站历史、真实稿件或部署凭据。

当前公开源码供审阅；正式开源许可证尚待作者选定，未授予额外使用许可。

## 来源复核与版本（开发中）

编辑台现在提供原文稳定行号、人工信息清单、正文原句定位和四种保留状态。保留项必须引用已保存正文中的原句；正文变化会将已有信息点重置为待核。统计仅覆盖人工列出的信息点，不代表整场讲话的完整度。来源对照留在本地，不随公开正文导出。

每次正文变化前保存历史快照，可查看与当前正文的逐行差异。暂不提供自动信息提取、语义遗漏识别、版本恢复按钮和并发编辑保护。信息清单中存在“待核”项时，不能完成最终复核或导出。尚未强制要求建立清单；未列出的信息不在统计范围内。

## Agent + MCP（推荐入口，v0.2.0）

由当前 Agent 整理内容；MCP 负责本地材料、来源清单、正文版本和待审包，无需另外配置模型 API。Skill 方法放在 `skills/speech-record-workshop/`，跟随 Git 版本迭代；客户端需要安装该 Skill 或明确加载它。仅接 MCP 不保证客户端自动遵守 Skill。

```sh
python3.12 -m venv .venv-mcp
.venv-mcp/bin/pip install -r requirements-mcp.txt
.venv-mcp/bin/python mcp_server.py
```

这是 stdio 服务，不监听公网端口。在支持 MCP 的客户端配置中使用绝对路径（替换下方目录）：

```json
{"mcpServers":{"speech-recap-workshop":{"command":"/absolute/path/speech-recap-workshop/.venv-mcp/bin/python","args":["/absolute/path/speech-recap-workshop/mcp_server.py"],"env":{"RECAP_DATA_DIR":"/absolute/path/private-recap-data"}}}}
```

可用工具：`workshop_method`、`workshop_list`、`workshop_create`、`workshop_read`、`workshop_save_body`、`workshop_save_evidence`、`workshop_version`、`workshop_review_package`。同一数据目录可供原本地界面查看；不要并发编辑同一篇稿件，首版尚无跨客户端冲突锁。MCP 不连接个人网站生产后台，不自动发布。当前方法指纹不能冒充历史执行证明。

协议验收：`.venv-mcp/bin/python tests/mcp_smoke.py`。MCP 环境要求 Python 3.10+，推荐 3.12。
