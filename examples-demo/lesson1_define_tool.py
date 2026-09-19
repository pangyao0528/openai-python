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