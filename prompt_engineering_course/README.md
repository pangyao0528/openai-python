# 企业级 Prompt 架构师进阶指南与实战课程

欢迎来到 **Prompt Engineering（提示词工程）企业级架构师进阶课程**！

在现代 AI 应用开发中，代码逻辑只是骨架，而 **Prompt Engineering** 是注入大模型灵魂与决策智慧的神经中枢。无论是打造精准的结构化数据流水线、设计高自治 Agent 智能体、防御黑客的恶意注入越狱，还是建立量化的评估指标，Prompt 架构设计能力都是顶尖 AI 工程师与平庸调包侠之间的核心分水岭。

本课程精心规划了 6 个循序渐进的进阶阶梯，每一章节均包含**系统理论深度解析 (Markdown)** 与**开箱即用的实战源码 (Python)**。

---

## 🗺 课程全景学习路线

```mermaid
graph TD
    classDef l1 fill:#E3F2FD,stroke:#1565C0,stroke-width:2px;
    classDef l2 fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px;
    classDef l3 fill:#FFF3E0,stroke:#E65100,stroke-width:2px;
    classDef l4 fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px;
    classDef l5 fill:#FFEBEE,stroke:#C62828,stroke-width:2px;
    classDef l6 fill:#E0F2F1,stroke:#00695C,stroke-width:2px;

    subgraph 第一阶段：结构化工程基础
        C1["第 01 章：角色边界与 XML 标签工程化架构<br>(消除语义歧义，构建行为宪章)"]:::l1
        C2["第 02 章：结构化输出与少样本 (Few-Shot) 范式<br>(三代抽取技术演进与 Pydantic 严格约束)"]:::l2
    end

    subgraph 第二阶段：推理驱动与智能体
        C3["第 03 章：思维链 (CoT) 与 ReAct 智能体范式<br>(Thought-Action-Observation 闭环)"]:::l3
        C4["第 04 章：高阶思维树与自我反思 (ToT & Self-Refine)<br>(多分支探索、自洽性投票与自我纠错)"]:::l4
    end

    subgraph 第三阶段：企业级安全与工业评测
        C5["第 05 章：提示词攻防对抗与双层 Guardrail 架构<br>(直接/间接注入拦截、双层审判者门禁)"]:::l5
        C6["第 06 章：大模型裁判 (LLM-as-a-Judge) 与自动化评测<br>(评分量规 Rubric、基准回归与记分板)"]:::l6
    end

    C1 --> C2 --> C3 --> C4 --> C5 --> C6
```

---

## 📚 详细章节目录

### 🎯 阶段一：结构化工程基础

#### 章节 01：角色边界与 XML 标签工程化架构
* **核心目标**：从松散的自然语言转向现代工业级 XML 标签结构（`<role>`, `<context>`, `<rules>`, `<format>`, `<security_constraints>`），彻底消除语义歧义与注意力漂移。
* **学习材料**：
  * [理论篇：01_theory_system_prompt.md](./01_basic_persona_and_context/01_theory_system_prompt.md)
  * [实战篇：lesson1_roleplay_bot.py](./01_basic_persona_and_context/lesson1_roleplay_bot.py)

#### 章节 02：结构化输出与少样本 (Few-Shot) 范式
* **核心目标**：洞悉三代结构化抽取演进史（纯 Prompt -> JSON Object Mode -> Pydantic 语法级约束），掌握高质量 Few-Shot 样本挑选的黄金法则。
* **学习材料**：
  * [理论篇：02_theory_few_shot_and_json.md](./02_intermediate_structured_output/02_theory_few_shot_and_json.md)
  * [实战篇：lesson2_data_extractor.py](./02_intermediate_structured_output/lesson2_data_extractor.py)

---

### 🧠 阶段二：推理驱动与智能体

#### 章节 03：思维链 (CoT) 与 ReAct 智能体范式
* **核心目标**：理解 Transformer 自回归生成机理，通过强迫模型在下发 Tool Calling 前生成 `<thought>` 思维链，降低 65% 以上的参数错误率。
* **学习材料**：
  * [理论篇：03_theory_cot_and_react.md](./03_advanced_reasoning_agent/03_theory_cot_and_react.md)
  * [实战篇：lesson3_agent_reasoning.py](./03_advanced_reasoning_agent/lesson3_agent_reasoning.py)

#### 章节 04：高阶思维树与自我反思 (ToT & Self-Refine)
* **核心目标**：告别脆弱的线性单向思考，掌握自洽性多路径投票 (Self-Consistency)、思维树 (Tree of Thoughts) 剪枝回溯，以及 Generator-Critic-Refiner 自我批判纠错流水线。
* **学习材料**：
  * [理论篇：04_theory_thinking_patterns.md](./04_advanced_thinking_patterns/04_theory_thinking_patterns.md)
  * [实战篇：lesson4_thinking_patterns.py](./04_advanced_thinking_patterns/lesson4_thinking_patterns.py)

---

### 🛡 阶段三：企业级安全与工业评测

#### 章节 05：提示词攻防对抗与双层 Guardrail 架构
* **核心目标**：解密直接注入 (Direct Injection)、间接注入 (Indirect Injection)、角色越狱 (DAN) 与提示词盗窃手法；构建生产级双层审判者 (Dual-LLM Guardrail) 安全门禁网关。
* **学习材料**：
  * [理论篇：05_theory_adversarial_defense.md](./05_adversarial_and_defense/05_theory_adversarial_defense.md)
  * [实战篇：lesson5_adversarial_defense.py](./05_adversarial_and_defense/lesson5_adversarial_defense.py)

#### 章节 06：大模型裁判 (LLM-as-a-Judge) 与自动化评测
* **核心目标**：告别凭肉眼感觉调优 Prompt 的业余做法，建立固化黄金基准测试集 (Golden Dataset)，设计严谨量化评分量规 (Rubric)，搭建自动化批量回归流水线与记分板。
* **学习材料**：
  * [理论篇：06_theory_eval_and_judge.md](./06_eval_and_judge/06_theory_eval_and_judge.md)
  * [实战篇：lesson6_eval_pipeline.py](./06_eval_and_judge/lesson6_eval_pipeline.py)

---

## 🚀 极速运行与环境配置指南

所有实战脚本均遵循**安全第一**原则，严禁硬编码任何真实私钥。代码全面支持环境变量驱动，同时自带**智能 Mock 离线模式**（即便没有配置 API Key，代码也能完整运行并输出标准教学结果）：

```bash
# 方式 A：使用标准官方 OpenAI 环境变量
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL_NAME="gpt-4o-mini"

# 方式 B：使用国内大模型兼容端点 (如智谱 GLM、DeepSeek 等)
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"
export OPENAI_MODEL_NAME="glm-4.6v"

# 方式 C：零配置离线运行 (直接启动各章节实战即可自动进入 Mock 模式)
python prompt_engineering_course/01_basic_persona_and_context/lesson1_roleplay_bot.py
python prompt_engineering_course/02_intermediate_structured_output/lesson2_data_extractor.py
python prompt_engineering_course/03_advanced_reasoning_agent/lesson3_agent_reasoning.py
python prompt_engineering_course/04_advanced_thinking_patterns/lesson4_thinking_patterns.py
python prompt_engineering_course/05_adversarial_and_defense/lesson5_adversarial_defense.py
python prompt_engineering_course/06_eval_and_judge/lesson6_eval_pipeline.py
```
