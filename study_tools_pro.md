# OpenAI Python SDK：Tool Calling 工业级进阶指南 (Pro)

这份指南专为有一定基础、立志于开发**生产级智能体 (Enterprise Agents)** 的开发者准备。

在真实的业务场景中（如企业级大模型服务、复杂的自动化智能体），大模型的 Tool Calling 绝不仅仅是写两个 `if/else` 这么简单。你将面临诸多挑战：如果有 50 个工具怎么管理？模型并发调用了 5 个接口怎么提速？底层的外部 API 挂了或者模型参数传错了怎么办？如何在流式（打字机）输出中无缝穿插工具执行？

本指南将带你一一攻克这些工业级难题。

---

## 第一章：告别 `if/else` —— 动态工具注册与路由

基础教程里，我们拿到模型的 `tool.name` 后，手动写 `if name == "A": ... elif name == "B": ...`。当工具数量达到两位数时，代码将极度腐化。

**✅ 工业级解法：动态注册表 (Tool Registry)**

在 Python 中，最佳实践是利用**装饰器 (Decorator)** 或字典来动态绑定函数和 Schema。

```python
import json
from typing import Callable, Dict, Any
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

class ToolRegistry:
    def __init__(self):
        # 存储实际的 Python 函数
        self._functions: Dict[str, Callable] = {}
        # 存储给 OpenAI 的 Schema 列表
        self.openai_tools = []

    def register(self, pydantic_model: BaseModel, name: str, description: str):
        """装饰器：注册一个工具"""
        def decorator(func: Callable):
            self._functions[name] = func
            self.openai_tools.append(
                pydantic_function_tool(model=pydantic_model, name=name, description=description)
            )
            return func
        return decorator

    def execute(self, tool_name: str, arguments_json: str) -> str:
        """动态路由并执行"""
        if tool_name not in self._functions:
            return f"Error: Tool {tool_name} not found."
            
        func = self._functions[tool_name]
        try:
            # 自动反序列化
            kwargs = json.loads(arguments_json)
            # 执行真正的函数
            result = func(**kwargs)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            # 千万别让整个程序崩溃，详见第三章
            return f"Error executing {tool_name}: {str(e)}"

# ================= 使用演示 =================
registry = ToolRegistry()

class WeatherArgs(BaseModel):
    city: str = Field(description="城市名")

@registry.register(pydantic_model=WeatherArgs, name="get_weather", description="查天气")
def get_weather(city: str):
    return {"city": city, "temp": 25}

# 发给 OpenAI 时： client.chat.completions.create(..., tools=registry.openai_tools)
# 拿到模型返回时： registry.execute(tool_call.function.name, tool_call.function.arguments)
```

---

## 第二章：并行工具调用 (Parallel Tool Calling)

现代大模型（如 gpt-4o, gpt-4o-mini）支持**并行调用**。如果用户问：“请分别查一下北京、上海、东京的天气”，模型会**一次性**返回 3 个 Tool Calls。

如果你用普通的 `for` 循环同步执行这 3 个网络请求，速度会慢得令人发指。

**✅ 工业级解法：使用 Asyncio 并发执行**

```python
import asyncio
import json

async def process_tool_calls(tool_calls, registry):
    # 构建协程任务列表
    tasks = []
    for tc in tool_calls:
        # 将每个工具调用的执行包装为一个异步任务
        tasks.append(
            asyncio.to_thread(
                registry.execute, 
                tc.function.name, 
                tc.function.arguments
            )
        )
    
    # 并发执行所有任务！耗时取决于最慢的那一个，而不是总和
    results = await asyncio.gather(*tasks)
    
    # 构建发回给 OpenAI 的 message 列表
    tool_messages = []
    for tc, result in zip(tool_calls, results):
        tool_messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": str(result)
        })
    return tool_messages

# 在主流程中：
# tool_messages = await process_tool_calls(assistant_msg.tool_calls, registry)
# messages.extend(tool_messages)
```

---

## 第三章：优雅的容错与大模型“自愈”机制

如果你调用的第三方 API 挂了，或者大模型产生的 JSON 参数不符合 Pydantic 的规范（比如漏了必填参数），普通的程序会直接抛出 `Exception` 并终止。用户看到的将是一个 `500 Server Error`。

**✅ 工业级解法：让大模型自己修 Bug**

不要截断对话，而是把**报错的字符串当做工具执行的结果发回给大模型**。GPT 拥有极强的查漏补缺能力，它看到报错后，通常会自动道歉，调整参数再试一次，或者换一种方式回答用户。

```python
def safe_execute_tool(func, arguments_json):
    try:
        args = json.loads(arguments_json)
        # 这里甚至可以用 Pydantic_model.model_validate(args) 强制校验参数
        return func(**args)
    except json.JSONDecodeError:
        # 模型生成的 JSON 格式坏了
        return "System Error: 你的参数不是合法的 JSON，请检查并重试。"
    except ValueError as e:
        # 参数校验失败
        return f"Validation Error: 你的参数错误 -> {str(e)}。请修正后重试。"
    except TimeoutError:
        # 外部网络挂了
        return "Network Error: 获取外部数据超时。请直接告诉用户目前无法查询该信息，不要瞎编。"
    except Exception as e:
        # 其他未知异常
        return f"Unknown Error: 执行过程中发生错误 {str(e)}。"
```
*提示：将这些 Error 文本原封不动地设为 `role: "tool"` 的 `content` 并发给大模型即可，模型会做出极具人情味的应变。*

---

## 第四章：终极挑战 —— 在流式输出 (Streaming) 中处理工具

在 Web 应用中，我们需要逐字打出 AI 的回复（流式输出）。但是，工具调用的 JSON 也是**被切碎了一段一段发过来的**，你怎么处理？

**✅ 工业级解法：积攒与拼接机制**

在 `stream=True` 的模式下：
1. 如果模型决定写普通文字，`delta.content` 会有值。
2. 如果模型决定调用工具，`delta.content` 是空的，而 `delta.tool_calls` 会分片吐出函数名和 JSON 参数。

你需要在本地把分片的 JSON 拼接成完整的字符串，解析它，静默执行工具，然后再向模型发起**第二轮无缝的流式请求**供前端消费。

```python
from openai import OpenAI

client = OpenAI()
messages = [{"role": "user", "content": "今天北京天气如何？"}]

# 开启流式响应
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    tools=my_tools,
    stream=True
)

# 1. 准备好容器，用于积攒碎裂的 tool_calls
tool_calls_accumulator = {}

for chunk in response:
    delta = chunk.choices[0].delta
    
    # 场景 A：纯文本输出，直接丢给前端
    if delta.content:
        print(delta.content, end="", flush=True)
        
    # 场景 B：拦截到了工具调用的碎片
    if delta.tool_calls:
        for tc in delta.tool_calls:
            idx = tc.index  # 可能并发调用多个工具，index 代表当前是第几个工具
            if idx not in tool_calls_accumulator:
                tool_calls_accumulator[idx] = {"id": tc.id, "name": tc.function.name, "arguments": ""}
            # 不断拼接 JSON 参数字符串
            if tc.function.arguments:
                tool_calls_accumulator[idx]["arguments"] += tc.function.arguments

# 当循环结束时，如果 tool_calls_accumulator 不为空，说明模型刚才是在静默拼写函数
if tool_calls_accumulator:
    # 构造发回给模型的历史消息
    assistant_tool_msg = {"role": "assistant", "tool_calls": []}
    for idx, tc in tool_calls_accumulator.items():
        assistant_tool_msg["tool_calls"].append({
            "id": tc["id"],
            "type": "function",
            "function": {"name": tc["name"], "arguments": tc["arguments"]}
        })
    messages.append(assistant_tool_msg)
    
    # 遍历刚才积攒的工具调用，在本地统统执行掉！
    for idx, tc in tool_calls_accumulator.items():
        result = registry.execute(tc["name"], tc["arguments"])
        messages.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": result
        })
    
    # 把带着工具结果的 messages 发给模型，发起第二次流式调用，前端就能看到文字了！
    print("\n[系统执行完工具，大模型开始真正回答]:")
    second_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True
    )
    for chunk in second_response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
```

---

### 🎉 大师之路总结

1. **写一个牛逼的装饰器**，将所有繁杂的 Python 函数一键注册给模型，远离 `if/else` 的地狱。
2. 在工具调用侧引入 **Asyncio**，利用并行工具能力（Parallel Calling）榨干网络性能。
3. 把 Python 里让人崩溃的 **Exception 转化成大模型能看懂的文字**，让大模型变成一个能主动重试、道歉的超强客服。
4. 战胜**流式分片拼接**的终极难题，为用户提供丝滑的文字输出体验。

掌握了这四点，你就可以去设计极其复杂的多智能体（Multi-Agent）系统和高度自治的 RPA（机器人流程自动化）平台了！
