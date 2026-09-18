import json
from typing import List

from pydantic import BaseModel

from openai import OpenAI

API_KEY = "f98bb610aedf4d0b824430f7e67ca363.Nt5DFPzp5DeUHvBZ"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4/",
)
# 这是最新的写法，目前国内各大平台还赞时未支持
# client.responses.create 接口。这是 OpenAI 最近新推出的一个非常新的 API 接口
# （对应的底层路由是 /v1/responses）。但国内的大部分模型厂商（如智谱 GLM）尚未兼容这个新接口。

# 目前各大厂商 100% 兼容的统一标准对话接口是 client.chat.completions.create
# response = client.responses.create(
#     model="gpt-5.5",
#     instructions="You are a coding assistant that talks like a pirate.",
#     input="How do I check if a Python object is an instance of a class?",
# )


class Step(BaseModel):
    explanation: str
    output: str


class MathResponse(BaseModel):
    steps: List[Step]
    final_answer: str


# 1. 在 System Prompt 中强烈要求输出 JSON，并给一个例子
system_prompt = """You are a helpful math tutor.
You MUST output your response in valid JSON format matching this schema:
{
  "steps": [{"explanation": "string", "output": "string"}],
  "final_answer": "string"
}
Do not include markdown code blocks or any other text. Only JSON.
"""

# 2. 回退到普通的 create 方法
response = client.chat.completions.create(
    model="glm-4.6v",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "solve 8x + 31 = 2"},
    ],
)

# 3. 获取纯文本并手动解析
raw_content = response.choices[0].message.content
try:
    # 尝试把字符串解析成字典
    data = json.loads(raw_content)

    # 扔给 Pydantic 做最终的类型校验和实例化
    math_response = MathResponse(**data)
    print(math_response.steps)
    print("answer: ", math_response.final_answer)
except json.JSONDecodeError:
    print("模型乱说话了，没有返回合法的 JSON！它的原始回复是：\n", raw_content)
