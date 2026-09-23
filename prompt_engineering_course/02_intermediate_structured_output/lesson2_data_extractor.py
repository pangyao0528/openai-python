"""
Lesson 2: 结构化输出全方案实战 —— Few-Shot 纯提示词 vs Pydantic 结构化输出
特性：
1. 对比第一代 Few-Shot JSON 抽取与第三代 Pydantic 语法级严格抽取
2. 彻底清除硬编码明文 API Key，使用标准环境变量
3. 自带 Mock 降级验证
"""
import os
import json
import openai
from pydantic import BaseModel, Field
from typing import Optional, List

api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_BASE_URL")
model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

client = None
if api_key:
    client = openai.OpenAI(api_key=api_key, base_url=base_url)

# =========================================================
# 方式一：经典 Few-Shot 提示词抽取 (全模型通用)
# =========================================================
FEW_SHOT_SYSTEM_PROMPT = """
你是一个精准的信息抽取专家。请从用户输入的客诉文本中抽取结构化信息。
严格输出标准的 JSON 字符串，不要包含任何 markdown 语法（如 ```json），也不要输出任何前后缀解释。

字段要求：
{
  "customer_name": "客户姓名，若无提及填 null",
  "phone_number": "联系电话，若无提及填 null",
  "products": ["涉及的产品列表"],
  "issue_summary": "核心问题一句话概述"
}

Few-Shot 示例参考：
<example_1>
输入: "我是李四，电话13900001111，上周买的戴尔显示器一直闪屏，换了HDMI线也没用。"
输出: {"customer_name": "李四", "phone_number": "13900001111", "products": ["戴尔显示器"], "issue_summary": "显示器持续闪屏故障"}
</example_1>

<example_2>
输入: "你们客服电话怎么一直占线啊？快点回个电话过来！"
输出: {"customer_name": null, "phone_number": null, "products": [], "issue_summary": "客服电话占线投诉"}
</example_2>
"""

def extract_with_few_shot(text: str):
    print(f"\n--- [方案 A: 经典 Few-Shot 抽取] ---")
    print(f"输入文本: '{text}'")

    if client:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": FEW_SHOT_SYSTEM_PROMPT},
                    {"role": "user", "content": f"输入: \"{text}\"\n输出:"}
                ],
                temperature=0.0
            )
            raw_text = response.choices[0].message.content or "{}"
            print("模型原始输出:", raw_text)
            parsed = json.loads(raw_text.strip().removeprefix("```json").removesuffix("```"))
            print("✅ 成功解析字典:", parsed)
            return parsed
        except Exception as e:
            print(f"API 运行提示: {e}，启用 Mock 输出")

    # Mock 演示
    mock_data = {
        "customer_name": "张先生",
        "phone_number": "13812345678",
        "products": ["MacBook Pro", "妙控鼠标"],
        "issue_summary": "充电器过热且鼠标无法蓝牙连接"
    }
    print("✅ Mock 成功解析字典:", mock_data)
    return mock_data

# =========================================================
# 方式二：现代 Pydantic Structured Outputs (语法级约束，零幻觉)
# =========================================================
class SupportTicket(BaseModel):
    customer_name: Optional[str] = Field(default=None, description="客户姓名")
    phone_number: Optional[str] = Field(default=None, description="电话号码")
    products: List[str] = Field(default_factory=list, description="涉及的硬件或软件产品名称列表")
    issue_summary: str = Field(description="核心故障一句话总结")

def extract_with_pydantic_structured(text: str):
    print(f"\n--- [方案 B: 现代 Pydantic Structured Outputs] ---")
    print(f"输入文本: '{text}'")

    if client:
        try:
            # 官方推荐的 beta.chat.completions.parse API
            completion = client.beta.chat.completions.parse(
                model=model_name,
                messages=[
                    {"role": "system", "content": "请从用户的输入中抽取支持工单数据。"},
                    {"role": "user", "content": text}
                ],
                response_format=SupportTicket
            )
            ticket: SupportTicket = completion.choices[0].message.parsed # 自动反序列化为类型安全的 Pydantic 对象
            print("✅ 获得强类型 Pydantic 对象:", ticket)
            print(f"   * 客户: {ticket.customer_name}, 产品: {ticket.products}, 摘要: {ticket.issue_summary}")
            return ticket
        except Exception as e:
            print(f"API 运行提示: {e}，启用 Mock 输出")

    # Mock 演示
    ticket = SupportTicket(
        customer_name="张先生",
        phone_number="13812345678",
        products=["MacBook Pro", "妙控鼠标"],
        issue_summary="充电器过热且鼠标无法蓝牙连接"
    )
    print("✅ Mock 获得强类型 Pydantic 对象:", ticket)
    return ticket

if __name__ == "__main__":
    test_input = "我是张先生，电话是13812345678。我买的MacBook Pro充电器发烫严重，另外送的妙控鼠标连不上蓝牙。"
    extract_with_few_shot(test_input)
    extract_with_pydantic_structured(test_input)
