
```
arxiv_daily_reviewer/
├── .github/
│   └── workflows/
│       └── daily_run.yml        # [部署] GitHub Actions 定时任务配置文件 (Cron job)
├── data/                        # [本地存储] 临时数据目录 (务必在 .gitignore 中忽略)
│   ├── pdfs/                    # 存放自动下载的论文 PDF 文件
│   └── reviews/                 # 存放 Agent 输出的中间评审结果 (JSON 格式)
├── src/                         # [核心代码]
│   ├── __init__.py
│   ├── config.py                # 全局配置管理 (如设定的 ArXiv 领域代码、打分阈值等)
│   ├── fetcher/                 # -> 模块一：精准收集
│   │   ├── __init__.py
│   │   ├── arxiv_client.py      # 负责调用 ArXiv API 获取昨日最新论文列表及元数据
│   │   └── pdf_parser.py        # 负责下载 PDF 并提取文本 (支持 PyMuPDF 等)
│   ├── reviewer/                # -> 模块二：多智能体审稿系统
│   │   ├── __init__.py
│   │   ├── graph.py             # 定义 Agent 之间的流转逻辑 (如果是 LangGraph)
│   │   ├── agents.py            # 实例化不同的 LLM Agent (初筛员、精读专家、Meta-Reviewer)
│   │   ├── prompts.py           # 集中管理所有 Prompt (避免将大段文本混在业务代码里)
│   │   └── schemas.py           # 定义 Pydantic Models，强制 LLM 输出格式化的 JSON
│   ├── ranker/                  # -> 模块三：聚合与排序
│   │   ├── __init__.py
│   │   └── sorter.py            # 读取 reviews/ 下的 JSON，执行降序排序并选出 Top K
│   ├── notifier/                # -> 模块四：生成战报与推送
│   │   ├── __init__.py
│   │   ├── email_sender.py      # 封装 SMTP 邮件发送逻辑
│   │   └── templates/
│   │       └── daily_report.html # Jinja2 模板文件，用于渲染最终美观的邮件排版
│   └── main.py                  # [入口文件] 调度器，负责把 1->2->3->4 串联起来执行
├── .env.example                 # 环境变量模板 (包含各种 API Key 和邮箱密码字段的占位符)
├── .gitignore                   # 告诉 Git 忽略哪些文件 (如 .env, venv/, data/ 等)
├── requirements.txt             # 项目依赖项 (如 langchain, google-genai, arxiv, jinja2)
└── README.md                    # 项目说明文档，记录如何本地运行和配置
```


## QA：获取邮箱的“授权码” (App Password)

为了安全，现在几乎所有的邮箱都不允许第三方脚本直接用“登录密码”发邮件，而是需要生成一串专用的“授权码”。

- **如果是 QQ 邮箱**：登录网页版 -> 设置 -> 账号 -> 找到“POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务” -> 开启“POP3/SMTP服务” -> 点击“生成授权码”。你会得到一串英文字母（如 `abcdxyz...`），把它填到 `.env` 的 `SMTP_PASSWORD` 里。
- **如果是 网易 163 邮箱**：登录网页版 -> 设置 -> POP3/SMTP/IMAP -> 开启 SMTP 服务 -> 新增授权码。
- **如果是 Gmail**：登录 Google 账号 -> 安全性 -> 开启“两步验证” -> 搜索“应用专用密码” (App Passwords) -> 创建一个名为 "Python" 的密码，得到一串 16 位的字符，填入 `SMTP_PASSWORD`。

