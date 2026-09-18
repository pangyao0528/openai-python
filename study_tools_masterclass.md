# OpenAI SDK Tool Calling 从入门到精通 (Masterclass)

本教程是一份极其详尽的综合指南，旨在带你从零开始，一步步打通大模型开发中最核心的关卡——**Tool Calling (工具调用)**。
教程分为**基础认知篇**、**进阶控制篇**和**工业级架构篇**。每一步都配有独立且完整的 Python 脚本，你可以随时复制、粘贴并在本地独立运行。

---

## 🌟 基础认知篇：大模型是如何使用工具的？

很多人对 Tool Calling 有一个极大的误解，认为“大模型连接了互联网，能在它的服务器上运行我的代码”。
**这是错的！**
真实的流程是一场来回传球的游戏：
1. 你告诉模型：我手头有一把锤子（函数名）和它能砸多大的钉子（参数说明）。
2. 模型思考后回答：我现在需要用锤子砸 3 号钉子，请你帮我砸一下。
3. **你（在自己的电脑上）** 挥动锤子，砸完后拿到结果。
4. 你把结果告诉模型。模型再说出人类能听懂的话。

### Step 1：用最优雅的方式定义工具
传统的做法是用极度冗长的 JSON Schema 去描述工具，非常痛苦。现代 SDK 提供了 `pydantic_function_tool`，让你可以像写普通 Python 类一样定义工具。

创建 `lesson1_define.py`：
```python
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

# 1. 像写数据模型一样，定义函数的参数格式
class WeatherArgs(BaseModel):
    # 注意：这里的描述(description)不仅给人看，大模型也会看！它靠这个理解参数的含义。
    location: str = Field(description="需要查询的城市名称，例如：北京、上海")
    unit: str = Field(default="celsius", description="温度单位：celsius 或 fahrenheit")

# 2. 将它转换为大模型能看懂的工具描述
weather_tool = pydantic_function_tool(
    model=WeatherArgs, 
    name="get_weather", 
    description="获取指定城市的当前实时天气。当用户询问天气时必须调用此工具。"
)

# 打印出来看看底层生成的长什么样
print(weather_tool)
```

### Step 2：把工具扔给大模型，拦截调用指令
定义好工具后，我们在请求接口时把它传进 `tools` 参数里。

创建 `lesson2_trigger.py`：
```python
from openai import OpenAI
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

client = OpenAI()

class WeatherArgs(BaseModel):
    location: str = Field(description="城市名称")

my_tools = [pydantic_function_tool(model=WeatherArgs, name="get_weather", description="查天气")]

# 正常发起对话，附带工具
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "帮我看看现在东京天气怎么样？"}],
    tools=my_tools
)

# 检查模型是否决定使用工具
msg = response.choices[0].message
if msg.tool_calls:
    print("🎯 大模型觉得需要调用工具！")
    tool_call = msg.tool_calls[0]
    print(f"它想要调用的函数名是: {tool_call.function.name}")
    print(f"它为你生成的参数是: {tool_call.function.arguments}")
else:
    print("大模型认为自己能回答，直接说了:", msg.content)
```

### Step 3：接发球闭环（终极基础形态）
在截获指令后，我们需要在本地运行真正的代码，然后再把结果告诉大模型。

创建 `lesson3_full_loop.py`：
```python
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

client = OpenAI()

# === A. 准备工作 ===
def local_weather_api(location: str):
    """这是你本地真正的业务代码"""
    print(f"\n⚙️ [本地执行中] 正在获取 {location} 的天气数据...")
    return f"{location}目前气温 22 度，多云，适合出行。"

class WeatherArgs(BaseModel): location: str = Field(description="城市名")
my_tools = [pydantic_function_tool(WeatherArgs, name="get_weather", description="查天气")]

# === B. 第一轮：模型下达指令 ===
messages = [{"role": "user", "content": "明天深圳天气如何？"}]
res = client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=my_tools)
assistant_msg = res.choices[0].message

# [重要] 必须把模型的指令追加到历史记录中
messages.append(assistant_msg)

# === C. 拦截执行与结果反馈 ===
if assistant_msg.tool_calls:
    for tc in assistant_msg.tool_calls:
        # 1. 提取参数
        args = json.loads(tc.function.arguments)
        # 2. 本地执行
        if tc.function.name == "get_weather":
            result = local_weather_api(args["location"])
            # 3. 将结果封装塞回消息中 (role="tool" 表示这是工具的执行结果)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,  # 告诉模型，这是对应哪一个指令的返回结果
                "content": result
            })

# === D. 第二轮：模型总结 ===
final_res = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
print("\n🤖 AI 最终回复:", final_res.choices[0].message.content)
```

---

## 🛠 进阶控制篇：强行干预模型决策

### Step 4：强制调用特定的工具
大模型有时候会“偷懒”不调用工具，你可以用 `tool_choice` 参数强制它。

创建 `lesson4_tool_choice.py`：
```python
# (假设已经有了 client, messages, my_tools)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "推荐几首歌"}], # 用户并没有问天气
    tools=my_tools,
    # 尽管用户没问天气，但我们强制要求模型必须调用 get_weather 工具
    tool_choice={"type": "function", "function": {"name": "get_weather"}}
)
# 运行后你会发现，模型依然乖乖生成了 get_weather 的调用指令
```

---

## 🚀 工业级架构篇 (Pro)：打造真实的 Agent

在企业级项目中，你不可能面对几十个工具去写几十个 `if/else`，也不可能因为网络超时就让整个机器人崩溃。我们需要更现代的架构。

### Step 5：基于装饰器的动态注册表 (消除 `if/else`)
创建一个 `lesson5_registry.py`，我们将实现一个通用的调用中枢。

```python
import json
from openai import pydantic_function_tool

class AgentTools:
    def __init__(self):
        self.functions = {}
        self.openai_tools = []

    def register(self, model, name, desc):
        """装饰器：将真实的 Python 函数与 Schema 绑定起来"""
        def decorator(func):
            self.functions[name] = func
            self.openai_tools.append(pydantic_function_tool(model, name=name, description=desc))
            return func
        return decorator

    def execute(self, name: str, args_json: str) -> str:
        """根据传来的函数名，自动反序列化参数并执行"""
        if name not in self.functions:
            return f"Error: 找不到工具 {name}"
        kwargs = json.loads(args_json)
        return str(self.functions[name](**kwargs))

# --- 使用方式 ---
registry = AgentTools()

# 定义工具 1
from pydantic import BaseModel
class CalculatorArgs(BaseModel): a: int; b: int

@registry.register(CalculatorArgs, "add", "计算两数之和")
def add_numbers(a, b): return a + b

# 如果有大模型的调用指令过来，只需一行代码搞定：
# result = registry.execute(tool_call.function.name, tool_call.function.arguments)
```

### Step 6：大模型“自愈”容错机制
当 `json.loads` 失败，或者调用的外部 API 超时时，不要让程序抛出 `Exception` 崩溃！把错误信息转换为字符串，当作工具执行结果传回给大模型，它会向用户道歉或尝试修复。

创建 `lesson6_self_healing.py` (仅核心片段)：
```python
import json

def safe_execute(registry, tool_name, args_json):
    try:
        # 这里可能报错，比如模型生成的 JSON 少了引号
        return registry.execute(tool_name, args_json)
    except json.JSONDecodeError:
        # 捕捉错误，当做执行结果返回
        return "[System Error] 你生成的参数格式有误，不是合法的 JSON。请检查并重试！"
    except Exception as e:
        return f"[System Error] 工具执行失败: {str(e)}。请直接向用户说明系统故障。"

# 大模型收到带有 System Error 标记的 content 后，会理解自己出了错，并在第二次回答中做出补救。
```

### Step 7：并发提速 (Parallel Tool Calling)
现代大模型一次可能返回多个工具调用（例如查询北京和上海）。串行执行太慢，必须上异步并发。

创建 `lesson7_parallel.py`：
```python
import asyncio
import json

# 模拟一个耗时的网络查询工具
async def async_fetch_weather(city):
    await asyncio.sleep(2) # 模拟 2 秒网络延迟
    return f"{city} 天气晴朗"

async def process_parallel_calls(tool_calls):
    tasks = []
    # 1. 组装任务
    for tc in tool_calls:
        args = json.loads(tc.function.arguments)
        tasks.append(async_fetch_weather(args["city"]))
    
    # 2. 并发执行：无论查询多少个城市，总耗时都只有 2 秒！
    results = await asyncio.gather(*tasks)
    
    # 3. 封装为大模型接受的消息格式
    tool_messages = []
    for tc, res in zip(tool_calls, results):
        tool_messages.append({"role": "tool", "tool_call_id": tc.id, "content": res})
    return tool_messages
```

### Step 8：流式 (Streaming) 拦截与工具拼接
这是前端体验最佳的做法。当开启流式输出时，工具调用的 JSON 是一段段传来的，必须手动拼接。

创建 `lesson8_streaming.py`：
```python
from openai import OpenAI
client = OpenAI()

# (假设 my_tools 和 messages 已经准备好)
res_stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "北京天气如何？"}],
    tools=my_tools,
    stream=True
)

# 用于积攒破碎的 JSON 参数
tool_calls_buffer = {}

for chunk in res_stream:
    delta = chunk.choices[0].delta
    
    if delta.content:
        # 如果是正常文字，直接打印到屏幕
        print(delta.content, end="", flush=True)
        
    if delta.tool_calls:
        # 如果是工具调用，积攒拼接到 buffer 中
        for tc in delta.tool_calls:
            if tc.index not in tool_calls_buffer:
                tool_calls_buffer[tc.index] = {"id": tc.id, "name": tc.function.name, "arguments": ""}
            if tc.function.arguments:
                tool_calls_buffer[tc.index]["arguments"] += tc.function.arguments

if tool_calls_buffer:
    # 循环结束后，说明刚才是在拼接参数。现在你拥有了完整的 arguments，可以去执行 json.loads 并执行本地代码了！
    print("\n\n[后台已拦截完毕，完整的 JSON 参数为:]")
    for k, v in tool_calls_buffer.items():
        print(f"Name: {v['name']}, Args: {v['arguments']}")
    
    # 接下来就是将结果追加回 messages，发起第二次 stream=True 请求的过程...
```

---

🎉 **结语**：当你掌握了从 `pydantic` 定义工具、利用装饰器动态路由注册表、用 `asyncio` 并发提速、通过传回报错让模型自我修复，以及在 `Streaming` 引擎中无缝拦截并二次请求的全流程后，你已经具备了编写工业级通用大模型基座的绝对硬实力。
