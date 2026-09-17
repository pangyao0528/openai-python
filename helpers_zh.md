# 结构化输出解析助手 (Structured Outputs Parsing Helpers)

OpenAI API 支持通过 `response_format` 请求参数从模型中提取 JSON，关于该 API 的更多细节，请参阅[此指南](https://platform.openai.com/docs/guides/structured-outputs)。

SDK 提供了一个 `client.chat.completions.parse()` 方法，它是 `client.chat.completions.create()` 的一层封装，旨在提供更丰富的 Python 类型集成，并返回一个 `ParsedChatCompletion` 对象（它是标准 `ChatCompletion` 类的子类）。

## 使用 Pydantic 模型自动解析响应内容

你可以将一个 Pydantic 模型传递给 `.parse()` 方法，SDK 会自动将该模型转换为 JSON Schema，发送给 API，并将响应内容解析回给定的模型中。

```py
from typing import List
from pydantic import BaseModel
from openai import OpenAI

class Step(BaseModel):
    explanation: str
    output: str

class MathResponse(BaseModel):
    steps: List[Step]
    final_answer: str

client = OpenAI()
completion = client.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "You are a helpful math tutor."},
        {"role": "user", "content": "solve 8x + 31 = 2"},
    ],
    response_format=MathResponse,
)

message = completion.choices[0].message
if message.parsed:
    print(message.parsed.steps)
    print("answer: ", message.parsed.final_answer)
else:
    print(message.refusal)
```

## 解析 Responses API 输出

使用 `client.responses.parse(..., text_format=YourModel)` 将 Responses API 的输出解析为 Pydantic 模型。同样的解析规则也适用于 `client.responses.stream(..., text_format=YourModel)` 及其异步等效方法。

- 包含 `phase="final_answer"` 的消息会被解析。没有 `phase` 字段或 `phase` 为 null 的消息会保留旧版行为并被解析。
- 评论 (Commentary) 及其他显式阶段将保留其原始文本和元数据，且 `parsed=None`，即使文本恰好符合 Schema。
- `output_parsed` 会返回第一个成功解析的结果；若没有，则返回 `None`。如果模型返回了拒绝 (refusal)，不会将评论作为后备答案。
- 在符合条件的消息中，如果出现了无效的 JSON 或不符合 Schema 的文本，依然会引发验证错误。缺失的 phase 不会从文本或模型名称中推断得出。

`output_text` 会继续拼接所有输出文本（包括评论）。如需结构化结果，请使用 `output_parsed`；当你重播消息 (replaying messages) 且希望保留它们原本的阶段时，请保留 `output`。

## 自动解析函数调用 (Function Tool Calls)

如果你满足以下条件，`.parse()` 方法也会自动解析 `function` 的工具调用：

- 你使用了 `openai.pydantic_function_tool()` 助手方法
- 你的工具 schema 被标记为 `"strict": True`

例如：

```py
from enum import Enum
from typing import List, Union
from pydantic import BaseModel
import openai

class Table(str, Enum):
    orders = "orders"
    customers = "customers"
    products = "products"

class Column(str, Enum):
    id = "id"
    status = "status"
    expected_delivery_date = "expected_delivery_date"
    delivered_at = "delivered_at"
    shipped_at = "shipped_at"
    ordered_at = "ordered_at"
    canceled_at = "canceled_at"

class Operator(str, Enum):
    eq = "="
    gt = ">"
    lt = "<"
    le = "<="
    ge = ">="
    ne = "!="

class OrderBy(str, Enum):
    asc = "asc"
    desc = "desc"

class DynamicValue(BaseModel):
    column_name: str

class Condition(BaseModel):
    column: str
    operator: Operator
    value: Union[str, int, DynamicValue]

class Query(BaseModel):
    table_name: Table
    columns: List[Column]
    conditions: List[Condition]
    order_by: OrderBy

client = openai.OpenAI()
completion = client.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant. The current date is August 6, 2024. You help users query for the data they are looking for by calling the query function.",
        },
        {
            "role": "user",
            "content": "look up all my orders in may of last year that were fulfilled but not delivered on time",
        },
    ],
    tools=[
        openai.pydantic_function_tool(Query),
    ],
)

tool_call = (completion.choices[0].message.tool_calls or [])[0]
print(tool_call.function)
assert isinstance(tool_call.function.parsed_arguments, Query)
print(tool_call.function.parsed_arguments.table_name)
```

### 与 `.create()` 的不同之处

`chat.completions.parse()` 方法在使用时，施加了一些 `chat.completions.create()` 没有的限制：

- 如果响应结束时的 `finish_reason` 是 `length` 或 `content_filter`，将会分别抛出 `LengthFinishReasonError` 或 `ContentFilterFinishReasonError` 错误。
- 仅支持 strict 的函数工具，即传递形式必须为 `{'type': 'function', 'function': {..., 'strict': True}}`。

# 流式传输助手 (Streaming Helpers)

OpenAI 在交互时支持响应的流式传输，涵盖 [Chat Completion](#chat-completions-api) 与 [Assistant](#assistant-streaming-api) API。

## 聊天补全 API (Chat Completions API)

SDK 提供了一个 `.chat.completions.stream()` 方法，它是 `.chat.completions.create(stream=True)` 的一层封装，不仅提供了粒度更细的事件 API，还会自动对每个差值 (delta) 进行累加拼接。

它同样支持前文提到的所有[解析助手](#structured-outputs-parsing-helpers)。

与 `.create(stream=True)` 不同，`.stream()` 方法必须结合**上下文管理器 (context manager)** 使用，以防止意外的响应泄漏：

```py
from openai import AsyncOpenAI

client = AsyncOpenAI()

async with client.chat.completions.stream(
    model='gpt-4o-2024-08-06',
    messages=[...],
) as stream:
    async for event in stream:
        if event.type == 'content.delta':
            print(event.content, flush=True, end='')
```

当进入上下文管理器时，会返回一个 `ChatCompletionStream` 或 `AsyncChatCompletionStream` 实例。这类似于 `.create(stream=True)` 在同步下是迭代器，在异步下是异步迭代器。迭代器抛出的完整事件列表在[下文](#chat-completions-events)列出。

当上下文管理器退出时，该响应将被关闭。不过，`stream` 实例在上下文外依然可被访问。

### 聊天补全事件 (Chat Completions Events)

这些事件允许你跟踪对话生成的进度、访问局部结果并分离处理流的不同部分。

你可以会遇到的事件类型包括：

#### ChunkEvent
API 发送的每一个 chunk 都会抛出该事件。
- `type`: `"chunk"`
- `chunk`: API 返回的原始 `ChatCompletionChunk` 对象
- `snapshot`: 当前累计的 chat completion 状态快照

#### ContentDeltaEvent
每当 chunk 中包含新的正文内容时抛出。
- `type`: `"content.delta"`
- `delta`: 该 chunk 收到的新增正文字符串
- `snapshot`: 迄今为止累加的正文内容
- `parsed`: 局部解析完成的内容（如适用）

#### ContentDoneEvent
正文生成完毕时抛出。如果有多个 choices，可能会被触发多次。
- `type`: `"content.done"`
- `content`: 完整生成的正文
- `parsed`: 完整解析的内容（如适用）

#### RefusalDeltaEvent
当 chunk 中包含内容拒绝（refusal）的部分时抛出。
- `type`: `"refusal.delta"`
- `delta`: 该 chunk 新增的拒绝对话字符串
- `snapshot`: 迄今为止累加的拒绝内容快照

#### RefusalDoneEvent
当拒绝内容完整结束时抛出。
- `type`: `"refusal.done"`
- `refusal`: 完整的拒绝内容

#### FunctionToolCallArgumentsDeltaEvent
当 chunk 包含函数调用参数的片段时抛出。
- `type`: `"tool_calls.function.arguments.delta"`
- `name`: 被调用的函数名称
- `index`: 工具调用的索引
- `arguments`: 迄今为止累加的原始 JSON 参数字符串
- `parsed_arguments`: 局部解析出的参数对象
- `arguments_delta`: 该 chunk 收到的一段 JSON 片段

#### FunctionToolCallArgumentsDoneEvent
当函数调用的参数接收完毕时抛出。
- `type`: `"tool_calls.function.arguments.done"`
- `name`: 被调用的函数名
- `index`: 工具调用的索引
- `arguments`: 完整的原始 JSON 参数字符串
- `parsed_arguments`: 完整解析的参数对象。如果你使用的是 `openai.pydantic_function_tool()`，这里会是所给模型的一个实例。

#### LogprobsContentDeltaEvent / DoneEvent / Refusal...
类似于上述的 Delta 和 Done，只是针对 `logprobs` 信息（[日志概率](https://cookbook.openai.com/examples/using_logprobs)）。

### 流方法的其他快捷函数
流式类上还提供了以下两个常用便捷方法：

**`.get_final_completion()`**
返回累加好的完整的 `ParsedChatCompletion` 对象。
```py
async with client.chat.completions.stream(...) as stream:
    ...

completion = await stream.get_final_completion()
print(completion.choices[0].message)
```

**`.until_done()`**
如果你只想阻塞等地流完成，你可以调用 `.until_done()`：
```py
async with client.chat.completions.stream(...) as stream:
    await stream.until_done()
    # 此时流已结束
```

## 助手流式 API (Assistant Streaming API)

OpenAI 支持从 Assistant 返回流式响应。SDK 对 API 做了一层封装，让你可以订阅自己关心的事件类型，以及直接获取累计的响应结果。
更多细节参见官方文档：[Assistant Streaming](https://platform.openai.com/docs/assistants/overview?lang=python)

详细通过 EventHandler 拦截事件以及通过 for 循环获取迭代事件的方法，均可参考对应的代码示例。

### 创建助手流的快捷方法
- `client.beta.threads.runs.stream()`
- `client.beta.threads.create_and_run_stream()`
- `client.beta.threads.runs.submit_tool_outputs_stream()`

### 助手的各类事件钩子 (Assistant Events)
你可以通过重载各类 `on_xxx(self, ...)` 钩子来订阅并处理消息。如 `on_text_created`, `on_tool_call_delta` 等等。

# 轮询助手 (Polling Helpers)

在调用如创建 Run、将文件上传到 Vector Stores 等异步并且需要时间的操作时，SDK 提供了一些用于不断请求最新状态直至到达终态的辅助函数（`*_and_poll` 结尾）。
你可以利用 `poll_interval_ms` 来设置这些轮询接口的请求频次。

```python
client.beta.threads.create_and_run_poll(...)
client.beta.threads.runs.create_and_poll(...)
client.beta.threads.runs.submit_tool_outputs_and_poll(...)
client.vector_stores.files.upload_and_poll(...)
client.vector_stores.files.create_and_poll(...)
client.vector_stores.file_batches.create_and_poll(...)
client.vector_stores.file_batches.upload_and_poll(...)
client.videos.create_and_poll(...)
```
