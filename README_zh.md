# OpenAI Python API 库

<!-- prettier-ignore -->
[![PyPI version](https://img.shields.io/pypi/v/openai.svg?label=pypi%20(stable))](https://pypi.org/project/openai/)

OpenAI Python 库使得从任何 Python 3.10+ 应用程序中访问 OpenAI REST API 变得十分便捷。该库包含所有请求参数和响应字段的类型定义，并提供了由 [HTTPX2](https://httpx2.pydantic.dev/) 驱动的同步和异步客户端。

它是基于我们的 [OpenAPI 规范](https://github.com/openai/openai-openapi) 自动生成的。

## 文档

REST API 文档可以在 [platform.openai.com](https://platform.openai.com/docs/api-reference) 找到。此库的完整 API 参考可以在 [api.md](api.md) 找到。

## 安装

```sh
# 从 PyPI 安装
pip install openai
```

## 用法

此库的完整 API 参考可以在 [api.md](api.md) 中找到。

与 OpenAI 模型交互的主要 API 是 [Responses API](https://developers.openai.com/api/reference/resources/responses)。你可以使用以下代码让模型生成文本。

```python
import os
from openai import OpenAI

client = OpenAI(
    # 这是默认行为，可省略
    api_key=os.environ.get("OPENAI_API_KEY"),
)

response = client.responses.create(
    model="gpt-5.5",
    instructions="You are a coding assistant that talks like a pirate.",
    input="How do I check if a Python object is an instance of a class?",
)

print(response.output_text)
```

以前生成文本的标准 API（将无限期受支持）是 [Chat Completions API](https://platform.openai.com/docs/api-reference/chat)。你可以使用以下代码通过该 API 生成文本。

```python
from openai import OpenAI

client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-5.5",
    messages=[
        {"role": "developer", "content": "Talk like a pirate."},
        {
            "role": "user",
            "content": "How do I check if a Python object is an instance of a class?",
        },
    ],
)

print(completion.choices[0].message.content)
```

虽然你可以提供 `api_key` 关键字参数，但我们建议使用 [python-dotenv](https://pypi.org/project/python-dotenv/) 将 `OPENAI_API_KEY="My API Key"` 添加到你的 `.env` 文件中，这样你的 API 密钥就不会存储在源代码控制系统中。
[点击此处获取 API 密钥](https://platform.openai.com/settings/organization/api-keys)。

### 工作负载身份认证 (Workload Identity Authentication)

针对像托管 Kubernetes、Azure 和 Google Cloud Platform 等安全的自动化环境，可以使用云身份提供商的短效令牌来进行工作负载身份认证，而不是使用长效 API 密钥。

#### Kubernetes (服务账户令牌)

```python
from openai import OpenAI
from openai.auth import k8s_service_account_token_provider

client = OpenAI(
    workload_identity={
        "identity_provider_id": "idp-123",
        "service_account_id": "sa-456",
        "provider": k8s_service_account_token_provider(
            "/var/run/secrets/kubernetes.io/serviceaccount/token"
        ),
    },
)

response = client.chat.completions.create(
    model="gpt-5.5",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

#### Azure (托管身份)

```python
from openai import OpenAI
from openai.auth import azure_managed_identity_token_provider

client = OpenAI(
    workload_identity={
        "identity_provider_id": "idp-123",
        "service_account_id": "sa-456",
        "provider": azure_managed_identity_token_provider(
            resource="https://management.azure.com/",
        ),
    },
)
```

#### Google Cloud Platform (计算引擎元数据)

```python
from openai import OpenAI
from openai.auth import gcp_id_token_provider

client = OpenAI(
    workload_identity={
        "identity_provider_id": "idp-123",
        "service_account_id": "sa-456",
        "provider": gcp_id_token_provider(audience="https://api.openai.com/v1"),
    },
)
```

#### 自定义主题令牌提供者 (Custom subject token provider)

```python
from openai import OpenAI


def get_custom_token() -> str:
    return "your-jwt-token"


client = OpenAI(
    workload_identity={
        "identity_provider_id": "idp-123",
        "service_account_id": "sa-456",
        "provider": {
            "token_type": "jwt",
            "get_token": get_custom_token,
        },
    }
)
```

你也可以自定义令牌刷新缓冲时间（默认为过期前 1200 秒，即 20 分钟）：

```python
from openai import OpenAI
from openai.auth import k8s_service_account_token_provider

client = OpenAI(
    workload_identity={
        "identity_provider_id": "idp-123",
        "service_account_id": "sa-456",
        "provider": k8s_service_account_token_provider("/var/token"),
        "refresh_buffer_seconds": 120.0,
    }
)
```

### 视觉 (Vision)

使用图片 URL：

```python
prompt = "What is in this image?"
img_url = "https://api.nga.gov/iiif/a2e6da57-3cd1-4235-b20e-95dcaefed6c8/full/!800,800/0/default.jpg"

response = client.responses.create(
    model="gpt-5.5",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"{img_url}"},
            ],
        }
    ],
)
```

使用 Base64 编码的图片字符串：

```python
import base64
from openai import OpenAI

client = OpenAI()

prompt = "What is in this image?"
with open("path/to/image.png", "rb") as image_file:
    b64_image = base64.b64encode(image_file.read()).decode("utf-8")

response = client.responses.create(
    model="gpt-5.5",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:image/png;base64,{b64_image}"},
            ],
        }
    ],
)
```

## 异步用法 (Async usage)

只需导入 `AsyncOpenAI` 替代 `OpenAI` 即可，并在每次调用 API 时使用 `await`：

```python
import os
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(
    # 这是默认行为，可省略
    api_key=os.environ.get("OPENAI_API_KEY"),
)


async def main() -> None:
    response = await client.responses.create(
        model="gpt-5.5", input="Explain disestablishmentarianism to a smart five year old."
    )
    print(response.output_text)


asyncio.run(main())
```

同步与异步客户端在功能上是完全一致的。

### 搭配 aiohttp 使用

默认情况下，异步客户端使用 HTTPX2。如果为了提升并发性能，你也可以将 `aiohttp` 用作 HTTPX2 传输层。

```sh
# 从 PyPI 安装
pip install openai[aiohttp]
```

然后通过 `http_client=DefaultAioHttpClient()` 来实例化客户端以启用它：

```python
import os
import asyncio
from openai import DefaultAioHttpClient
from openai import AsyncOpenAI


async def main() -> None:
    async with AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),  # 默认行为，可省略
        http_client=DefaultAioHttpClient(),
    ) as client:
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say this is a test",
                }
            ],
            model="gpt-5.5",
        )


asyncio.run(main())
```

## 流式响应 (Streaming responses)

我们提供了对使用 Server-Sent Events (SSE) 的流式响应的支持。

```python
from openai import OpenAI

client = OpenAI()

stream = client.responses.create(
    model="gpt-5.5",
    input="Write a one-sentence bedtime story about a unicorn.",
    stream=True,
)

for event in stream:
    print(event)
```

异步客户端的接口也是完全相同的：

```python
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI()


async def main():
    stream = await client.responses.create(
        model="gpt-5.5",
        input="Write a one-sentence bedtime story about a unicorn.",
        stream=True,
    )

    async for event in stream:
        print(event)


asyncio.run(main())
```

## 实时 API (Realtime API)

Realtime API 让你能够构建低延迟、多模态的对话体验。目前它同时支持文本和音频的输入输出，并通过 WebSocket 连接支持[函数调用 (function calling)](https://platform.openai.com/docs/guides/function-calling)。

SDK 底层使用了 [`websockets`](https://websockets.readthedocs.io/en/stable/) 库来管理连接。

基于文本的简单示例：

```py
import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI()

    async with client.realtime.connect(model="gpt-realtime-2") as connection:
        await connection.session.update(
            session={"type": "realtime", "output_modalities": ["text"]}
        )

        await connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Say hello!"}],
            }
        )
        await connection.response.create()

        async for event in connection:
            if event.type == "response.output_text.delta":
                print(event.delta, flush=True, end="")

            elif event.type == "response.output_text.done":
                print()

            elif event.type == "response.done":
                break

asyncio.run(main())
```

处理音频时，可以参考这个[音频终端 (TUI) 示例脚本](https://github.com/openai/openai-python/blob/main/examples/realtime/push_to_talk_app.py)。

### 实时 API 的错误处理

任何时候发生错误，Realtime API 将发送一个 [`error` 事件](https://platform.openai.com/docs/guides/realtime-model-capabilities#error-handling)，并且连接会保持打开以继续可用。这意味着你需要自行处理这些错误，因为 SDK 收到 `error` 事件时不会直接抛出异常。

```py
client = AsyncOpenAI()

async with client.realtime.connect(model="gpt-realtime-2") as connection:
    ...
    async for event in connection:
        if event.type == 'error':
            print(event.error.type)
            print(event.error.code)
            print(event.error.event_id)
            print(event.error.message)
```

## 异常处理 (Handling errors)

当库无法连接到 API 时（如网络连接问题或超时），会抛出 `openai.APIConnectionError` 的子类。
当 API 返回非成功状态码（即 4xx 或 5xx 响应）时，会抛出 `openai.APIStatusError` 的子类。
所有的错误均继承自 `openai.APIError`。

```python
import openai
from openai import OpenAI

client = OpenAI()

try:
    client.fine_tuning.jobs.create(
        model="gpt-4o",
        training_file="file-abc123",
    )
except openai.APIConnectionError as e:
    print("The server could not be reached")
    print(e.__cause__)  # 底层异常
except openai.RateLimitError as e:
    print("A 429 status code was received; we should back off a bit.")
except openai.APIStatusError as e:
    print("Another non-200-range status code was received")
    print(e.status_code)
    print(e.response)
```

## 请求超时 (Timeouts)

请求默认会在 10 分钟后超时。你可以通过 `timeout` 选项配置它：

```python
import httpx2
from openai import OpenAI

# 配置所有请求的默认超时：
client = OpenAI(
    # 20 秒 (默认是 10 分钟)
    timeout=20.0,
)

# 或者单次请求覆盖配置：
client.with_options(timeout=5.0).chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "How can I list all files in a directory using Python?",
        }
    ],
    model="gpt-5.5",
)
```

## Microsoft Azure OpenAI

要想与 [Azure OpenAI](https://learn.microsoft.com/azure/ai-services/openai/overview) 结合使用此库，请使用 `AzureOpenAI` 类而不是 `OpenAI` 类。

```py
from openai import AzureOpenAI

# 从环境变量 AZURE_OPENAI_API_KEY 中获取 API Key
client = AzureOpenAI(
    api_version="2023-07-01-preview",
    azure_endpoint="https://example-endpoint.openai.azure.com",
)

completion = client.chat.completions.create(
    model="deployment-name",  # e.g. gpt-35-instant
    messages=[
        {
            "role": "user",
            "content": "How do I output all files in a directory using Python?",
        },
    ],
)
print(completion.to_json())
```

## 版本控制 (Versioning)

本项目主要遵循 [SemVer](https://semver.org/spec/v2.0.0.html) 惯例。

## 需求 (Requirements)

Python 3.10 或以上版本。
