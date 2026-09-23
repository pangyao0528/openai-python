"""
Lesson 4: 精准控制大模型调用行为 (tool_choice 与 parallel_tool_calls)
"""
import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "your-api-key-here"),
    base_url=os.environ.get("OPENAI_BASE_URL", None)
)
model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

class WeatherArgs(BaseModel):
    city: str = Field(description="城市名称")

class SearchArgs(BaseModel):
    query: str = Field(description="搜索关键词")

tools = [
    pydantic_function_tool(model=WeatherArgs, name="get_weather", description="查实时天气"),
    pydantic_function_tool(model=SearchArgs, name="search_web", description="全网搜索引擎")
]

# 测试 1: 强制必须调用工具 (tool_choice="required")
print("=" * 60)
print("1️⃣ [演示 tool_choice='required']: 哪怕用户输入闲聊，模型也必须挑一个工具调用")
try:
    res_required = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": "给我讲个幽默的笑话吧"}],
        tools=tools,
        tool_choice="required" # 必须调用工具
    )
    msg = res_required.choices[0].message
    if msg.tool_calls:
        print(f"👉 模型被强迫调用的工具: {msg.tool_calls[0].function.name}")
        print(f"👉 生成的参数: {msg.tool_calls[0].function.arguments}")
except Exception as e:
    print(f"执行提示: {e}")

# 测试 2: 强制指定调用特定的工具
print("\n" + "=" * 60)
print("2️⃣ [演示强制调用指定工具]: 强制必须调用 get_weather")
try:
    res_specific = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": "帮我查一下量子力学的最新研究进展"}],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "get_weather"}},
        parallel_tool_calls=False # 禁用并发，强制单一调用
    )
    msg = res_specific.choices[0].message
    if msg.tool_calls:
        print(f"👉 模型严格按要求调用了: {msg.tool_calls[0].function.name}")
        print(f"👉 传参: {msg.tool_calls[0].function.arguments}")
except Exception as e:
    print(f"执行提示: {e}")
