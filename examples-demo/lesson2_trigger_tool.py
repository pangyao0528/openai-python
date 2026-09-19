from openai import OpenAI
from pydantic import BaseModel, Field
from openai import pydantic_function_tool


API_KEY = "f98bb610aedf4d0b824430f7e67ca363.Nt5DFPzp5DeUHvBZ"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4/",
)

class WeatherParams(BaseModel):
    location: str = Field(description="城市名称，例如：北京")

tools = [
    pydantic_function_tool(model=WeatherParams, name="get_weather", description="获取天气")
]

# 正常发起对话，但这次带上 tools
response = client.chat.completions.create(
    model="glm-4.6v",
    messages=[{"role": "user", "content": "今天北京天气怎么样？"}],
    tools=tools
)

# 关键来了！检查大模型是否决定调用工具
message = response.choices[0].message
if message.tool_calls:
    print("大模型决定调用工具！")
    tool_call = message.tool_calls[0]
    # pyrefly: ignore [missing-attribute]
    print(f"调用的函数名: {tool_call.function.name}")  # ty: ignore[unresolved-attribute]
    # pyrefly: ignore [missing-attribute]
    print(f"模型生成的参数: {tool_call.function.arguments}")  # ty: ignore[unresolved-attribute]
else:
    print("大模型认为不需要工具，直接回答了：", message.content)