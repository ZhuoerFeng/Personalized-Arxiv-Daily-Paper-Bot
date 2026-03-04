import os
import requests
import fitz  # PyMuPDF
from pathlib import Path
import logging
import re

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


def extract_main_text_from_pdf(filepath: str, max_pages: int = 15) -> str:
    """
    智能解析 PDF 正文：兼容双栏/单栏排版，并自动在 References 处截断。
    """
    logger.info(f"正在进行智能解析 (支持双栏识别): {filepath}")
    doc = fitz.open(filepath)
    pages_to_read = min(max_pages, len(doc))
    full_text = ""

    for page_num in range(pages_to_read):
        page = doc.load_page(page_num)
        page_width = page.rect.width
        
        # 提取文本块: (x0, y0, x1, y1, text, block_no, block_type)
        blocks = page.get_text("blocks")
        
        left_col = []
        right_col = []
        single_col = []

        for b in blocks:
            if b[6] == 0:  # 确保是文本块
                # 简单启发式：如果文本块跨越了页面中线，认为是单栏（如标题、摘要）
                if b[0] < page_width * 0.4 and b[2] > page_width * 0.6:
                    single_col.append(b)
                # 否则按中线分为左右两栏
                elif b[0] < page_width / 2:
                    left_col.append(b)
                else:
                    right_col.append(b)
        
        # 单独按 Y 轴 (垂直方向) 排序
        single_col.sort(key=lambda b: b[1])
        left_col.sort(key=lambda b: b[1])
        right_col.sort(key=lambda b: b[1])
        
        # 拼装顺序：先放顶部的单栏（通常是标题），然后左栏，最后右栏
        for b in single_col + left_col + right_col:
            full_text += b[4] + "\n"

    doc.close()

    # 在参考文献处截断 (兼容多种常见格式)
    ref_pattern = re.compile(r'\n(References|REFERENCES|Bibliography)\b')
    ref_match = ref_pattern.search(full_text)
    if ref_match:
        logger.info(f"在第 {ref_match.start()} 字符处检测到参考文献，已截断。")
        full_text = full_text[:ref_match.start()]

    return full_text

