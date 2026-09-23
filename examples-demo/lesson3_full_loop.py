"""
Lesson 3: 接发球完整闭环 —— 本地执行工具并将结果回塞给大模型 (规范单轮全流程)
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

# ----------------- 1. 定义本地真实业务逻辑 -----------------
def my_local_weather_api(location: str) -> str:
    """这是一个模拟的本地系统接口，在实际生产中可调用第三方 RESTful API 或查询数据库"""
    print(f"\n⚙️ [本地系统] 正在查询 {location} 的天气数据...")
    if "北京" in location:
        return json.dumps({"temp": 18, "condition": "多云，有微风", "air_quality": "优"}, ensure_ascii=False)
    elif "上海" in location:
        return json.dumps({"temp": 24, "condition": "晴朗温暖", "air_quality": "良"}, ensure_ascii=False)
    else:
        return json.dumps({"temp": 22, "condition": "晴转多云", "air_quality": "优"}, ensure_ascii=False)

# ----------------- 2. 准备传给模型的 Tool Schema -----------------
class WeatherParams(BaseModel):
    location: str = Field(description="城市名称，例如：北京、上海")

tools = [
    pydantic_function_tool(model=WeatherParams, name="get_weather", description="获取某地的当前天气")
]

# ----------------- 3. 第一轮对话：大模型下达指令 -----------------
messages = [{"role": "user", "content": "请问北京和上海现在的天气分别怎么样？"}]
print("-> 发送用户提问给大模型:", messages[0]["content"])

try:
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools
    )
    assistant_msg = response.choices[0].message

    # 【核心规范 1】必须把大模型的这条调用指令原封不动追加到历史记录中！
    messages.append(assistant_msg)

    # ----------------- 4. 拦截指令并在本地执行 -----------------
    if assistant_msg.tool_calls:
        print(f"\n<- 大模型下达了 {len(assistant_msg.tool_calls)} 个工具调用指令 (并行调用)")
        
        for tool_call in assistant_msg.tool_calls:
            print(f"   * 准备执行: {tool_call.function.name} ID: {tool_call.id}")
            args = json.loads(tool_call.function.arguments)
            
            # 根据函数名派发执行
            if tool_call.function.name == "get_weather":
                result = my_local_weather_api(args["location"])
                
                # 【核心规范 2】将执行结果以 role="tool" 封装，并严格附带 tool_call_id
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
                print(f"   -> 已将本地执行结果装配回对话上下文: {result}")

        # ----------------- 5. 第二轮对话：大模型总结并回复人类 -----------------
        print("\n-> 发送工具结果给大模型，等待模型最终总结回复...")
        final_response = client.chat.completions.create(
            model=model_name,
            messages=messages
        )
        final_text = final_response.choices[0].message.content
        print("\n🤖 AI 最终回复:")
        print("-" * 50)
        print(final_text)
        print("-" * 50)
    else:
        print("\n大模型未调用工具，直接回复：", assistant_msg.content)

except Exception as e:
    print(f"\n⚠️ 运行出错（请检查 API 密钥或网络环境）：{e}")
    print("💡 提示：可通过设置环境变量运行，例如：")
    print("   export OPENAI_API_KEY='sk-...'")
    print("   export OPENAI_MODEL_NAME='gpt-4o-mini'")