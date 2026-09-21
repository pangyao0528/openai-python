import os
import json
import openai

from pydantic import BaseModel
from typing import List, Optional

API_KEY = "f98bb610aedf4d0b824430f7e67ca363.Nt5DFPzp5DeUHvBZ"
client = openai.OpenAI(
    api_key=API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4/" )


# ---------------------------------------------------------
# 方式一：纯 Prompt 方式 + Few Shot (适用于所有模型)
# ---------------------------------------------------------
FEW_SHOT_PROMPT = """
你是一个精准的信息抽取机器人。请从用户的输入中抽取关键信息，并严格以 JSON 格式输出。
不要输出任何 markdown 语法（如 ```json），也不要输出任何解释性文本。

你需要抽取的字段结构如下：
{
    "customer_name": "客户姓名，字符串类型，如果没有则为 null",
    "phone_number": "联系电话，字符串类型，如果没有则为 null",
    "issue_summary": "客户遇到的问题的一句话总结"
}

下面是两个例子：

# 例子 1
输入："我是张三，我的电话是 13812345678。我的路由器一直亮红灯，连不上网。"
输出：
{"customer_name": "张三", "phone_number": "13812345678", "issue_summary": "路由器亮红灯无法联网"}

# 例子 2
输入："喂？有人在吗？我的电脑开不了机了。"
输出：
{"customer_name": null, "phone_number": null, "issue_summary": "电脑无法开机"}
"""

# pyrefly: ignore [implicit-any-parameter, unannotated-return]
def extract_with_few_shot(text):
    print(f"\n[Few-Shot 方式提取] 正在处理文本: '{text}'")
    response = client.chat.completions.create(
        model="glm-4.6v",
        messages=[
            {"role": "system", "content": FEW_SHOT_PROMPT},
            {"role": "user", "content": f"输入：'{text}'\n输出："}
        ],
        temperature=0 # 抽取任务通常需要确定性，把温度调为 0
    )
    
    result_str = response.choices[0].message.content
    print("模型原始输出:", result_str)
    
    try:
        # 直接尝试解析 JSON
        assert result_str is not None
        parsed_data = json.loads(result_str)  # ty: ignore[invalid-argument-type]
        print("✅ 成功解析为字典:", parsed_data)
    except json.JSONDecodeError:
        print("❌ 解析 JSON 失败！模型没有输出合法的 JSON。")

# ---------------------------------------------------------
# 方式二：使用 OpenAI 最新的 Structured Outputs (推荐)
# 这实际上也是一种基于 Schema 的强制规范，和 Tools 定义非常像
# ---------------------------------------------------------

# 使用 Pydantic 定义我们要的结构
class TicketInfo(BaseModel):
    customer_name: Optional[str]
    phone_number: Optional[str]
    issue_summary: str

# pyrefly: ignore [implicit-any-parameter, unannotated-return]
def extract_with_structured_output(text):
    print(f"\n[Structured Output 方式提取] 正在处理文本: '{text}'")
    response = client.beta.chat.completions.parse(
        model="glm-4.6v",
        messages=[
            {"role": "system", "content": "你是一个精准的信息抽取机器人。"},
            {"role": "user", "content": text}
        ],
        response_format=TicketInfo, # 直接传入 Pydantic 模型
    )
    
    # 返回的直接是解析好的 Python 对象！
    ticket = response.choices[0].message.parsed
    assert ticket is not None
    print(f"✅ 解析成功: 姓名={ticket.customer_name}, 电话={ticket.phone_number}, 总结={ticket.issue_summary}")  # ty: ignore[unresolved-attribute]
    print("序列化后的数据:", ticket.model_dump_json(indent=2))


if __name__ == "__main__":
    test_text = "你好，我是王大锤。我刚刚不小心把水洒在键盘上了，现在几个按键失灵。我的手机号是 19988887777，请尽快安排维修。"
    
    # extract_with_few_shot(test_text)
    
    extract_with_structured_output(test_text)
