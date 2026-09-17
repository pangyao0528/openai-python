from openai import OpenAI

API_KEY = ""

client = OpenAI(
    api_key=API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4/",
)
# 这是最新的写法，目前国内各大平台还赞时未支持
# client.responses.create 接口。这是 OpenAI 最近新推出的一个非常新的 API 接口
# （对应的底层路由是 /v1/responses）。但国内的大部分模型厂商（如智谱 GLM）尚未兼容这个新接口。

# 目前各大厂商 100% 兼容的统一标准对话接口是 client.chat.completions.create
# response = client.responses.create(
#     model="gpt-5.5",
#     instructions="You are a coding assistant that talks like a pirate.",
#     input="How do I check if a Python object is an instance of a class?",
# )

# 通用的目前是当前写法
response = client.chat.completions.create(
    model="glm-4.6v", # 智谱目前常用的是 glm-4 
    messages=[
        {"role": "system", "content": "You are a coding assistant that talks like a pirate."},
        {"role": "user", "content": "How do I check if a Python object is an instance of a class?"}
    ]
)

print(response.choices[0].message.content)