"""
Lesson 4: 高阶思维范式实战 —— Self-Refine (自我反思与批判改进闭环)
特性：
1. 工业级 Generator -> Critic -> Refiner 三阶段自动迭代流水线
2. 彻底清除硬编码明文 API Key，使用标准环境变量
3. 自带 Mock 降级验证
"""
import os
import openai

api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_BASE_URL")
model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

client = None
if api_key:
    client = openai.OpenAI(api_key=api_key, base_url=base_url)

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    if client:
        try:
            res = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            return res.choices[0].message.content or ""
        except Exception as e:
            print(f"API 调用提示: {e}，启用 Mock 降级。")
    return ""

def run_self_refine_pipeline(task: str):
    print("=" * 70)
    print(f"📝 原始写作任务:\n{task}")
    print("=" * 70)

    # 阶段 1: 初稿生成 (Generator)
    print("\n👉 [阶段 1: 初稿快速生成 (Drafting)]...")
    generator_system = "你是一名企业公关写手。请根据用户需求撰写一份简短的公告草稿。"
    draft = call_llm(generator_system, task)
    if not draft:
        draft = "尊敬的用户：由于我们服务器硬件故障，今天上午服务崩溃了2小时，数据有点错乱，正在紧急修复。给大家添麻烦了，我们将给每个人赔偿5元优惠券。"
    print(f"📄 【第一版初稿】:\n{draft}\n")

    # 阶段 2: 严苛批判找茬 (Critic)
    print("👉 [阶段 2: 独立评审员严苛批判 (Critiquing)]...")
    critic_system = """
你是一名极其严苛的公关总监与法务专家。请审查公关草稿，并按照以下 3 项量规进行严厉挑刺：
1. 【用词合规性】：是否使用了容易引发恐慌或法务风险的词汇（如"崩溃"、"错乱"）？
2. 【诚意与共情】：态度是否过于生硬消极？
3. 【补偿得体度】：赔偿措施是否显得廉价小气、缺乏诚意？

请列出具体的修改意见清单。
"""
    critique = call_llm(critic_system, f"待审查草稿：\n{draft}")
    if not critique:
        critique = (
            "1. 违规词汇：使用了'崩溃'、'错乱'等负面恐慌词汇，严重损害品牌信誉，应改为'系统服务波动'、'部分显示异常'。\n"
            "2. 态度问题：缺乏对用户业务受阻的真诚歉意，显得推卸责任。\n"
            "3. 补偿失当：'5元优惠券'极具讽刺意味，容易引发二次舆情嘲弄，建议改为发放'7天高级会员服务体验卡'并提供一对一工单优先通道。"
        )
    print(f"🔍 【评审员批判意见】:\n{critique}\n")

    # 阶段 3: 结合挑刺意见重构润色 (Refiner)
    print("👉 [阶段 3: 结合批判意见重构定稿 (Refining)]...")
    refiner_system = """
你是一名拥有20年危机公关经验的高级架构师。
请结合原始任务、第一版草稿以及评审员的犀利批判意见，彻底重写一份言辞得体、态度真诚、法务合规的高品质公告。
"""
    refine_input = f"原始任务: {task}\n第一版草稿:\n{draft}\n\n评审员修改建议:\n{critique}\n\n请直接输出重写后的最终版本："
    final_version = call_llm(refiner_system, refine_input)
    if not final_version:
        final_version = (
            "尊敬的用户：\n\n"
            "今日上午 10:15 起，由于核心节点网络负载异常波动，部分区域用户在访问系统时遇到加载延迟或短暂中断。\n"
            "经技术团队全力紧急处置，相关服务已于 12:00 全面恢复平稳运行。\n\n"
            "对于此次服务波动给您工作与生活带来的不便，我们深表歉意。\n"
            "为表达我们的歉意与诚意，我们将为所有受影响用户自动延期 7 天高级 VIP 服务，并开通专属技术保障通道。\n"
            "感谢您的理解与持续陪伴！"
        )
    print(f"🏆 【最终精修版本】:\n{final_version}")
    print("=" * 70)

if __name__ == "__main__":
    task_desc = "写一篇由于云服务器宕机导致服务中断2小时的客户致歉信。"
    run_self_refine_pipeline(task_desc)
