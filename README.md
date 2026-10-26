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
