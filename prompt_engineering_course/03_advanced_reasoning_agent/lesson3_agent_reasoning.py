import os
import json
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 模拟的本地工具集
def get_user_schedule(date):
    """查询用户的日程安排"""
    print(f"\n[Tool 执行] 查询 {date} 的日程...")
    if "明天" in date:
        return "下午 3 点有空，其他时间都在开会。"
    return "日程为空。"

def send_email(to_whom, subject, body):
    """发送邮件"""
    print(f"\n[Tool 执行] 给 {to_whom} 发送邮件，主题：{subject}")
    return "邮件发送成功。"

# 定义 Tools Schema 给大模型看
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_user_schedule",
            "description": "查询用户指定日期的日程安排",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "日期，例如'明天'，'今天'"}
                },
                "required": ["date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "向指定对象发送邮件",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_whom": {"type": "string", "description": "收件人，如'老板'"},
                    "subject": {"type": "string", "description": "邮件主题"},
                    "body": {"type": "string", "description": "邮件正文"}
                },
                "required": ["to_whom", "subject", "body"]
            }
        }
    }
]

# 【核心】：使用 Prompt 强制模型在调用工具前进行 CoT（思维链）推理
AGENT_PROMPT = """
你是一个全能的 AI 助理。你可以使用提供的工具来帮助用户完成复杂的任务。

【至关重要的规则】：
在决定是否调用工具，或者调用哪个工具之前，你**必须**先输出一段你的思考过程，说明你为什么要这么做。
请按照以下格式输出你的思考过程：
<thought>
你的思考过程写在这里...
</thought>

只有在输出思考过程后，你才能调用工具。
如果需要多次调用工具，每次调用前都必须先输出 <thought>。
"""

def run_agent(user_prompt):
    print(f"\n========== 新任务开始 ==========")
    print(f"用户: {user_prompt}")
    
    messages = [
        {"role": "system", "content": AGENT_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    # 简单的循环来处理多步 Tool 调用
    for step in range(5): # 最多允许思考 5 步，防止死循环
        print(f"\n--- 第 {step+1} 步思考 ---")
        response = client.chat.completions.create(
            model="gpt-4o", # 复杂推理建议使用大模型
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # 1. 打印模型的思考过程 (CoT)
        if response_message.content:
             print(f"🤖 模型的思考 (Thought):\n{response_message.content.strip()}")
             
        # 将模型的回复（包括它的 thought 和可能的 tool_calls）追加到对话历史中
        messages.append(response_message)
        
        # 2. 判断模型是否决定调用工具
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"🛠️ 模型决定执行 Action: {function_name}({function_args})")
                
                # 执行本地函数
                if function_name == "get_user_schedule":
                    function_response = get_user_schedule(function_args.get("date"))
                elif function_name == "send_email":
                    function_response = send_email(function_args.get("to_whom"), function_args.get("subject"), function_args.get("body"))
                else:
                    function_response = "Error: 找不到该工具。"
                    
                # 3. 将观察结果 (Observation) 喂回给模型
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
                print(f"👁️ 观察结果 (Observation): {function_response}")
        else:
            # 如果没有 tool_calls，说明任务完成了，得出了最终答案
            print(f"\n✅ 最终完成！")
            break

if __name__ == "__main__":
    complex_task = "帮我看看明天的日历，如果下午 3 点有空，就给老板发一封邮件约他那个时间开会过一下季度总结，邮件语气要非常正式。如果没空，就告诉我没空即可，不需要发邮件。"
    run_agent(complex_task)
