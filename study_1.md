# OpenAI Python SDK 实战闯关指南 (面向 Python 开发者)

这是一份专为 **熟悉 Python 但初次接触 OpenAI API** 的开发者设计的实战指南。

与干巴巴的 API 文档不同，本指南采用 **“代码片段驱动”** 的学习方式。你可以将这里的每一段代码直接复制到你的本地环境中运行，通过修改代码来直观地感受 API 的行为。

---

## 准备工作：环境与认证

在开始之前，确保你已经安装了 SDK 并准备好了 API Key。OpenAI SDK 推荐通过环境变量来管理 Key，这对于熟悉 Python 的你来说应该不陌生。

**1. 安装依赖**
如果还没安装，可以通过 pip 安装（建议在虚拟环境中）：
```bash
pip install openai
```
*(如果想要自动加载 `.env` 文件，可以同时安装 `pip install python-dotenv`)*

**2. 初始化客户端**
在现代开发中，推荐显式实例化 `OpenAI` 客户端，而不是使用全局变量。SDK 会自动读取 `OPENAI_API_KEY` 环境变量。

创建一个 `lesson1_setup.py` 文件并运行：

```python
import os
from openai import OpenAI

# 确保环境变量已设置，例如在终端中运行: export OPENAI_API_KEY="sk-..."
# 如果你使用 python-dotenv，可以在这里 load_dotenv()

# 实例化客户端 (自动从 os.environ 获取 OPENAI_API_KEY)
client = OpenAI()

print("客户端初始化成功！")
print(f"Base URL: {client.base_url}")
```

**📖 源码指引：**
好奇 `client = OpenAI()` 背后发生了什么？去看看 [`src/openai/_client.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/_client.py) 中 `OpenAI` 类的 `__init__` 方法。你会发现它是如何通过 `os.environ.get("OPENAI_API_KEY")` 自动加载环境变量的。

---

## 第一关：你的第一次对话 (Hello World)

OpenAI 最核心的接口是 **Chat Completions (聊天补全)** 接口。与传统的单个字符串输入不同，大模型期望接收的是一个**消息列表 (messages)**。

创建一个 `lesson2_hello.py` 文件并运行：

```python
from openai import OpenAI

client = OpenAI()

# 发起一次简单的对话请求
response = client.chat.completions.create(
    model="gpt-4o-mini",  # 指定使用的模型，gpt-4o-mini 是高性价比的首选
    messages=[{"role": "user", "content": "你好！请用一句话介绍一下 Python 的特点。"}],
)

# 打印完整的响应对象，看看它长什么样 (Pydantic Model)
print("=== 完整响应对象 ===")
print(response.model_dump_json(indent=2))

# 提取核心的回复内容
print("\n=== AI 回复 ===")
reply = response.choices[0].message.content
print(reply)
```

**💡 核心要点：**
1. **`model`**: 必须指定。对于日常测试，`gpt-4o-mini` 既快又便宜。
2. **`messages`**: 这是一个列表。每个元素是一个字典，必须包含 `role` (角色) 和 `content` (内容)。
3. **数据提取**: 响应是一个层级较深的对象。你需要通过 `response.choices[0].message.content` 来拿到纯文本。这是由于 API 的设计需要支持“生成多个候选回复（choices）”的场景（尽管默认只有一个）。

**📖 源码指引：**
- **去哪里看参数定义？** 查看 [`src/openai/types/chat/completion_create_params.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/types/chat/completion_create_params.py)。你可以看到除了 `model` 和 `messages`，还能传哪些参数。
- **去哪里看真正的发请求代码？** 查看 [`src/openai/resources/chat/completions/completions.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/resources/chat/completions/completions.py) 的 `create` 方法。

---

## 第二关：理解角色系统 (System Prompts)

在 `messages` 列表中，`role` 是非常关键的概念。主要的 `role` 有三种：
- `system`: 系统级指令。用于给 AI 设定人设、背景或严格的规则。**它的权重非常高。**
- `user`: 用户的提问或输入。
- `assistant`: AI 模型之前的回复。

让我们用 `system` prompt 把 AI 变成一个专门把代码翻译成大白话的老程序员。

创建一个 `lesson3_system_prompt.py` 文件并运行：

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",  # 复杂指令建议使用 gpt-4o
    messages=[
        {
            "role": "system",
            "content": "你是一个有20年经验的资深 Python 架构师。你的任务是用通俗易懂、带有幽默感的语言解释代码概念。不要写代码，只讲核心思想。",
        },
        {"role": "user", "content": "请给我解释一下 Python 里的 '装饰器(Decorator)' 到底是个啥？"},
    ],
)

print(response.choices[0].message.content)
```

**💪 实操建议：**
尝试修改上面的 `system` content，比如把它改成：“你是一个暴躁的导师，回答问题前先数落学生一顿”，然后再运行一次，感受 `system` prompt 对模型输出风格的巨大影响。

**📖 源码指引：**
想知道都有哪些角色 (`role`) 是合法的吗？查看类型定义：[`src/openai/types/chat/chat_completion_message_param.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/types/chat/chat_completion_message_param.py)。你会发现除了 `system`, `user`, `assistant`，还有给工具用的 `tool` 和 `function` 角色。

---

## 第三关：多轮对话与状态管理 (上下文)

**一个极易犯的错误**：认为 OpenAI 服务端会记住你们的对话记录。
**事实是**：API 是**完全无状态的 (Stateless)**。你要想让 AI 记住上下文，**必须在每次请求时，把历史记录完整地传过去。**

让我们手写一个能在终端里聊天的多轮对话机器人。

创建一个 `lesson4_chat_loop.py` 文件并运行：

```python
from openai import OpenAI

client = OpenAI()

# 1. 初始化对话历史，先放入系统人设
conversation_history = [{"role": "system", "content": "你是一个简洁的 AI 助手。回答尽量简短，不要超过30个字。"}]

print("🤖 聊天机器人已启动 (输入 'quit' 退出)\n")

while True:
    # 2. 获取用户输入
    user_input = input("你: ")
    if user_input.lower() in ["quit", "exit"]:
        break

    # 3. 将用户的话追加到历史记录中
    conversation_history.append({"role": "user", "content": user_input})

    # 4. 把完整的历史记录发给 API
    response = client.chat.completions.create(model="gpt-4o-mini", messages=conversation_history)

    # 5. 提取 AI 回复
    ai_reply = response.choices[0].message.content
    print(f"AI: {ai_reply}\n")

    # 6. 【关键】把 AI 的回复也追加到历史记录中，作为 'assistant' 角色
    conversation_history.append({"role": "assistant", "content": ai_reply})
```

**💡 核心要点：**
仔细看第 3 步和第 6 步。你的 `conversation_history` 列表会像雪球一样越滚越大。在实际的商业项目中（比如一个长期的聊天框），你通常需要控制这个列表的长度，比如只保留最近的 10 条对话，否则会超出模型的 Token 限制。

**📖 源码指引：**
如果你在构建真正具备长期记忆、检索外部知识（RAG）的机器人，开发者通常不会像上面这样手动维护 `messages`，而是使用更高级的 **Assistants API**。这部分的源码可以从 [`src/openai/resources/beta/assistants.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/resources/beta/assistants.py) 入手了解。

---

## 第四关：掌控输出风格 (控制参数)

在调用接口时，除了 `model` 和 `messages`，还有几个经常需要调整的参数。

创建一个 `lesson5_parameters.py` 文件并运行：

```python
from openai import OpenAI

client = OpenAI()

prompt = "给一家新开的咖啡馆起3个独特的名字。"

# 示例 A：极度保守、确定的输出 (Temperature = 0)
print("=== 保守生成 (Temperature=0) ===")
res_conservative = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.0,  # 取值范围 0.0 ~ 2.0，默认为 1.0。0 表示极度确定、毫无创造力。
)
print(res_conservative.choices[0].message.content)

# 示例 B：极度发散、富有创意的输出 (Temperature = 1.5)
print("\n=== 创意生成 (Temperature=1.5) ===")
res_creative = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=1.5,  # 较高的值会让输出更加随机和发散
    max_tokens=100,  # 限制 AI 最多生成的 token 数量，防止它喋喋不休
)
print(res_creative.choices[0].message.content)
```

**💡 核心要点：**
- **`temperature`**: 写代码/做数学题等需要严谨逻辑的场景，设置为 0。写小说/起名字/头脑风暴，设置为 0.7 - 1.5。
- **`max_tokens`**: 控制生成的最大长度。注意，如果 AI 话没说完触碰到了这个限制，输出会被硬生生截断。

**📖 源码指引：**
想看看 API 响应里除了文本还返回了啥？比如到底消耗了多少 Token？
你可以查看 [`src/openai/types/chat/chat_completion.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/types/chat/chat_completion.py) 里的 `CompletionUsage` 定义。在代码里你可以打印 `response.usage.total_tokens` 来获取总消耗。

---

## 第六关：进阶源码研读 (Source Code Architecture)

当你会用这些基础 API 之后，作为一名资深开发者，去了解它底层的实现逻辑是非常有帮助的。这个 SDK 是如何把你的 Python 参数转换为 HTTP 请求，又是如何反序列化结果的呢？你可以按照下面的路径去阅读源码：

### 1. 入口与网络层：`client` 是怎么初始化的？
*   **去看哪：** [`src/openai/_client.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/_client.py)
*   **看什么：** 重点看 `OpenAI` 和 `AsyncOpenAI` 类的 `__init__` 方法。你会发现它默认从环境变量读取 `api_key`，并且底层使用了一个共享的 `httpx.Client` (或 `httpx.AsyncClient`) 来管理连接池。

### 2. 自动化生成架构与 HTTP 请求发起
*   **去看哪：** [`src/openai/resources/chat/completions/completions.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/resources/chat/completions/completions.py)
*   **看什么：** 找 `create` 方法。你会发现这个 SDK 的绝大部分 API 文件（包括这个）是根据 OpenAPI 规范**自动生成**的。它负责把 `messages`, `model` 等参数打包成 JSON，并调用底层的 `.post()` 方法发送请求。

### 3. Pydantic 魔法：结构化输出是如何解析的？
*   **去看哪：** [`src/openai/lib/chat/_completions.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/lib/chat/_completions.py)
*   **看什么：** 找 `parse` 方法。这是极为少见的人类**手写文件**（存放于 `lib/` 目录下）。它里面实现了极其复杂的逻辑：如何在发请求前把你传进去的 Pydantic BaseModel 转换成 OpenAI 期望的 JSON Schema，并在拿到响应后，自动调用 Pydantic 解析出来。

### 4. 流式生成器 (Streaming) 的底层秘密
*   **去看哪：** [`src/openai/_streaming.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/_streaming.py)
*   **看什么：** 看 `Stream` 类是如何封装底层的 HTTP Chunk 读取的。它本质上是一个迭代器，解析 Server-Sent Events (SSE)，让你能在业务代码中愉快地 `for chunk in response`。

### 5. 如何获取原始 HTTP Header (如速率限制)
*   **去看哪：** [`src/openai/_response.py`](file:///Users/pangyao/Desktop/util/llm/code/openai-python/src/openai/_response.py) (查找 `.with_raw_response` 机制)
*   **看什么：** 如果你需要绕过 Pydantic 解析，直接获取原生的 `httpx.Response`（比如你想看 OpenAI 给你返回的 `x-ratelimit-remaining` header），可以通过 `client.chat.completions.with_raw_response.create(...)` 来实现。

---

## 🎉 下一步去哪儿？

当你在本地敲完前 5 关，并顺着第 6 关翻阅了一遍核心源码后，你已经超越了 90% 的调用者，真正掌握了 OpenAI Python SDK 的精髓。

接下来的业务技能，你可以根据项目需要查阅这些我为你准备好的中文翻译文档：
1. [**流式响应 (Streaming)**](README_zh.md) - 实现打字机效果，大幅降低用户等待焦虑。
2. [**结构化输出 (Structured Outputs)**](helpers_zh.md) - 强制大模型每次都返回完美的 JSON。
3. [**代理与高级网络配置 (HTTPX2)**](httpx2_zh.md) - 在国内网络环境或使用企业代理网关时的必备技能。
