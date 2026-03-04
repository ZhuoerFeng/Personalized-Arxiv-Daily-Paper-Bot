import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# 1. 初始化路径与环境变量
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
load_dotenv(os.path.join(project_root, '.env'))

from src.fetcher.arxiv_client import fetch_daily_papers
from src.reviewer.coarse_filter import batch_coarse_filter
from src.notifier.email_sender import EmailNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ArXivAgent")

def main():
    logger.info("🚀 启动 ArXiv 每日论文速递 Agent...")

    # 配置区
    TARGET_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG"]
    KEYWORDS = ["Benchmark", "Evaluation", "Reward Model", "LLM Agent", "Memory", 'Long Context', "Reasoning", "Reinforcement Learning", 'Creative Writing'] # 粗筛关键词
    MIN_SCORE_THRESHOLD = 5
    RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
    MODEL_NAME = "gemini-2.5-pro" 
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # ==========================================
    # 步骤 1: 抓取最新论文
    # ==========================================
    logger.info(f"👉 步骤 1: 正在抓取 {TARGET_CATEGORIES} 领域的最新论文...")
    raw_papers = fetch_daily_papers(categories=TARGET_CATEGORIES, days_back=1, max_results=150)
    
    total_scanned = len(raw_papers)
    high_value_papers = [] # 初始化为空列表
    total_tokens_consumed = 0

    # 逻辑分流：如果抓到了论文，才去打分；否则直接跳到发信步骤
    if total_scanned == 0:
        logger.warning("今天没有获取到任何新论文，跳过 AI 打分环节，准备发送空战报...")
    else:
        # ==========================================
        # 步骤 2: AI 批量粗筛打分
        # ==========================================
        logger.info(f"👉 步骤 2: 正在交由 {MODEL_NAME} 进行相关度粗筛打分...")
        scored_papers, total_tokens_consumed = batch_coarse_filter(
            papers=raw_papers, 
            keywords=KEYWORDS, 
            model_name=MODEL_NAME, 
            batch_size=50
        )
        high_value_papers = [p for p in scored_papers if p.get("relevance_score", 0) >= MIN_SCORE_THRESHOLD]
        high_value_papers = [p for p in high_value_papers if p.get("quality_score", 0) >= MIN_SCORE_THRESHOLD]
        logger.info(f"粗筛完成: 扫描 {total_scanned} 篇，命中 {len(high_value_papers)} 篇高分论文。")
        logger.info(f"💰 本次运行总计消耗 Token: {total_tokens_consumed}")
    # ==========================================
    # 步骤 3: 渲染 HTML 邮件模板
    # ==========================================
    logger.info("👉 步骤 3: 正在生成战报...")
    template_dir = os.path.join(project_root, 'src', 'notifier', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('daily_report.html')

    template_data = {
        "date": today_str,
        "keywords": ", ".join(KEYWORDS),
        "total_scanned": total_scanned,
        "papers": high_value_papers,
        "total_tokens": total_tokens_consumed
    }
    
    html_content = template.render(**template_data)

    # ==========================================
    # 步骤 4: 发送邮件
    # ==========================================
    logger.info("👉 步骤 4: 正在推送邮件...")
    notifier = EmailNotifier()
    
    # 可以在标题里加上直观的提示，让你不点开邮件就知道今天有没有干货
    if len(high_value_papers) > 0:
        subject = f"🚀 ArXiv 顶分论文速递 - 命中 {len(high_value_papers)} 篇 ({today_str})"
    else:
        subject = f"📭 ArXiv 每日速递 - 今日暂无匹配 ({today_str})"
        
    success = notifier.send_email(
        receiver_email=RECEIVER_EMAIL,
        subject=subject,
        html_content=html_content
    )

    if success:
        logger.info("✅ 整个工作流执行完毕，邮件发送成功！")
    else:
        logger.error("❌ 邮件发送失败，请检查 notifier 模块。")

if __name__ == "__main__":
    main()