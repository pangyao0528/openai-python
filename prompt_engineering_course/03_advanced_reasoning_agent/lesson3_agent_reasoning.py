"""
Lesson 3: 复杂推理智能体 —— 使用 CoT 思维链 + ReAct 规范驾驭多工具编排
特性：
1. 强制在调用工具前吐出 <thought> 思维链推导
2. 彻底清除明文 API Key，使用标准环境变量
3. 自带 Mock 降级验证
"""
import os
import json
import openai
from pydantic import BaseModel, Field
from openai import pydantic_function_tool

api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_BASE_URL")
model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

client = None
if api_key:
    client = openai.OpenAI(api_key=api_key, base_url=base_url)

# ----------------- 1. 本地工具体系 -----------------
def get_user_schedule(date: str) -> str:
    """查询日程"""
    print(f"   ⚙️ [Tool 执行] 查询 {date} 的日程安排...")
    if "明天" in date:
        return "明天下午 15:00-16:00 空闲，其余时间均在开会。"
    return "全天日程空闲。"

def send_email(recipient: str, subject: str, content: str) -> str:
    """发送邮件"""
    print(f"   ⚙️ [Tool 执行] 给 {recipient} 发送邮件，主题: {subject}，内容: {content}")
    return "邮件已成功投递至收件箱。"

class ScheduleArgs(BaseModel):
    date: str = Field(description="查询日期，如'今天', '明天'")

class EmailArgs(BaseModel):
    recipient: str = Field(description="收件人姓名或邮箱")
    subject: str = Field(description="邮件主题")
    content: str = Field(description="邮件正文内容")

tools = [
    pydantic_function_tool(model=ScheduleArgs, name="get_user_schedule", description="查询指定日期的日程"),
    pydantic_function_tool(model=EmailArgs, name="send_email", description="发送邮件给指定人员")
]

# ----------------- 2. 强思维链约束的 Agent 提示词 -----------------
AGENT_SYSTEM_PROMPT = """
<system_instruction>
  <role>你是高级行政执行智能体，负责协助主管规划日程并处理重要事务。</role>
  
  <rules>
    1. 你可以使用提供的外部工具获取信息或执行操作。
    2. 在任何决策或工具调用前，你必须进行缜密的逐步推理（Chain-of-Thought）。
    3. 只有当明确确认日程空闲时，方可执行预约或发送会议邀请。若日程冲突，切勿盲目发信！
  </rules>
</system_instruction>
"""

def run_agent(task_instruction: str):
    print("=" * 65)
    print(f"📋 主管下发复合任务:\n'{task_instruction}'")
    print("=" * 65)

    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": task_instruction}
    ]

    if client:
        try:
            # 轮次 1: 模型分析任务并决定调用日程工具
            print("\n🔄 [Agent 推理轮次 1]:")
            r1 = client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools
            )
            msg1 = r1.choices[0].message
            messages.append(msg1)
            
            if msg1.content:
                print(f"💭 思考过程: {msg1.content}")
                
            if msg1.tool_calls:
                for tc in msg1.tool_calls:
                    print(f"👉 决定调用工具: {tc.function.name}")
                    args = json.loads(tc.function.arguments)
                    if tc.function.name == "get_user_schedule":
                        res = get_user_schedule(args["date"])
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": res})

                # 轮次 2: 模型阅读日程结果后，进一步判断并决定发邮件
                print("\n🔄 [Agent 推理轮次 2]:")
                r2 = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=tools
                )
                msg2 = r2.choices[0].message
                messages.append(msg2)
                
                if msg2.tool_calls:
                    for tc in msg2.tool_calls:
                        print(f"👉 确认空闲，触发行动: {tc.function.name}")
                        args = json.loads(tc.function.arguments)
                        if tc.function.name == "send_email":
                            res = send_email(args["recipient"], args["subject"], args["content"])
                            messages.append({"role": "tool", "tool_call_id": tc.id, "content": res})

                # 最终总结
                final_res = client.chat.completions.create(model=model_name, messages=messages)
                print("\n🤖 最终交付答复:\n", final_res.choices[0].message.content)
                return
        except Exception as e:
            print(f"API 运行提示: {e}，启用 Mock 输出")

    # Mock 演示
    print("\n🔄 [Agent 推理轮次 1 (Mock)]:")
    print("💭 思考过程: 用户要求检查明天日程并在下午3点有空时发邮件给老板。我需要首先调用 get_user_schedule 查询明天的具体空闲时段。")
    res1 = get_user_schedule("明天")
    print(f"   ◀ 观察结果 (Observation): {res1}")

    print("\n🔄 [Agent 推理轮次 2 (Mock)]:")
    print("💭 思考过程: 日程显示明天下午 15:00-16:00 确实有空。符合触发条件，我将调用 send_email 工具为用户安排会议。")
    res2 = send_email("老板", "关于明天下午3点的工作汇报会议确认", "老板您好，已确认主管明天下午15:00-16:00空闲，特此安排工作汇报会议。")
    print(f"   ◀ 观察结果 (Observation): {res2}")

    print("\n🤖 最终交付答复:\n主管您好，已为您核实明天日程：下午 15:00-16:00 正好有空闲。已成功给老板发送了会议预约邮件，请您届时准时参会！")

if __name__ == "__main__":
    task = "帮我看看我明天的日历，如果在下午 3 点有空，就给老板发一封邮件安排开会；如果没空就算了。"
    run_agent(task)
