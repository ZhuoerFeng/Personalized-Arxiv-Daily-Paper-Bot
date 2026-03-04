import arxiv
from datetime import datetime, timedelta, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_daily_papers(categories: list, days_back: int = 1, max_results: int = 1000) -> list:
    """
    获取指定领域最近 N 天发布的 ArXiv 论文。
    
    :param categories: 领域列表，如 ["cs.AI", "cs.CL"]
    :param days_back: 获取过去几天的论文（默认 1 天）
    :param max_results: 每次 API 请求的最大结果数
    :return: 包含论文元数据的字典列表
    """
    # 构建查询语句，例如: cat:cs.AI OR cat:cs.CL
    query = " OR ".join([f"cat:{cat}" for cat in categories])
    logger.info(f"正在查询 ArXiv，领域: {query}")
    
    # 初始化 ArXiv 客户端
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending # 按提交时间倒序
    )
    
    # 设定时间截止线（UTC时间，因为 ArXiv 使用 UTC）
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    
    papers = []
    for result in client.results(search):
        # 如果论文发布时间晚于截止时间，则收集
        if result.published >= cutoff_date:
            paper_info = {
                "id": result.get_short_id(),
                "title": result.title.replace('\n', ' '), # 清理标题换行
                "summary": result.summary.replace('\n', ' '),
                "authors": [a.name for a in result.authors],
                "published": result.published.strftime("%Y-%m-%d"),
                "pdf_url": result.pdf_url
            }
            papers.append(paper_info)
        else:
            # 因为结果是按时间倒序排列的，一旦遇到早于截止时间的论文，直接终止循环，节省时间
            break
            
    logger.info(f"成功获取 {len(papers)} 篇最近 {days_back} 天的新论文。")
    return papers

