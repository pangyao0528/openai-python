# 复杂推理与 Agent (ReAct)

在你学习过 Tools（函数调用）之后，你可能会发现一个问题：如果你给了模型 5 个不同的 Tools（比如查天气、查日历、发邮件、读文件、写文件），对于一个简单的指令（"今天天气如何？"），它知道去调用查天气的工具。

但是，如果面对复杂的指令呢？
> "帮我看看我明天的日历，如果在下午 3 点有空，就给老板发一封邮件安排开会，并在我的备忘录文件里记录下来。如果没空，就算了。"

这时候，普通的 Prompt 加上 Tools 很容易让模型混乱，它可能会选错工具，或者参数传错，或者步骤乱掉。

## 1. 核心武器：Chain of Thought (CoT 思维链)

研究表明，**强迫大模型在给出最终答案或采取行动之前，先"把思考过程写出来"**，能大幅度提升它的逻辑推理能力。

**魔法咒语：**
> "Let's think step by step." (让我们一步一步地思考)

在 Prompt 中，我们不让它直接行动，而是要求它按照特定的格式输出思考过程。

## 2. Agent 的终极形态：ReAct 框架

ReAct = **Re**asoning (推理) + **Act**ing (行动)。这是目前构建 Agent 最经典的 Prompt 范式。

我们会在 System Prompt 中规定模型必须按照以下循环来工作：

1.  **Thought (思考)**：现在我需要做什么？
2.  **Action (行动)**：调用什么 Tool？（对应 function calling）
3.  **Observation (观察)**：Tool 返回了什么结果？（你把 function 的结果传回给它）
4.  ...循环...直到得出最终结果...
5.  **Final Answer (最终答案)**：告诉用户最终结果。

### ReAct Prompt 示例：
```markdown
# 目标
解答用户的问题。你可以使用以下工具：[查天气, 查日历, 发邮件]。

# 规则
你必须且只能按照以下格式交替输出：

Thought: 我现在应该考虑...
Action: 调用某个工具...

(等待用户输入 Observation)

Thought: 根据观察结果，我接下来应该...
Action: 调用另一个工具...

直到你收集到足够的信息，最后输出：
Final Answer: 最终的答复。
```

结合 OpenAI 原生的 Function Calling 能力，我们可以在 System Prompt 中重点强调让模型在调用工具前，**必须先输出 `Thought`（思考过程）**。这能让复杂的 Tool Calling 准确率大幅提升。

---
👉 **接下来，请打开 `lesson3_agent_reasoning.py`，我们将演示如何用 Prompt 引导模型拆解复杂任务。**
