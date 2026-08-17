"""AI client for code generation and analysis."""

from __future__ import annotations

from loguru import logger
from openai import OpenAI

from .config import AIConfig


class AIClient:
    """AI client for code generation."""

    def __init__(self, config: AIConfig) -> None:
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=120.0,
        )
        self.conversation: list[dict] = []

    def _call_api(
        self,
        messages: list[dict],
        temperature: float = 1.0,
        max_tokens: int = 1000,
    ) -> str:
        """通用 API 调用方法"""
        # NOTE: MiMo API 使用 max_completion_tokens 而非 max_tokens，其他模型可能需要改回 max_tokens
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens,
            top_p=0.95,
        )
        msg = response.choices[0].message
        return msg.content or msg.reasoning_content or ""

    def _clean_code(self, code: str) -> str:
        """清理代码，移除 markdown 标记"""
        if "```" in code:
            # 提取代码块中的内容
            parts = code.split("```")
            for part in parts:
                part = part.strip()
                # 跳过语言标识符行
                if part.startswith(("python", "java", "cpp", "javascript", "typescript")):
                    # 移除语言标识符
                    lines = part.split("\n", 1)
                    if len(lines) > 1:
                        code = lines[1].strip()
                        break
                elif part and not part.startswith(("```", "python", "java", "cpp", "javascript")):
                    code = part
                    break
        return code.strip()

    def reset_conversation(self) -> None:
        """重置对话历史"""
        self.conversation = []

    def analyze_problem(self, problem: dict) -> str:
        """分析题目并给出解题思路"""
        content = problem.get('translatedContent', '') or problem.get('content', '')
        title = problem.get('translatedTitle', '') or problem.get('title', '')
        short_content = content[:1000] if content else ''

        prompt = f"""分析以下 LeetCode 题目并给出解题思路：

标题: {title}
难度: {problem.get('difficulty')}
标签: {', '.join([tag.get('name', '') for tag in problem.get('topicTags', [])][:5])}
题目: {short_content}

请简要用中文回答：
1. 题目理解
2. 解题思路
3. 算法和复杂度
"""
        # 重置对话并开始新对话
        self.reset_conversation()
        self.conversation = [
            {"role": "system", "content": "你是算法专家，请用中文简洁回答。"},
            {"role": "user", "content": prompt},
        ]

        result = self._call_api(self.conversation, temperature=0.7, max_tokens=1000)
        self.conversation.append({"role": "assistant", "content": result})
        return result

    def generate_code(self, problem: dict, analysis: str, language: str) -> str:
        """生成代码，利用之前的分析上下文"""
        title = problem.get('translatedTitle', '') or problem.get('title', '')

        prompt = f"用{language}解决LeetCode题目：{title}。只输出代码，格式：class Solution:"

        # 继续之前的对话上下文
        self.conversation.append({"role": "user", "content": prompt})

        code = self._call_api(self.conversation, temperature=0.1, max_tokens=2000)
        self.conversation.append({"role": "assistant", "content": code})
        return self._clean_code(code)

    def fix_code(self, problem: dict, code: str, error: str, language: str) -> str:
        """修复代码，利用之前的对话上下文"""
        prompt = f"""修复这个{language}代码的错误：

代码:
{code}

错误:
{error}

要求：
1. 只返回修复后的代码
2. 保持相同的函数签名
3. 修复具体错误
"""
        # 继续之前的对话上下文
        self.conversation.append({"role": "user", "content": prompt})

        fixed_code = self._call_api(self.conversation, temperature=0.3, max_tokens=2000)
        self.conversation.append({"role": "assistant", "content": fixed_code})
        return self._clean_code(fixed_code)

    def fix_analysis(self, problem: dict, analysis: str, error: str, code: str = "") -> str:
        """根据错误结果和当前代码更新分析"""
        title = problem.get('translatedTitle', '') or problem.get('title', '')

        prompt = f"""之前的分析和代码提交到 LeetCode 后没有通过。

题目: {title}
错误信息: {error}

之前提交的代码:
{code}

之前的分析:
{analysis}

请重新分析，找出问题所在，并给出正确的解题思路。用中文回答。"""

        # 继续之前的对话上下文
        self.conversation.append({"role": "user", "content": prompt})

        result = self._call_api(self.conversation, temperature=0.7, max_tokens=1000)
        self.conversation.append({"role": "assistant", "content": result})
        return result

    def build_testcases(self, problem: dict, num_cases: int, language: str) -> dict | None:
        """生成暴力解 + 测试用例输入，用于本地差分验证。失败返回 None。

        返回格式:
            {"brute_force_code": "<暴力解python代码>", "test_inputs": "<每行一个参数的用例文本>"}
        """
        title = problem.get('translatedTitle', '') or problem.get('title', '')
        content = problem.get('translatedContent', '') or problem.get('content', '')
        short_content = content[:1000] if content else ''

        prompt = f"""LeetCode 题目: {title}
难度: {problem.get('difficulty')}

题目描述:
{short_content}

请生成用于本地差分测试的内容：
1. 写一个暴力解，命名为 brute_solve 的 Python 函数，参数与题目函数一致(不含 self)。
   暴力解必须对小规模输入保证正确，可以用递归/枚举/模拟，慢没关系，但答案必须正确。如需 import，请包含在代码内。
2. 生成 {num_cases} 个合法测试输入，覆盖以下情况：
   - 边界：空数组、单元素、两个元素、最值
   - 均衡分布：各类型元素数量接近
   - 不均衡分布：某类型元素数量远多于/远少于其他类型(这是很多题的隐藏考点)
   - 较大规模：元素数量取到暴力解能承受的上限(尽量大，但不要导致暴力解超时)
   确保大小、分布多样化，不要全是小而均衡的用例。

严格按以下格式输出，不要 markdown，不要额外解释：

===BRUTE_FORCE_CODE===
def brute_solve(参数):
    # 暴力解代码
===TEST_INPUTS===
用例1参数1
用例1参数2
用例2参数1
===END===

说明：每个用例的参数按函数参数顺序各占一行。单参数题目每行一个输入。"""

        self.conversation.append({"role": "user", "content": prompt})
        result = self._call_api(self.conversation, temperature=0.3, max_tokens=2000)
        self.conversation.append({"role": "assistant", "content": result})
        return self._parse_build_output(result)

    def _parse_build_output(self, text: str) -> dict | None:
        """解析 AI 返回的暴力解+用例文本。失败返回 None。"""
        try:
            if "===BRUTE_FORCE_CODE===" not in text or "===TEST_INPUTS===" not in text:
                return None
            code_part = text.split("===BRUTE_FORCE_CODE===", 1)[1]
            code_part = code_part.split("===TEST_INPUTS===", 1)[0].strip()
            inputs_part = text.split("===TEST_INPUTS===", 1)[1]
            inputs_part = inputs_part.split("===END===", 1)[0].strip()
            if not code_part or not inputs_part:
                return None
            return {"brute_force_code": code_part, "test_inputs": inputs_part}
        except Exception:
            return None
