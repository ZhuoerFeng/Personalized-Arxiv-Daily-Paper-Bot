# 🤖 PaperAgent: ArXiv 每日论文智能审稿与订阅系统

PaperAgent 是一个自动化的多智能体工作流项目。它能够每天定时从 ArXiv 抓取指定领域的最新论文，利用大语言模型（如 Gemini / GPT 等）根据你自定义的关键词进行“相关度”与“质量”的双重打分，最后生成精美的 HTML 战报，并通过邮件一键推送到多个订阅者的邮箱，同时在本地进行归档备份。

## ✨ 核心特性

- **🎯 精准抓取 (Fetcher)**: 调用 ArXiv API 自动获取过去 24 小时内特定领域（如 `cs.AI`, `cs.CL`）的最新论文。
- **🧠 AI 智能粗筛 (Reviewer)**: 使用大模型（默认 `gemini-2.5-pro`）对论文摘要进行批量评估，根据预设的关键词输出结构化评分（相关度 & 质量）。
- **🕵️‍♂️ 全文深度审稿 (Deep Reviewer) `[NEW!]`**: 自动下载高分论文的 PDF，智能解析双栏/单栏排版（最多提取前 15 页并自动在 References 处截断）。随后依据 ICML 官方审稿准则，从 *Soundness, Presentation, Significance, Originality* 四个维度给出详细的图文评价、优缺点分析及最终录用推荐。
- **📊 动态排版与多用户推送 (Notifier)**: 基于 Jinja2 引擎渲染高颜值的 HTML 每日战报，并支持通过 SMTP 服务群发给多个用户。
- **💾 本地数据沉淀**: 自动将每日的 AI 过滤打分结果存为 `JSON`，将战报存为 `HTML`，方便后续用于 RAG 知识库检索或网页端展示。

---

## 🏗️ 系统架构

项目的执行流水线如下：
1. **获取 (Fetch)** -> 2. **打分 (Review)** -> 3. **排序 (Rank)** -> 4. **推送与归档 (Notify & Archive)**


---

## 🚀 快速开始

### 1. 环境准备

确保你的机器上安装了 Python 3.9+，然后克隆项目并安装依赖：

```bash
git clone [https://github.com/yourusername/paperagent.git](https://github.com/yourusername/paperagent.git)
cd paperagent
pip install -r requirements.txt
```

### 2. 配置环境变量 (.env)

在项目根目录下创建一个 `.env` 文件，填入你的大模型 API 密钥以及发信邮箱的 SMTP 配置。

代码段

```
# 大模型 API 配置 (根据 src/llmapi/model.py 里的具体网关逻辑配置)
LLM_API_KEY="sk-xxxxxx"
LLM_BASE_URL="[https://api.your-gateway.com/v1](https://api.your-gateway.com/v1)"

# 邮件 SMTP 配置 (以 QQ 邮箱或网易邮箱为例)
SMTP_HOST="smtp.qq.com"  # 或者是 smtp.163.com, smtp.gmail.com 等
SMTP_PORT=465            # SSL 端口通常为 465
SMTP_USERNAME="your_sender_email@qq.com"
SMTP_PASSWORD="你的邮箱授权码" # 注意：这里填的是授权码，不是登录密码！

# 接收者邮箱配置 (支持多个邮箱，用英文逗号分隔)
RECEIVER_EMAILS="alice@example.com, bob@example.com"
```

> **💡 关于邮箱授权码 (App Password) 的获取：**
>
> - **QQ邮箱**：设置 -> 账号 -> POP3/IMAP/SMTP/Exchange服务 -> 开启 SMTP -> 生成授权码。
> - **Gmail**：Google 账号 -> 安全性 -> 两步验证 -> 应用专用密码 (App Passwords) -> 生成 16 位字符。

### 3. 自定义检索规则

打开 `main.py`，在 `main()` 函数开头找到**配置区**，你可以根据自己的研究方向修改：

Python

```
TARGET_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG"] # ArXiv 领域代码
KEYWORDS = ["LLM Agent", "Reasoning", "Reinforcement Learning"] # 你的关注点
MIN_SCORE_THRESHOLD = 5 # 触发推送的最低分数线
MODEL_NAME = "gemini-2.5-pro" # 调用的具体模型名
```

### 4. 运行 Agent

你可以通过以下命令直接运行一次测试：

Bash

```
python main.py
```

如果你只想测试邮件发送配置是否正确，可以运行：

Bash

```
python test_real_email.py
```

------

## 📂 目录结构

Plaintext

```
paperagent/
├── data/                        # 自动生成的本地数据 (已在 .gitignore 中忽略)
│   ├── pdfs/                    # 论文 PDF 缓存
│   ├── reports/                 # 每日生成的 HTML 战报 (daily_report_YYYY-MM-DD.html)
│   └── reviews/                 # AI 每日打分结果 (filter_results_YYYY-MM-DD.json)
├── src/                         
│   ├── fetcher/                 # 负责 API 请求与 PDF 抓取
│   ├── llmapi/                  # 大模型请求网关封装
│   ├── reviewer/                # Prompt 构建与批量打分逻辑
│   ├── ranker/                  # 数据清洗与排序逻辑
│   └── notifier/                # Jinja2 模板与 SMTP 邮件发送
├── .env                         # 环境变量 (不要提交到 Git)
├── main.py                      # 工作流主调度入口
└── requirements.txt             # 项目依赖
```

------

## 🛠️ 接下来：自动化部署建议

如果你希望让它每天自动运行，可以通过以下两种方式部署：

1. **Linux Crontab**: 适合有一台一直开机的云服务器（例如每天早晨 8 点运行：`0 8 * * * cd /path/to/paperagent && python main.py`）。
2. **GitHub Actions**: 利用 `.github/workflows/daily_run.yml` 配置 Cron Job，白嫖 GitHub 的算力自动发邮件。
