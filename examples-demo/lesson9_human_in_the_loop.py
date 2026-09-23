"""
Lesson 9: 人机协同审批机制 (Human-in-the-Loop, HITL) —— 守护高危操作安全红线
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

# 定义高危敏感操作集合
SENSITIVE_TOOLS = {"transfer_money", "delete_database", "send_external_email"}

# 1. 普通安全工具: 查余额
def query_balance(user: str) -> str:
    return json.dumps({"user": user, "balance": 10000.0, "currency": "USD"}, ensure_ascii=False)

# 2. 高危敏感工具: 转账
def transfer_money(to_account: str, amount: float) -> str:
    return json.dumps({
        "status": "success",
        "tx_id": "TX_998822",
        "to": to_account,
        "amount": amount,
        "msg": "资金已成功划转"
    }, ensure_ascii=False)

def execute_with_hitl(tool_name: str, args_json: str, auto_approve: bool = False) -> str:
    """带人机协同审查的执行网关"""
    args = json.loads(args_json)
    
    # 审查拦截高危操作
    if tool_name in SENSITIVE_TOOLS:
        print("\n" + "!" * 60)
        print(f"🚨 [安全网关拦截] 侦测到大模型请求执行高危敏感操作: '{tool_name}'")
        print(f"📋 拟执行参数: {json.dumps(args, ensure_ascii=False, indent=2)}")
        print("!" * 60)
        
        # 人工审核交互
        if auto_approve:
            choice = "Y"
            print("👉 (自动测试模式已批准)")
        else:
            try:
                choice = input("⚠️ 是否授权大模型执行该操作？[Y=批准 / N=驳回]: ").strip().upper()
            except EOFError:
                choice = "N"

        if choice != "Y":
            print("🛑 [人类管理员驳回] 该操作未获授权！")
            # 将驳回信息包装成标准消息反哺模型，大模型会停止调用并向用户解释
            return json.dumps({
                "status": "rejected",
                "error_code": "PERMISSION_DENIED_BY_HUMAN",
                "message": "用户/管理员拒绝了该笔转账申请，请终止该操作并告知用户已安全取消。"
            }, ensure_ascii=False)
        else:
            print("✅ [人类管理员批准] 正在放行执行...")

    # 执行实际逻辑
    if tool_name == "transfer_money":
        return transfer_money(args["to_account"], args["amount"])
    elif tool_name == "query_balance":
        return query_balance(args["user"])
    return json.dumps({"error": "Unknown tool"})

# ================= 演示测试 =================
class TransferArgs(BaseModel):
    to_account: str = Field(description="收款方账号")
    amount: float = Field(description="转账金额")

tools = [
    pydantic_function_tool(model=TransferArgs, name="transfer_money", description="执行资金转账操作")
]

print("=" * 60)
print("演示场景 1: 人类拒绝高危操作 (驳回测试)")
fake_args = '{"to_account": "6222020200119988", "amount": 5000.0}'
rejected_result = execute_with_hitl("transfer_money", fake_args, auto_approve=False)
print(f"\n反哺给模型的 Tool 消息内容:\n{rejected_result}")

print("\n" + "=" * 60)
print("演示场景 2: 人类批准高危操作 (放行测试)")
approved_result = execute_with_hitl("transfer_money", fake_args, auto_approve=True)
print(f"\n反哺给模型的 Tool 消息内容:\n{approved_result}")
print("=" * 60)
