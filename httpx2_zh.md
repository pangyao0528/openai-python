# 迁移至 HTTPX2

OpenAI Python SDK 现已全面使用 [HTTPX2](https://httpx2.pydantic.dev/) 作为其同步和异步的 HTTP 客户端。HTTPX2 库在安装 `openai` 时会自动一并安装，而旧版的 `httpx` 包不再被默认安装。本指南将介绍如何平稳过渡，以应对与 SDK 的 HTTP 层发生交互的修改。

## 如果你使用的是 SDK 默认的 HTTP 客户端

当你创建 `OpenAI` 或 `AsyncOpenAI` 客户端时如果没有提供自定义的 `http_client`，你现有的 API 调用、响应解析、流式传输、身份认证、重试逻辑和数字超时设置都会继续正常工作，完全不受影响：

```python
from openai import OpenAI

client = OpenAI(timeout=30.0)
response = client.responses.create(model="gpt-5.5", input="Hello")
```

不需要单独或额外安装 HTTPX2：
```sh
pip install openai
```

如果你的应用程序直接导入了 `httpx`（例如你原本依赖 SDK 附带安装了它），现在你需要手动添加自己的 `httpx` 依赖项，或者将所有的引用迁移到 `httpx2`。安装新版 SDK 不会自动为你安装旧版的 `httpx`。

## TLS 证书与受信任根证书库 (Trust Stores)

**HTTPX2 改变了默认的 TLS 信任库行为，这也同样适用于使用 SDK 默认 HTTP 客户端的应用。** 之前，HTTPX 会根据 `certifi` 包提供的 CA 证书包来校验凭证。而 HTTPX2 改为了使用**操作系统自带的信任库**，并且 SDK 也已不再安装 `certifi`。

这在一些缺乏系统 CA 证书的精简版容器镜像 (container images)、企业内带有 TLS 拦截策略的代理环境、或是依赖定制化 `certifi` 证书包的场景中可能会导致证书校验失败。你需要将所需的 CA 证书安装到操作系统的信任库中，或者手动通过环境变量配置你的证书包路径：

```sh
export SSL_CERT_FILE=/path/to/ca-bundle.pem
```

或者配置受信任 CA 证书所在的目录：

```sh
export SSL_CERT_DIR=/path/to/ca-directory
```

默认情况下 `trust_env=True`，因此上述环境变量会自动被读取。如果想要在自定义的客户端上显式控制，可通过 `verify` 属性传递一个 `ssl.SSLContext`：

```python
import ssl
from openai import OpenAI, DefaultHttpx2Client

ssl_context = ssl.create_default_context(cafile="/path/to/ca-bundle.pem")
client = OpenAI(http_client=DefaultHttpx2Client(verify=ssl_context))
```

在异步配置中使用 `DefaultAsyncHttpx2Client(verify=ssl_context)` 即可。SDK 自带的 aiohttp 传输层也是沿用的这些 HTTPX2 TLS 配置。

## 如果你提供了一个自定义的 HTTP 客户端

请使用 HTTPX2 客户端以及 HTTPX2 配置对象。SDK 提供了一些便捷辅助类，能够帮助你保留官方建议的超时、连接池和重定向等默认参数：

```python
import httpx2
from openai import OpenAI, AsyncOpenAI, DefaultHttpx2Client, DefaultAsyncHttpx2Client

proxy_client = OpenAI(http_client=DefaultHttpx2Client(proxy="http://proxy.example.com:8080"))

transport_client = OpenAI(
    http_client=DefaultHttpx2Client(
        transport=httpx2.HTTPTransport(local_address="0.0.0.0"),
        timeout=httpx2.Timeout(30.0, connect=5.0),
    )
)

async_client = AsyncOpenAI(http_client=DefaultAsyncHttpx2Client(timeout=httpx2.Timeout(30.0)))
```

你也可以直接构造 `httpx2.Client` 和 `httpx2.AsyncClient` 实例，不过除非你主动设置，它们将不再享用 SDK 建议的参数，而是使用 HTTPX2 的自身默认配置。

以前名字 `DefaultHttpxClient` 和 `DefaultAsyncHttpxClient` 依旧有效，但它们现在构造出来的也是 HTTPX2 客户端。为了指代更加明确，建议统一改用 `DefaultHttpx2Client` 和 `DefaultAsyncHttpx2Client`。

## 超时、URL、Transport 等配置对象的变更

需要将以往代码里的 HTTPX 对象替换为 HTTPX2 对象：

| 之前的对象 | HTTPX2 的对应对象 |
| --- | --- |
| `httpx.Client` | `httpx2.Client` |
| `httpx.AsyncClient` | `httpx2.AsyncClient` |
| `httpx.Timeout` | `httpx2.Timeout` |
| `httpx.URL` | `httpx2.URL` |
| `httpx.Limits` | `httpx2.Limits` |
| `httpx.HTTPTransport` | `httpx2.HTTPTransport` |
| `httpx.AsyncHTTPTransport` | `httpx2.AsyncHTTPTransport` |
| `httpx.MockTransport` | `httpx2.MockTransport` |

如果你之前设置了细粒度 SDK 超时限制，它应该变为：
```python
import httpx2
from openai import OpenAI

client = OpenAI(timeout=httpx2.Timeout(60.0, connect=5.0, read=20.0))
```

基于数字的超时值（如 `timeout=30.0`）及普通字符串 URL 不受影响。

## 拦截器 (Event Hooks) 与身份验证 (Authentication)

现在认证 Handler 和各种钩子 (hooks) 接收到的是 HTTPX2 的请求与响应对象。需要相应更新你的自定义的 Auth 类和类型批注：

```python
import httpx2
from openai import OpenAI, DefaultHttpx2Client

def log_request(request: httpx2.Request) -> None:
    print(request.method, request.url)

client = OpenAI(http_client=DefaultHttpx2Client(event_hooks={"request": [log_request]}))
```

## aiohttp 拓展

目前可选的 aiohttp 依赖支持使用的是原生的 HTTPX2 传输层实现。它无需安装过时的 HTTPX 或外部的 `httpx-aiohttp` 适配器：

```sh
pip install 'openai[aiohttp]'
```

```python
from openai import AsyncOpenAI, DefaultAioHttpClient

client = AsyncOpenAI(http_client=DefaultAioHttpClient())
```

其中 `DefaultAioHttpClient()` 本身就是一个 `httpx2.AsyncClient`。应用开发者无需直接导入或构建该底层的传输层。

## 临时逃生通道：兼容旧版 HTTPX 客户端

如果你严重依赖那些只支持 HTTPX 的拦截库、测试库 (比如 RESPX)，你可以显式地安装 legacy httpx，然后主动传入旧版客户端实例进行兜底处理：

```sh
pip install openai httpx
```

```python
from typing import Any, cast
import httpx
from openai import OpenAI

client = OpenAI(http_client=cast(Any, httpx.Client()))
```

不过旧版 HTTPX 仅在运行时被兜底支持。SDK 官方类型检查现在全都要求 HTTPX2 客户端。强行传入会引起 mypy 或 Pyright 等报错，你需要配合 `cast(Any, ...)` 绕过。

在使用原生 HTTPX 兜底时，`cast_to=httpx2.Response` 不会将 HTTPX 的响应转化为 HTTPX2 的响应。强烈建议将这视为短期的临时解决方案，未来可能会被彻底剔除。
