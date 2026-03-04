import os
import requests
import fitz  # PyMuPDF
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def download_pdf(pdf_url: str, paper_id: str, save_dir: str = "data/pdfs") -> str:
    """
    从 ArXiv 下载 PDF 到本地目录
    """
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    # 清理 paper_id 中可能包含的版本号 (例如: 2403.12345v1 -> 2403.12345)
    clean_id = paper_id.split('v')[0]
    filepath = os.path.join(save_dir, f"{clean_id}.pdf")
    
    # 如果本地已经有缓存，则直接返回路径，避免重复下载
    if os.path.exists(filepath):
        logger.info(f"PDF 已存在缓存: {filepath}")
        return filepath
        
    logger.info(f"正在下载 PDF: {pdf_url} -> {filepath}")
    response = requests.get(pdf_url, stream=True)
    response.raise_for_status() # 检查请求是否成功
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    return filepath

def extract_text_from_pdf(filepath: str, max_pages: int = None) -> str:
    """
    使用 PyMuPDF 提取 PDF 文本。
    
    :param filepath: PDF 本地路径
    :param max_pages: 限制最大读取页数 (为了省Token，比如有些论文后面的 Appendix 特别长，可以限制只读前 15 页)
    """
    logger.info(f"正在解析 PDF 文本: {filepath}")
    doc = fitz.open(filepath)
    text = ""
    
    # 确定要读取的页数
    pages_to_read = min(max_pages, len(doc)) if max_pages else len(doc)
    
    for page_num in range(pages_to_read):
        page = doc.load_page(page_num)
        # 提取文本，并做简单的清洗
        page_text = page.get_text("text")
        text += f"\n--- Page {page_num + 1} ---\n"
        text += page_text
        
    doc.close()
    return text