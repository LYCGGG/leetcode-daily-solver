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
            timeout=120.0,  # 2 minute timeout
        )

    def analyze_problem(self, problem: dict) -> str:
        """Analyze a problem and suggest approach."""
        # Try to get Chinese content first, fallback to English
        content = problem.get('translatedContent', '') or problem.get('content', '')
        title = problem.get('translatedTitle', '') or problem.get('title', '')

        # Shorten content to reduce processing time
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
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "你是算法专家，请用中文简洁回答。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        msg = response.choices[0].message
        # Mimo may return content in reasoning_content
        return msg.content or msg.reasoning_content or ""

    def generate_code(self, problem: dict, analysis: str, language: str) -> str:
        """Generate solution code."""
        # Get Chinese title if available
        title = problem.get('translatedTitle', '') or problem.get('title', '')

        # Use very simple prompt for Mimo
        prompt = f"用{language}解决LeetCode题目：{title}。只输出代码，格式：class Solution:"

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        msg = response.choices[0].message
        code = msg.content or msg.reasoning_content or ""
        # Clean code block markers
        if "```" in code:
            # Extract code from markdown blocks
            parts = code.split("```")
            for part in parts:
                if part.strip() and not part.strip().startswith(("python", "java", "cpp", "javascript")):
                    code = part.strip()
                    break
        # Remove language identifier at start
        for lang in ["python", "java", "cpp", "javascript", "typescript"]:
            if code.startswith(lang):
                code = code[len(lang):].strip()
                break
        return code.strip()

    def fix_code(self, problem: dict, code: str, error: str, language: str) -> str:
        """Fix code based on error feedback."""
        prompt = f"""Fix this {language} code that has an error:

Title: {problem.get('title')}
Code:
{code}

Error:
{error}

Requirements:
1. Return ONLY the fixed code, no explanations
2. Keep the same function signature
3. Fix the specific error
"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": f"You are an expert {language} debugger. Return only code, no markdown."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        msg = response.choices[0].message
        fixed_code = msg.content or msg.reasoning_content or ""
        if fixed_code.startswith("```"):
            fixed_code = fixed_code.split("\n", 1)[1]
        if fixed_code.endswith("```"):
            fixed_code = fixed_code.rsplit("```", 1)[0]
        return fixed_code.strip()
