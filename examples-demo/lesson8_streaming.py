"""
Lesson 8: 流式输出 (Streaming) 中的工具切片拦截与二次推流
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

def local_weather(city: str) -> str:
    return json.dumps({"city": city, "temperature": "26°C", "weather": "晴"}, ensure_ascii=False)

class WeatherArgs(BaseModel):
    city: str = Field(description="城市名称")

tools = [
    pydantic_function_tool(model=WeatherArgs, name="local_weather", description="获取实时天气")
]

messages = [{"role": "user", "content": "帮我看看广州今天天气怎么样？"}]

print("=" * 65)
print("🌊 发起第一轮流式请求 (stream=True)...")

try:
    stream_response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        stream=True
    )

    # 准备切片缓冲容器 (用于拼接被碎裂的 arguments JSON 字符串)
    tool_calls_accumulator = {}

    for chunk in stream_response:
        delta = chunk.choices[0].delta
        
        # 场景 A: 模型直接输出思考或文字回答（打字机流式）
        if delta.content:
            print(delta.content, end="", flush=True)

        # 场景 B: 模型返回的是工具调用的碎片切片
        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls_accumulator:
                    tool_calls_accumulator[idx] = {
                        "id": tc.id or "",
                        "name": tc.function.name or "",
                        "arguments": ""
                    }
                if tc.id:
                    tool_calls_accumulator[idx]["id"] = tc.id
                if tc.function.name:
                    tool_calls_accumulator[idx]["name"] = tc.function.name
                if tc.function.arguments:
                    # 持续拼接切片字符
                    tool_calls_accumulator[idx]["arguments"] += tc.function.arguments

    # 如果有积攒的工具调用
    if tool_calls_accumulator:
        print("\n\n⚙️ [后台静默捕获到完整工具指令]:")
        
        # 1. 构建 assistant 的消息对象回填至历史记录
        assistant_tool_msg = {
            "role": "assistant",
            "tool_calls": []
        }
        for idx, call_data in tool_calls_accumulator.items():
            print(f"   * 工具: {call_data['name']}, 拼装后的完整参数: {call_data['arguments']}")
            assistant_tool_msg["tool_calls"].append({
                "id": call_data["id"],
                "type": "function",
                "function": {
                    "name": call_data["name"],
                    "arguments": call_data["arguments"]
                }
            })
        messages.append(assistant_tool_msg)

        # 2. 本地执行并将结果放入 role="tool"
        for idx, call_data in tool_calls_accumulator.items():
            if call_data["name"] == "local_weather":
                args = json.loads(call_data["arguments"])
                exec_result = local_weather(args.get("city", "未知"))
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_data["id"],
                    "content": exec_result
                })

        # 3. 发起第二次流式推流，前端无缝看到最终回答！
        print("\n🤖 [第二次流式响应：AI 开始逐字向用户回答]:")
        second_stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True
        )
        for chunk in second_stream:
            content_piece = chunk.choices[0].delta.content
            if content_piece:
                print(content_piece, end="", flush=True)
        print("\n")

except Exception as e:
    print(f"\n⚠️ 运行提示: {e}")
    print("💡 提示：设置环境变量 OPENAI_API_KEY 后可体验完整流式交互。")
