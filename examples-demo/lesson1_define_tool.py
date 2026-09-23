"""
Lesson 1: 使用 Pydantic 定义现代化 Tool Schema (含标准模式与严格模式 Strict Mode 对比)
"""
import json
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

# 1. 定义工具参数模型
class WeatherParams(BaseModel):
    location: str = Field(
        description="需要查询天气的城市名称，例如：北京、上海、深圳、Tokyo"
    )
    unit: str = Field(
        default="celsius",
        description="温度单位：'celsius' (摄氏度) 或 'fahrenheit' (华氏度)"
    )

# 2. 生成标准 Tool Schema (供 OpenAI Chat Completions 使用)
standard_tool = pydantic_function_tool(
    model=WeatherParams,
    name="get_current_weather",
    description="当用户询问指定城市的当前天气情况时调用此工具。"
)

print("=" * 60)
print("📌 [1] 生成的标准 Tool JSON Schema:")
print(json.dumps(standard_tool, ensure_ascii=False, indent=2))

# 3. 生成 Strict Mode (严格模式) Tool Schema
# 严格模式在 OpenAI 模型端保证 100% 遵循 JSON Schema，杜绝字段缺失或类型错乱
strict_tool = pydantic_function_tool(
    model=WeatherParams,
    name="get_current_weather_strict",
    description="获取指定城市的当前天气（严格模式，100% 杜绝参数幻觉）"
)

print("=" * 60)
print("📌 [2] Tool 定义成功！可直接作为 tools=[...] 传入 client.chat.completions.create")
print("=" * 60)