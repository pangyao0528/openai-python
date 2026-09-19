# Prompt Engineering 高级进阶指南与实战课程

欢迎来到 Prompt Engineering 高级进阶课程！

在学习完 OpenAI API 的 Tools（函数调用）基础之后，单纯的代码逻辑已经不足以支撑复杂的 AI 应用。大模型的表现，本质上取决于你如何向它下达指令——这就是 **Prompt Engineering (提示词工程)** 的核心意义。

本课程分为三个循序渐进的章节，每个章节都包含**理论讲解 (Markdown)** 和**配套实战 (Python)**。

## 学习路线

### 🎯 章节 01：基础框架与角色设定 (Basic Persona and Context)
* **目标**：学习如何通过 System Prompt 牢牢控制模型的角色、语气和边界，防止模型“放飞自我”。
* **内容**：
  * [理论篇：01_theory_system_prompt.md](./01_basic_persona_and_context/01_theory_system_prompt.md)
  * [实战篇：lesson1_roleplay_bot.py](./01_basic_persona_and_context/lesson1_roleplay_bot.py)

### 🧱 章节 02：结构化输出与少样本提示 (Intermediate Structured Output)
* **目标**：掌握 Few-Shot (少样本) 技巧，并学会让大模型不仅能输出自然语言，还能输出严格格式化的 JSON 数据，这对于数据抽取至关重要。
* **内容**：
  * [理论篇：02_theory_few_shot_and_json.md](./02_intermediate_structured_output/02_theory_few_shot_and_json.md)
  * [实战篇：lesson2_data_extractor.py](./02_intermediate_structured_output/lesson2_data_extractor.py)

### 🤖 章节 03：复杂推理与 Agent (Advanced Reasoning Agent)
* **目标**：结合你之前学过的 Tools，学习如何通过提示词引导模型进行“思考 (CoT)”，拆解复杂任务，最终打造一个具备自主推理和行动能力的 Agent。
* **内容**：
  * [理论篇：03_theory_cot_and_react.md](./03_advanced_reasoning_agent/03_theory_cot_and_react.md)
  * [实战篇：lesson3_agent_reasoning.py](./03_advanced_reasoning_agent/lesson3_agent_reasoning.py)

## 建议学习方式

1. 先阅读每个目录下的 `theory.md` 理论文件。
2. 打开对应的 `lesson.py` 文件，仔细阅读代码中的注释。
3. 运行代码，观察输出。
4. **动手修改 Prompt**，看看不同的提示词对模型输出会产生什么影响，这是学好 Prompt 唯一的途径！
