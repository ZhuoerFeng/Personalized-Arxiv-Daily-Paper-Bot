import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import json
from src.fetcher.pdf_parser import download_pdf, extract_main_text_from_pdf
from src.reviewer.deep_reviewer import generate_icml_review

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
    # RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
    receiver_emails_str = os.getenv("RECEIVER_EMAILS", os.getenv("RECEIVER_EMAIL", ""))
    RECEIVER_EMAILS = [email.strip() for email in receiver_emails_str.split(",") if email.strip()]
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
        # 步骤 2.5: 对高分论文进行全文下载与深度审稿
        # ==========================================
        if len(high_value_papers) > 0:
            logger.info("👉 步骤 2.5: 正在对高分论文进行全文下载与深度审稿 (ICML 标准)...")
            for paper in high_value_papers:
                try:
                    # 1. 下载 PDF
                    pdf_path = download_pdf(paper['pdf_url'], paper['id'])
                    # 2. 提取正文
                    paper_text = extract_main_text_from_pdf(pdf_path, max_pages=15)
                    # 3. AI 审稿
                    review_result, review_tokens = generate_icml_review(paper_text, MODEL_NAME)
                    
                    if review_result:
                        paper['icml_review'] = review_result
                        total_tokens_consumed += review_tokens
                        logger.info(f"✅ 完成论文 {paper['id']} 的深度审稿 (推荐分: {review_result['overall_recommendation']}/6)")
                except Exception as e:
                    logger.error(f"❌ 处理论文 {paper['id']} 深度审稿时失败: {e}")

        logger.info(f"💰 本次运行 (含粗筛+精审) 总计消耗 Token: {total_tokens_consumed}")

        # ==========================================
        # 保存过滤结果 (JSON) 到本地
        # ==========================================
        reviews_dir = os.path.join(project_root, 'data', 'reviews')
        os.makedirs(reviews_dir, exist_ok=True)
        results_file = os.path.join(reviews_dir, f"filter_results_{today_str}.json")
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(scored_papers, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 过滤结果 JSON 已保存至: {results_file}")
        except Exception as e:
            logger.error(f"❌ 保存过滤结果失败: {e}")

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
    # 【新增】保存生成的战报 (HTML) 到本地
    # ==========================================
    reports_dir = os.path.join(project_root, 'data', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    report_file = os.path.join(reports_dir, f"daily_report_{today_str}.html")

    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"💾 每日战报 HTML 已保存至: {report_file}")
    except Exception as e:
        logger.error(f"❌ 保存 HTML 战报失败: {e}")

    # ==========================================
    # 步骤 4: 发送邮件
    # ==========================================
    logger.info("👉 步骤 4: 正在推送邮件...")
    if not RECEIVER_EMAILS:
        logger.warning("⚠️ 未配置收件人邮箱 (RECEIVER_EMAILS)，跳过邮件发送步骤。")
        return
    
    notifier = EmailNotifier()
    
    # 可以在标题里加上直观的提示，让你不点开邮件就知道今天有没有干货
    if len(high_value_papers) > 0:
        subject = f"🚀 ArXiv 顶分论文速递 - 命中 {len(high_value_papers)} 篇 ({today_str})"
    else:
        subject = f"📭 ArXiv 每日速递 - 今日暂无匹配 ({today_str})"
        
    # 循环发送给所有配置的用户
    success_count = 0
    for email_addr in RECEIVER_EMAILS:
        success = notifier.send_email(
            receiver_email=email_addr,
            subject=subject,
            html_content=html_content
        )
        if success:
            success_count += 1

    if success_count == len(RECEIVER_EMAILS):
        logger.info(f"✅ 整个工作流执行完毕，成功发送给 {success_count} 位用户！")
    else:
        logger.warning(f"⚠️ 邮件发送完成，但部分失败。成功: {success_count}/{len(RECEIVER_EMAILS)}。")


if __name__ == "__main__":
    main()