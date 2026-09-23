"""
Lesson 10: 终极自主智能体引擎 (Autonomous Agent Engine)
特性：
1. While-Loop 自主多轮状态机（彻底取代手工嵌套 if）
2. 最大轮次熔断保护 (max_turns 防死循环烧 Token)
3. 装饰器工具注册表 (ToolRegistry)
4. 上下文滑动修剪策略 (Context Pruning 防爆 Token)
5. 错误安全诊断反哺 (Self-Healing)
"""
import os
import json
from typing import Callable, Dict, Type, List
from pydantic import BaseModel, Field
from openai import OpenAI, pydantic_function_tool

# ----------------- 1. 通用工具注册表 -----------------
class ToolRegistry:
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self.openai_tools = []

    def register(self, model: Type[BaseModel], name: str, description: str):
        def decorator(func: Callable):
            self._functions[name] = func
            self.openai_tools.append(
                pydantic_function_tool(model=model, name=name, description=description)
            )
            return func
        return decorator

    def execute(self, tool_name: str, arguments_json: str) -> str:
        """带异常自愈保护的执行器"""
        if tool_name not in self._functions:
            return f"[System Error] Tool '{tool_name}' 不存在，请不要臆想该工具。"
        
        func = self._functions[tool_name]
        try:
            kwargs = json.loads(arguments_json)
            result = func(**kwargs)
            return json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result)
        except json.JSONDecodeError as e:
            return f"[System Error] 传入的参数非合法 JSON 格式: {str(e)}，请修正参数后重试。"
        except Exception as e:
            return f"[System Error] 执行工具发生错误: {str(e)}"

# ----------------- 2. 自主 Agent 状态机 -----------------
class AutonomousAgent:
    def __init__(
        self, 
        client: OpenAI, 
        registry: ToolRegistry, 
        model: str = "gpt-4o-mini",
        max_turns: int = 6
    ):
        self.client = client
        self.registry = registry
        self.model = model
        self.max_turns = max_turns

    def _prune_context(self, messages: List[dict], max_count: int = 15) -> List[dict]:
        """保持 System 提示词不变，仅保留最近的历史上下文"""
        if len(messages) <= max_count:
            return messages
        system_msgs = [m for m in messages if m.get("role") == "system"]
        recent = messages[-(max_count - len(system_msgs)):]
        return system_msgs + recent

    def run(self, user_prompt: str) -> str:
        print("\n" + "=" * 65)
        print(f"🚀 [Agent 任务启动]: {user_prompt}")
        print("=" * 65)

        messages = [
            {
                "role": "system", 
                "content": (
                    "你是一个具备自主决策能力的专业智能体助手。"
                    "你可以根据需要连续多轮调用工具，直至获取到充分信息并彻底解决用户的问题。"
                    "获取所有必要数据后，给出详尽、准确的总结回答。"
                )
            },
            {"role": "user", "content": user_prompt}
        ]

        turn = 0
        while turn < self.max_turns:
            turn += 1
            print(f"\n🔄 --- [思考与决策轮次 {turn}/{self.max_turns}] ---")

            # 1. 提交对话请求 (带上下文修剪)
            active_messages = self._prune_context(messages)
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=active_messages,
                    tools=self.registry.openai_tools
                )
            except Exception as e:
                return f"❌ 调用大模型失败: {e}"

            assistant_msg = response.choices[0].message
            # 记录大模型的回复
            messages.append(assistant_msg)

            # 2. 检查是否达成终态：如果没有工具调用，说明 Agent 自主推理完成！
            if not assistant_msg.tool_calls:
                print("🎯 [Agent 自主决策]: 信息收集充足，已生成最终解答。")
                print("=" * 65)
                return assistant_msg.content

            # 3. 遍历并执行所有下发的工具调用
            print(f"⚙️ [工具派发]: 检测到 {len(assistant_msg.tool_calls)} 个操作指令")
            for tc in assistant_msg.tool_calls:
                name = tc.function.name
                args = tc.function.arguments
                print(f"   ▶ 调用工具: {name} | 参数: {args}")
                
                # 动态安全执行
                output = self.registry.execute(name, args)
                print(f"   ◀ 执行返回: {output}")

                # 将工具执行结果装配回对话流
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": output
                })

        # 4. 超出轮次触发熔断
        return f"⚠️ [安全熔断] Agent 超过了最大轮次上限 ({self.max_turns} 次)，已安全中止避免死循环。"

# ================= 业务工具接入与端到端实战 =================
registry = ToolRegistry()

# 工具 1: 股票实时行情
class StockArgs(BaseModel):
    ticker: str = Field(description="美股代码，例如 AAPL, TSLA, NVDA")

@registry.register(model=StockArgs, name="get_stock_price", description="获取美股标的的最新交易价格 (美元)")
def get_stock_price(ticker: str):
    prices = {"AAPL": 224.50, "TSLA": 248.20, "NVDA": 118.80}
    price = prices.get(ticker.upper(), 100.0)
    return {"ticker": ticker.upper(), "price_usd": price, "status": "market_open"}

# 工具 2: 实时外汇汇率
class ForexArgs(BaseModel):
    base_currency: str = Field(description="源货币代码，如 USD")
    target_currency: str = Field(description="目标货币代码，如 CNY")

@registry.register(model=ForexArgs, name="get_forex_rate", description="查询外汇实时兑换汇率")
def get_forex_rate(base_currency: str, target_currency: str):
    if base_currency.upper() == "USD" and target_currency.upper() == "CNY":
        return {"base": "USD", "target": "CNY", "rate": 7.1250}
    return {"rate": 1.0}

# 工具 3: 精确高精度数学计算器
class CalcArgs(BaseModel):
    expression: str = Field(description="需要计算的数学表达式，例如 '100 * 224.5 * 7.125'")

@registry.register(model=CalcArgs, name="calculator", description="精确计算数学运算表达式")
def calculator(expression: str):
    # 安全计算器实现
    allowed_chars = set("0123456789+-*/. ()")
    if not all(c in allowed_chars for c in expression):
        return "Error: 包含非法字符，仅允许基础四则运算"
    try:
        val = eval(expression, {"__builtins__": None}, {})
        return {"expression": expression, "result": round(float(val), 2)}
    except Exception as e:
        return f"Error: 计算失败 {e}"

# ================= 运行测试 =================
if __name__ == "__main__":
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", "your-api-key-here"),
        base_url=os.environ.get("OPENAI_BASE_URL", None)
    )
    model = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

    agent = AutonomousAgent(client=client, registry=registry, model=model, max_turns=6)
    
    # 复合型连续推理任务：需要先查股价 -> 再查汇率 -> 再进行资产换算
    complex_task = "帮我查询苹果公司 (AAPL) 现在的股价，并按实时汇率折算成人民币。如果我持有 100 股，总市值是多少人民币？"
    
    try:
        final_answer = agent.run(complex_task)
        print("\n🏆 [Agent 最终交付结果]:")
        print(final_answer)
    except Exception as e:
        print(f"\n⚠️ 运行提示: {e}")
        print("💡 提示：可通过设置环境变量 OPENAI_API_KEY 运行该完整 Agent 实例。")
