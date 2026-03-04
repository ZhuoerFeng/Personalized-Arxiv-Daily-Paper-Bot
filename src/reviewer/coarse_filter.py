import json
import re
import math
from pydantic import BaseModel, Field
# 引入你封装的 API 网关
from src.llmapi.model import GateWays

# ---------------------------------------------------------
# 1. 定义数据结构 (用于本地校验和类型提示)
# ---------------------------------------------------------
class PaperScore(BaseModel):
    paper_id: int
    relevance_score: int  # 替换原来的 score
    quality_score: int    # 新增质量分
    reason: str

# ---------------------------------------------------------
# 2. 辅助函数：安全解析 LLM 返回的 JSON
# ---------------------------------------------------------
def extract_json_from_text(text: str) -> dict:
    """
    从 LLM 返回的文本中安全提取 JSON。
    处理模型可能包裹的 ```json ... ``` markdown 格式。
    """
    try:
        # 尝试直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        # 如果失败，尝试用正则提取 markdown 代码块中的 JSON
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)

    if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    # 如果都失败了，抛出异常或返回空结构
    raise ValueError(f"无法从模型输出中解析 JSON:\n{text}")

# ---------------------------------------------------------
# 3. 批量粗筛核心函数
# ---------------------------------------------------------
def batch_coarse_filter(papers: list[dict], keywords: list[str], model_name: str = "gemini-2.5-pro", batch_size: int = 10) -> list[dict]:
    """
    对抓取到的论文列表进行批量粗筛。
    """
    # 实例化你的 API 网关
    gateway = GateWays(model_name=model_name)
    
    scored_papers = []
    total_batches = math.ceil(len(papers) / batch_size)
    
    print(f"总计 {len(papers)} 篇论文，将分为 {total_batches} 个批次进行粗筛...")

    # 为每篇论文分配一个临时的 index 作为 paper_id
    for index, paper in enumerate(papers):
        paper["_temp_id"] = index

    for i in range(0, len(papers), batch_size):
        batch = papers[i:i + batch_size]
        current_batch_num = (i // batch_size) + 1
        print(f"正在处理第 {current_batch_num}/{total_batches} 批...")

        # 构建当前批次的文本内容
        batch_text = ""
        for p in batch:
            batch_text += f"ID: {p['_temp_id']} | Title: {p['title']} | Abstract: {p['summary']}\n"

        # 构建严谨的 Prompt，强制要求 JSON 输出格式
        system_prompt = """
你是一个专业的学术会议初审委员。请根据用户提供的预设关键词，评估论文的【相关性】与【研究质量】。

【维度一：相关度打分标准 (1-5分)】
5分: 强相关，核心贡献直接针对关键词。
4分: 相关，关键词技术是其主要工具或解决其子问题。
3分: 中度相关，边缘提及，作为对比实验或背景。
2分: 弱相关，偶然提及术语，关联极小。
1分: 完全不相关。

【维度二：质量信号打分标准 (1-5分)】
评估摘要中透露出的扎实程度与价值。
5分: 极强信号。明确提供开源代码/数据/权重链接（不包括例如 will be open soured 的承诺开源）；或提出了突破性的理论证明；或包含详尽且突破性的量化指标。
4分: 强信号。包含清晰的对比基线（Baselines），有具体的量化提升数据，方法论阐述清晰，不空泛。
3分: 中等信号。标准的学术摘要，有方法有实验，但缺乏明确的量化数字或开源承诺。
2分: 弱信号。概念堆砌（如 A+B 模型），缺乏具体实验结果描述，或仅仅是应用型水文。
1分: 极差信号。逻辑混乱，完全没有结果支撑，或纯粹的综述/观点拼凑（除非关键词明确要求综述）。

【输出格式要求】
你必须且只能输出一个合法的 JSON 对象，不要包含任何额外的解释说明文字。JSON 格式如下：
{
    "results": [
        {
            "paper_id": 0, 
            "relevance_score": 4, 
            "quality_score": 5,
            "reason": "相关因为用了XXX技术；质量高因为明确提到开源代码且提升15%(25字内)"
        }
    ]
}
        """

        user_prompt = f"""
        【预设关键词】
        {", ".join(keywords)}

        【待评估论文列表】
        {batch_text}
        """

        # 组装 messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # 调用你封装的网关方法 (建议设置较低的 temperature 保证 JSON 稳定性)
            response = gateway.get_api_result(
                messages=messages, 
                temperature=0.1, 
                max_completion_tokens=2000 # 确保 token 足够输出一个批次的 JSON
            )
            
            # 获取模型输出的文本
            content = response.choices[0].message.content
            
            # 提取并解析 JSON
            result_data = extract_json_from_text(content)
            
            # 将打分结果合并回原始论文字典中
            for score_info in result_data.get("results", []):
                # 利用 Pydantic 进行数据校验
                validated_score = PaperScore(**score_info)
                
                # 找到对应的原论文
                original_paper = next((p for p in batch if p["_temp_id"] == validated_score.paper_id), None)
                if original_paper:
                    # 分别记录相关性分数、质量分数和理由
                    original_paper["relevance_score"] = validated_score.relevance_score
                    original_paper["quality_score"] = validated_score.quality_score
                    original_paper["reason"] = validated_score.reason
                    
                    scored_papers.append(original_paper)

        except Exception as e:
            print(f"批次 {current_batch_num} 处理失败: {e}")
            # 容错：如果失败可以跳过或记录日志，避免整个脚本中断

    # 清理临时 ID
    for p in scored_papers:
        p.pop("_temp_id", None)
        
    # 多级排序：优先按照 relevance_score 降序，如果 relevance_score 相同，则按照 quality_score 降序
    scored_papers.sort(
        key=lambda x: (x.get("relevance_score", 0), x.get("quality_score", 0)), 
        reverse=True
    )
    
    return scored_papers

