# OpenAI Python SDK：工具调用 (Tool Calling) 深度闯关指南

当你掌握了基础的对话生成后，大模型的下一个杀手锏就是 **Tool Calling（以前叫 Function Calling）**。
它赋予了大模型“长手长脚”的能力，让模型不再只是个“懂文字的百科全书”，而是能够：
*   **实时联网**获取最新数据（查天气、查股票）。
*   **操作本地系统**（读写本地文件、查询数据库）。
*   **控制外部设备**（通过 API 关灯、发邮件）。

> **💡 核心真相（新手必看）**
> 大模型**绝对不会**在它的服务器上真正运行你的 Python 代码！
> 所谓的“工具调用”，本质上是一场**接发球游戏**：
> 1. 你把“我有哪些函数（名字、参数说明）”告诉大模型。
> 2. 大模型根据用户的提问，决定：“哎，这个问题我不知道，但我发现你可以用 `get_weather` 函数查出来。请你帮我执行一下，参数是 `location="北京"`。”
> 3. 你在本地真正运行 `get_weather("北京")`，拿到结果。
> 4. 你把结果发回给大模型。大模型拿到结果后，再组织成人类友好的语言回答用户。

---

## 第一关：传统的方式 vs 现代的方式 (定义工具)

在告诉大模型你有什么工具之前，你必须用大模型能听懂的格式（JSON Schema）描述你的工具。

### 方式 A：纯手写 JSON (传统且痛苦)
你必须严格按照规范手写一长串字典：
```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取指定城市的当前天气",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "城市名，例如：北京, 上海"},
                "unit": {"type": "string", "enum": ["c", "f"]}
            },
            "required": ["location"]
        }
    }
}]
```

### 方式 B：使用 Pydantic 神器 (现代且优雅)
幸运的是，OpenAI Python SDK 提供了 `pydantic_function_tool` 辅助工具。你只需要写 Python 标准的 Pydantic 模型，剩下的脏活累活 SDK 帮你做！

创建一个 `lesson1_define_tool.py` 并运行：
```python
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

# 1. 定义函数参数的数据结构 (BaseModel)
class WeatherParams(BaseModel):
    # 这里的 docstring 和 Field(description) 会直接被大模型看到，用来理解怎么传参！
    location: str = Field(description="城市名称，例如：北京, 上海")
    unit: str = Field(default="c", description="温度单位，'c' 表示摄氏度，'f' 表示华氏度")

# 2. 将它转换为大模型认识的 tool 格式
my_tools = [
    pydantic_function_tool(
        model=WeatherParams, 
        name="get_current_weather", # 给大模型调用的函数名
        description="当你需要获取任何地方的天气信息时，请调用此工具。"
    )
]

print("生成的 Tool Schema:")
print(my_tools)
```

---

## 第二关：让大模型决定是否调用 (抛出问题)

现在，我们把问题和工具一起抛给大模型。

创建一个 `lesson2_trigger_tool.py` 并运行：
```python
from openai import OpenAI
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

client = OpenAI()

class WeatherParams(BaseModel):
    location: str = Field(description="城市名称，例如：北京")

tools = [
    pydantic_function_tool(model=WeatherParams, name="get_weather", description="获取天气")
]

# 正常发起对话，但这次带上 tools
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "今天北京天气怎么样？"}],
    tools=tools
)

# 关键来了！检查大模型是否决定调用工具
message = response.choices[0].message
if message.tool_calls:
    print("大模型决定调用工具！")
    tool_call = message.tool_calls[0]
    print(f"调用的函数名: {tool_call.function.name}")
    print(f"模型生成的参数: {tool_call.function.arguments}")
else:
    print("大模型认为不需要工具，直接回答了：", message.content)
```

---

## 第三关：本地执行并返回结果 (接发球完整闭环)

大模型只是给出了参数，**真正的执行逻辑需要你自己在 Python 里写**。拿到结果后，还要告诉大模型。

创建一个 `lesson3_full_loop.py`，这就是 Tool Calling 的**终极形态**：

```python
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

client = OpenAI()

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
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    tools=tools
)
assistant_msg = response.choices[0].message

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
    final_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        # 这次不用带 tools 也可以了，因为它只是做文字总结
    )
    print("\n🤖 AI 最终回复: ")
    print(final_response.choices[0].message.content)
```

---

## 第四关：强制控制大模型的行为 (`tool_choice`)

有时候大模型比较笨，它觉得不需要调用工具，或者它调错了工具。你可以用 `tool_choice` 参数来强迫它。

*   **`tool_choice="auto"` (默认)**：模型自己决定用不用、用哪个。
*   **`tool_choice="required"`**：模型**必须**调用工具，但调用哪个由它自己挑。
*   **`tool_choice={"type": "function", "function": {"name": "get_weather"}}`**：模型**绝对必须**调用 `get_weather` 这个特定的工具，不准废话。
*   **`tool_choice="none"`**：禁用工具（即便你传了 `tools` 列表）。

**💪 动手实践：**
在第三关的代码中，如果你遇到大模型“不听话”不调用工具的情况，可以在 `client.chat.completions.create()` 里强制加上 `tool_choice="required"` 试一试。

---

## 🎉 工具调用小结与进阶

你现在已经掌握了让 AI 拥有“实体能力”的核心技巧！
工具调用是打造高级 AI Agent（智能体）的基石。

**📖 进阶源码指引：**
1. 想要了解 `pydantic_function_tool` 的底层魔法？去看看 [`src/openai/lib/_tools.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/lib/_tools.py)。
2. 你可能会觉得每次都要写 `if msg.tool_calls: json.loads(...)` 非常繁琐。在工业界，我们通常会写一个装饰器（Decorator）或者一个专门的调度器类，自动把大模型的 JSON 映射到真实的 Python 函数上执行。
3. 如果你在写企业级应用，当本地函数执行报错（比如网络断了）时，不要让程序崩溃，而是把**错误信息（Error String）作为 `content` 传回给大模型**，聪明的大模型会自动向用户道歉并尝试换种方式处理！
