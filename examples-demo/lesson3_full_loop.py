import json
from openai import OpenAI
from pydantic import BaseModel, Field
from openai import pydantic_function_tool


API_KEY = "f98bb610aedf4d0b824430f7e67ca363.Nt5DFPzp5DeUHvBZ"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4/",
)



# ----------------- 1. 定义你的本地业务逻辑 -----------------
def my_local_weather_api(location: str) -> str:
    """这是一个模拟的本地函数，实际业务中这里可以调第三方接口或查数据库"""
    print(f"\n[本地系统] 正在查询 {location} 的天气...")
    if "北京" in location:
        return '{"temp": 15, "condition": "多云，有微风"}'
    else:
        return '{"temp": 25, "condition": "晴朗"}'

# ----------------- 2. 准备传给模型的 Tool Schema -----------------
class WeatherParams(BaseModel):
    location: str = Field(description="城市名称")

tools = [
    pydantic_function_tool(model=WeatherParams, name="get_weather", description="获取某地的当前天气")
]

# 初始化对话历史
messages = [{"role": "user", "content": "请问北京和上海现在的天气分别怎么样？"}]

# ----------------- 3. 第一轮对话：大模型下达指令 -----------------
print("-> 发送用户提问给大模型...")
# pyrefly: ignore [no-matching-overload]
response = client.chat.completions.create(
    model="glm-4.6v",
    messages= messages,  # ty: ignore[invalid-argument-type]
    tools=tools
)
assistant_msg = response.choices[0].message

print('第一次返回消息！--',assistant_msg)

# 必须把大模型的这条“调用指令”消息，也原封不动追加到历史记录里！
messages.append(assistant_msg)

# ----------------- 4. 拦截指令并在本地执行 -----------------
if assistant_msg.tool_calls:
    # 现代的大模型支持并行工具调用 (Parallel Tool Calling)，所以它可能会一次性返回多个调用
    for tool_call in assistant_msg.tool_calls:
        print(f"<- 大模型请求调用函数: {tool_call.function.name}")
        
        # 提取模型生成的参数（它是一个 JSON 字符串，我们需要 loads）
        args = json.loads(tool_call.function.arguments)
        
        # 这里进行路由，根据函数名调用不同的本地 Python 函数
        if tool_call.function.name == "get_weather":
            # 真正的执行本地逻辑
            result = my_local_weather_api(args["location"])
            
            # 【核心步骤】将本地执行结果，封装成一个 role="tool" 的消息塞回记录中
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id, # 必须带上 id，告诉模型这是对应哪个指令的回复
                "content": result             # 必须是字符串
            })
            print(f"-> 本地执行完毕，把结果发回给大模型：{result}")

# ----------------- 5. 第二轮对话：大模型总结并回复人类 -----------------
if assistant_msg.tool_calls:    
    print("\n-> 发送工具结果给大模型，等待最终总结...")
    # pyrefly: ignore [no-matching-overload]
    final_response = client.chat.completions.create(
        model="glm-4.6v",
        # pyrefly: ignore [bad-argument-type]
        messages=messages,  # ty: ignore[invalid-argument-type]
        # 这次不用带 tools 也可以了，因为它只是做文字总结
        tools= tools

    )
    print("\n🤖 AI 最终回复: ")
    print(final_response.choices[0].message.content)
    print('第二次返回消息！--',final_response.choices[0].message)
    assistant_last_msg = final_response.choices[0].message
    messages.append(assistant_last_msg)

        
        # ----------------- 6. 拦截指令并在本地执行 -----------------
    if assistant_last_msg.tool_calls:
    # 现代的大模型支持并行工具调用 (Parallel Tool Calling)，所以它可能会一次性返回多个调用
      for tool_call in assistant_last_msg.tool_calls:
        print(f"<- 大模型请求调用函数1: {tool_call.function.name}")
        
        # 提取模型生成的参数（它是一个 JSON 字符串，我们需要 loads）
        args = json.loads(tool_call.function.arguments)
        
        # 这里进行路由，根据函数名调用不同的本地 Python 函数
        if tool_call.function.name == "get_weather":
            # 真正的执行本地逻辑
            result = my_local_weather_api(args["location"])
            
            # 【核心步骤】将本地执行结果，封装成一个 role="tool" 的消息塞回记录中
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id, # 必须带上 id，告诉模型这是对应哪个指令的回复
                "content": result             # 必须是字符串
            })
            print(f"-> 本地执行完毕，把结果发回给大模型1：{result}")    

            if assistant_msg.tool_calls:    
               print("\n-> 发送工具结果给大模型，等待最终总结11..")
                # pyrefly: ignore [no-matching-overload]
            final_response = client.chat.completions.create(
                model="glm-4.6v",
                    # pyrefly: ignore [bad-argument-type]
                    messages=messages,  # ty: ignore[invalid-argument-type]
                    # 这次不用带 tools 也可以了，因为它只是做文字总结
                    tools= tools

                )
            print("\n🤖 AI 最终回复333: ")
            print(final_response.choices[0].message.content)
     
    

            