import json
import logging
from pydantic import BaseModel
from src.llmapi.model import GateWays
from src.reviewer.coarse_filter import extract_json_from_text

logger = logging.getLogger(__name__)

class ICMLReview(BaseModel):
    summary: str
    strengths_and_weaknesses: str
    soundness: int
    presentation: int
    significance: int
    originality: int
    questions_for_authors: str
    limitations: str
    overall_recommendation: int
    confidence: int

def generate_icml_review(paper_text: str, model_name: str = "gemini-2.5-pro") -> dict:
    """
    使用 ICML 审稿标准对论文全文进行评审。
    """
    gateway = GateWays(model_name=model_name)
    
    system_prompt = """
You are an expert AI researcher and a reviewer for ICML. 
Please review the provided paper text following the exact ICML Reviewer Guidelines.

----

Summary*
Briefly summarize the paper and its contributions. This is not the place to critique the paper; the authors should generally agree with a well-written summary. This is also not the place to paste the abstract; please provide the summary in your own understanding after reading.


Strengths And Weaknesses*
Please provide a thorough assessment of the strengths and weaknesses of the paper, touching on each of the following dimensions: soundness, presentation, significance, and originality. We encourage you to be open-minded about the potential strengths and broad definitions of significance and originality. For example, originality may arise from creative combinations of existing ideas, application to a real-world use case, or removing restrictive assumptions from prior theoretical results. We provide detailed guidelines below on each dimension:

Soundness: Is the submission technically sound? Are claims well supported (e.g., by theoretical analysis or experimental results)? Are the methods used appropriate? If the paper includes theoretical results, are the proofs correct and based on reasonable assumptions? If the paper includes empirical results, are the experiments well-designed? Are the authors careful and honest about evaluating both the strengths and weaknesses of their work? Note: Soundness is distinct from impact. A paper can be technically sound—meaning correct, rigorous, and methodologically appropriate—even if its contributions are modest or incremental. Conversely, a paper proposing a high-impact idea must still meet the same bar for technical soundness. Reviewers should assess these dimensions separately.
Presentation: Is the submission clearly written and well structured? (If not, please make constructive suggestions for improving its clarity.) Is the overall narrative easy to follow? Does the work properly position itself in the context of prior/concurrent literature and clearly discuss how it differs? (Note that a superbly written paper provides enough information for an expert reader to reproduce its results.)
Significance: Does the paper address an important or relevant problem? Does it advance understanding, capabilities, or practice in machine learning? Could it influence future research or applications (e.g., other researchers or practitioners are likely to use the ideas or build on them)? Is the scope of impact broad or specialized, and is that appropriate for the contribution? Even if the improvements are modest or domain-specific, could they unlock new directions or provide practical utility?
Originality: Does the work provide new insights, deepen understanding, or highlight important properties of existing methods? Does the work introduce new tasks, methods, theory, data, or perspectives that advance the field in some dimensions? Does this work offer a novel combination of existing techniques, and is the reasoning behind this combination well-articulated? Are the contributions clearly distinguished from closely related literature, and is the novelty well justified? As the questions above indicates, originality does not necessarily require introducing an entirely new method. Rather, a work that provides novel insights by evaluating existing methods, or demonstrates improved understanding is also equally valuable.

Soundness*
Based on what you discussed in “Strengths and Weaknesses”, please rate the paper on the following scale to indicate the soundness of the technical claims, experimental and research methodology, and whether the central claims of the paper are adequately supported with evidence. If you select “fair” or “poor” (indicating that the paper falls short of the standard), ensure that “Strengths and Weaknesses” include a clear justification of your rating.


4: excellent

3: good

2: fair

1: poor


Presentation*
Based on what you discussed in “Strengths and Weaknesses”, please rate the paper on the following scale to indicate the quality of the presentation. This should take into account the writing style and clarity, as well as contextualization relative to prior work. If you select “fair” or “poor” (indicating that the paper falls short of the standard), ensure that “Strengths and Weaknesses” include a clear justification of your rating.


4: excellent

3: good

2: fair

1: poor


Significance*
Based on what you discussed in “Strengths and Weaknesses”, please rate the paper on the following scale to indicate the significance of the overall contribution this paper makes to the research area being studied. If you select “fair” or “poor” (indicating that the paper falls short of the standard), ensure that “Strengths and Weaknesses” include a clear justification of your rating.


4: excellent

3: good

2: fair

1: poor

Originality*
Based on what you discussed in “Strengths and Weaknesses”, please rate the paper on the following scale to indicate its originality. If you select “fair” or “poor” (indicating that the paper falls short of the standard), ensure that “Strengths and Weaknesses” include a clear justification of your rating.


4: excellent

3: good

2: fair

1: poor


Key Questions For Authors*
If you have any important questions for the authors, please carefully formulate them here (ideally around 3-5). Please reserve your questions for cases where the response would likely change your evaluation of the paper, clarify a point in the paper that you found confusing, or address a critical limitation you identified. Please number your questions so authors can easily refer to them in the response, and explain how possible responses would change your evaluation of the paper.


Limitations*
Have the authors adequately discussed the limitations and potential negative societal impact of their work? If so, simply enter “yes”; if not, please include constructive suggestions for improvement. Authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact.

Overall Recommendation*
Please provide an overall recommendation for this submission. Choices:


6: Strong Accept: Technically flawless paper with exceptional impact on one or more areas of AI, with strong evaluation, reproducibility, and resources, and no unaddressed ethical considerations.

5: Accept: Technically solid paper, with high impact on at least one sub-area of AI or moderate-to-high impact on more than one area of AI, with good-to-excellent evaluation, resources, reproducibility, and no unaddressed ethical considerations.

4: Weak accept: Technically solid paper that advances at least one sub-area of AI, with a contribution that others are likely to build on, but with some weaknesses that limit its impact (e.g., limited evaluation). Please use sparingly.

3: Weak reject: A paper with clear merits, but also some weaknesses, which overall outweigh the merits. Papers in this category require revisions before they can be meaningfully built upon by others. Please use sparingly.

2: Reject: For instance, a paper with technical flaws, weak evaluation, inadequate reproducibility, incompletely addressed ethical considerations, or writing so poor that it is not possible to understand its key claims.

1: Strong Reject: For instance, a paper with well-known results, unaddressed ethical considerations, or a poorly written paper where it is impossible to tell what the nature of its contribution is.



Confidence*
Please provide a "confidence score" for your assessment of this submission to indicate how confident you are in your evaluation. Choices:


5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.

4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.

3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.

2: You are willing to defend your assessment, but it is quite likely that you did not understand the central parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.

1: Your assessment is an educated guess. The submission is not in your area, or the submission was difficult to understand. Math/other details were not carefully checked.

----

You MUST output your review strictly as a JSON object with the following keys. Do not include any markdown formatting outside the JSON, just the raw JSON object.

JSON Format Requirements:
{
  "summary": "Briefly summarize the paper and its contributions...",
  "strengths_and_weaknesses": "Assess soundness, presentation, significance, and originality...",
  "soundness": 4,  # Int from 1 (poor) to 4 (excellent)
  "presentation": 3, # Int from 1 (poor) to 4 (excellent)
  "significance": 4, # Int from 1 (poor) to 4 (excellent)
  "originality": 3, # Int from 1 (poor) to 4 (excellent)
  "questions_for_authors": "1. ...\n2. ...", 
  "limitations": "Evaluate if authors discussed limitations adequately...",
  "overall_recommendation": 5, # Int from 1 (Strong Reject) to 6 (Strong Accept)
  "confidence": 4 # Int from 1 (Educated guess) to 5 (Absolutely certain)
}
    """

    user_prompt = f"Here is the parsed text of the paper (truncated before references):\n\n<PAPER_TEXT>\n{paper_text}\n</PAPER_TEXT>"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    logger.info(f"正在向大模型 ({model_name}) 请求 ICML 深度审稿...")
    
    try:
        response = gateway.get_api_result(
            messages=messages, 
            temperature=0.2, # 保持较低的温度以确保客观性和 JSON 稳定性
            max_completion_tokens=4000
        )
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
        
        result_json = extract_json_from_text(content)
        # 使用 Pydantic 校验并转换回 dict
        validated_review = ICMLReview(**result_json).model_dump()
        return validated_review, tokens_used
        
    except Exception as e:
        logger.error(f"❌ 生成审稿意见时发生错误: {e}")
        return None, 0
