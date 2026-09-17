from openai import OpenAI

API_KEY = ""

client = OpenAI(
    api_key=API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4/",
)
# 这是最新的写法，目前国内各大平台还赞时未支持
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