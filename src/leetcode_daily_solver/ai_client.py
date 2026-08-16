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
        )

    def analyze_problem(self, problem: dict) -> str:
        """Analyze a problem and suggest approach."""
        # Try to get Chinese content first, fallback to English
        content = problem.get('translatedContent', '') or problem.get('content', '')
        title = problem.get('translatedTitle', '') or problem.get('title', '')

        prompt = f"""分析以下 LeetCode 题目并给出最佳解题思路：

标题: {title}
难度: {problem.get('difficulty')}
标签: {[tag.get('name') for tag in problem.get('topicTags', [])]}
题目内容: {content[:2000]}

请用中文提供：
1. 题目理解
2. 关键思路
3. 使用的算法/数据结构
4. 时间/空间复杂度分析
"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "你是一位资深算法竞赛选手，请用中文回答。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content or ""

    def generate_code(self, problem: dict, analysis: str, language: str) -> str:
        """Generate solution code."""
        prompt = f"""Write a {language} solution for this LeetCode problem:

Title: {problem.get('title')}
Difficulty: {problem.get('difficulty')}
Problem: {problem.get('content', '')[:2000]}

Analysis: {analysis}

Requirements:
1. Return ONLY the code, no explanations
2. Use proper function signature
3. Handle edge cases
4. Include comments for clarity
"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": f"You are an expert {language} programmer. Return only code, no markdown."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        code = response.choices[0].message.content or ""
        # Clean code block markers
        if code.startswith("```"):
            code = code.split("\n", 1)[1]
        if code.endswith("```"):
            code = code.rsplit("```", 1)[0]
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
        )
        fixed_code = response.choices[0].message.content or ""
        if fixed_code.startswith("```"):
            fixed_code = fixed_code.split("\n", 1)[1]
        if fixed_code.endswith("```"):
            fixed_code = fixed_code.rsplit("```", 1)[0]
        return fixed_code.strip()
