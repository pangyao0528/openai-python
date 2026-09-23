"""
Lesson 6: 大模型自愈容错机制 (Self-Healing) —— 让 AI 自主纠偏 Bad Request
"""
import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "your-api-key-here"),
    base_url=os.environ.get("OPENAI_BASE_URL", None)
)
model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

# 模拟一个有严格校验规则的本地银行接口
def query_account_balance(account_number: str) -> str:
    """仅接受 8 位纯数字的账号格式"""
    if not account_number.isdigit() or len(account_number) != 8:
        # 主动抛出校验异常
        raise ValueError(f"账号 '{account_number}' 格式无效！银行账号必须为恰好 8 位纯数字（例如：88001234）。")
    return json.dumps({"account": account_number, "balance": "¥52,380.00", "currency": "CNY"}, ensure_ascii=False)

def safe_execute(func, arguments_json: str) -> str:
    """安全执行沙箱：将异常转化为大模型能理解的系统诊断信息，坚决不让应用崩溃"""
    try:
        args = json.loads(arguments_json)
        return func(**args)
    except json.JSONDecodeError as e:
        return f"[System Error] Arguments JSON format error: {str(e)}. Please regenerate valid JSON."
    except ValueError as e:
        # 参数校验失败：把明确的修正要求反馈给大模型
        return f"[System Error] Parameter validation failed: {str(e)} Please check the user requirements and provide the corrected 8-digit account number."
    except Exception as e:
        return f"[System Error] Internal tool failure: {str(e)}"

class AccountArgs(BaseModel):
    account_number: str = Field(description="8位银行账号数字")

tools = [
    pydantic_function_tool(model=AccountArgs, name="query_account_balance", description="根据8位银行账号查询可用余额")
]

print("=" * 60)
print("演示自愈容错场景：假设大模型或用户第一次传入了带破折号的账号 '8800-1234'")

bad_arguments = '{"account_number": "8800-1234"}'
feedback_error = safe_execute(query_account_balance, bad_arguments)
print(f"\n1️⃣ 本地执行被安全拦截并捕获错误: \n   {feedback_error}")

print("\n2️⃣ 将该错误信息包装进 role='tool' 发给大模型，模型会理解错误并向用户说明或尝试纠正。")
print("=" * 60)
