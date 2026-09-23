"""
Lesson 5: 工业级工具注册表 (ToolRegistry) —— 告别 if/else 派发面条代码
"""
import os
import json
from typing import Callable, Dict, Any, Type
from pydantic import BaseModel, Field
from openai import OpenAI, pydantic_function_tool

class ToolRegistry:
    """生产级动态工具注册与执行中枢"""
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self.openai_tools = []

    def register(self, model: Type[BaseModel], name: str, description: str):
        """装饰器：将真实的 Python 函数与 Pydantic 参数模型及 OpenAI Schema 绑定"""
        def decorator(func: Callable):
            self._functions[name] = func
            self.openai_tools.append(
                pydantic_function_tool(model=model, name=name, description=description)
            )
            return func
        return decorator

    def execute(self, tool_name: str, arguments_json: str) -> str:
        """根据函数名动态派发并执行"""
        if tool_name not in self._functions:
            return json.dumps({"error": f"Tool '{tool_name}' not registered."}, ensure_ascii=False)
        
        target_func = self._functions[tool_name]
        try:
            kwargs = json.loads(arguments_json)
            result = target_func(**kwargs)
            if isinstance(result, (dict, list)):
                return json.dumps(result, ensure_ascii=False)
            return str(result)
        except Exception as e:
            return json.dumps({"error": f"Execution error in {tool_name}: {str(e)}"}, ensure_ascii=False)

# ================= 业务开发场景使用 =================
registry = ToolRegistry()

# 业务工具 1: 加法计算器
class AddArgs(BaseModel):
    a: float = Field(description="第一个加数")
    b: float = Field(description="第二个加数")

@registry.register(model=AddArgs, name="add_numbers", description="计算两个数字之和")
def add_numbers(a: float, b: float):
    print(f"   [本地执行] 计算: {a} + {b}")
    return {"operation": "add", "result": a + b}

# 业务工具 2: 查询用户VIP状态
class UserArgs(BaseModel):
    user_id: str = Field(description="用户ID")

@registry.register(model=UserArgs, name="get_user_vip", description="查询用户的会员等级与折扣")
def get_user_vip(user_id: str):
    print(f"   [本地执行] 查询用户 {user_id} 的会员状态")
    return {"user_id": user_id, "is_vip": True, "level": "Diamond", "discount": 0.85}

print("=" * 60)
print(f"✅ 注册表已就绪！当前共载入 {len(registry.openai_tools)} 个工具")
for t in registry.openai_tools:
    print(f" - 工具: {t['function']['name']}: {t['function']['description']}")

# 模拟大模型返回指令后的动态执行
sample_json_args = '{"a": 128.5, "b": 256.5}'
print("\n👉 模拟接收到模型指令 add_numbers，自动派发执行：")
exec_result = registry.execute("add_numbers", sample_json_args)
print(f"执行结果: {exec_result}")
