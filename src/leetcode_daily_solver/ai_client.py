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
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """通用 API 调用方法"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
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

    def fix_analysis(self, problem: dict, analysis: str, error: str) -> str:
        """根据错误结果更新分析"""
        title = problem.get('translatedTitle', '') or problem.get('title', '')
        
        prompt = f"""之前的分析有问题，提交到 LeetCode 失败了。

题目: {title}
错误信息: {error}

之前的分析:
{analysis}

请重新分析，找出问题所在，并给出正确的解题思路。用中文回答。"""

        # 继续之前的对话上下文
        self.conversation.append({"role": "user", "content": prompt})

        result = self._call_api(self.conversation, temperature=0.7, max_tokens=1000)
        self.conversation.append({"role": "assistant", "content": result})
        return result
