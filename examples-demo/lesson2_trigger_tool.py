"""
Lesson 2: 拦截与检查大模型产生的 tool_calls 指令
"""
import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

# 初始化客户端：优先读取环境变量，默认兼容各主流 OpenAI API 兼容平台
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "your-api-key-here"),
    base_url=os.environ.get("OPENAI_BASE_URL", None)
)
model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

# 1. 准备工具
class WeatherParams(BaseModel):
    location: str = Field(description="城市名称，例如：北京、上海")

tools = [
    pydantic_function_tool(
        model=WeatherParams,
        name="get_weather",
        description="查询指定城市的实时天气数据"
    )
]

# 2. 发起对话，带上 tools 说明书
user_prompt = "今天深圳的天气怎么样？"
print(f"-> 发送用户提问: '{user_prompt}'，模型: {model_name}")

try:
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": user_prompt}],
        tools=tools
    )

    message = response.choices[0].message

    # 3. 关键环节：检查大模型是否下达了工具调用指令
    if message.tool_calls:
        print("\n🎯 大模型决定调用外部工具！")
        for idx, tool_call in enumerate(message.tool_calls, start=1):
            print(f"\n--- [工具调用指令 #{idx}] ---")
            print(f"Tool Call ID  : {tool_call.id}")
            print(f"函数名 (Name)  : {tool_call.function.name}")
            print(f"生成的参数 (Args): {tool_call.function.arguments}")
            
            # 反序列化为 Python 字典方便后续消费
            parsed_args = json.loads(tool_call.function.arguments)
            print(f"反序列化后的参数 : {parsed_args}")
    else:
        print("\n大模型认为无需调用工具，直接回复了内容：")
        print(message.content)

except Exception as e:
    print(f"\n⚠️ 调调用出错（请检查 API 密钥或网络环境）：{e}")
    print("💡 提示：可通过设置环境变量运行，例如：")
    print("   export OPENAI_API_KEY='sk-...'")
    print("   export OPENAI_BASE_URL='https://...' # 可选兼容端点")
    print("   export OPENAI_MODEL_NAME='gpt-4o-mini'")