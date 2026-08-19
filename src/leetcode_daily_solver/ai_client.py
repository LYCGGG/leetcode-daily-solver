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
        """生成代码，利用之前的分析上下文。

        如果对话为空（独立运行），会先用 analysis 构建上下文。
        """
        title = problem.get('translatedTitle', '') or problem.get('title', '')

        # 如果对话为空，先构建上下文
        if not self.conversation:
            self.conversation = [
                {"role": "system", "content": "你是算法专家，请用中文简洁回答。"},
                {"role": "user", "content": f"分析以下 LeetCode 题目：\n标题: {title}\n{analysis}"},
                {"role": "assistant", "content": analysis},
            ]

        prompt = f"用{language}解决LeetCode题目：{title}。只输出代码，格式：class Solution:"

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
        # 重置对话
        self.reset_conversation()

        title = problem.get('translatedTitle', '') or problem.get('title', '')
        content = problem.get('translatedContent', '') or problem.get('content', '')
        short_content = content[:1000] if content else ''

        # 第一步：生成暴力解
        code_prompt = f"""LeetCode 题目: {title}
难度: {problem.get('difficulty')}
描述: {short_content}

请写一个名为 brute_solve 的暴力解函数，参数与题目函数一致（不含 self）。
暴力解必须正确，可以慢。
只输出函数代码，以 def brute_solve 开头。"""

        self.conversation = [
            {"role": "system", "content": "你是代码生成器。只输出 Python 代码，不要解释。"},
            {"role": "user", "content": code_prompt},
        ]
        code_result = self._call_api(self.conversation, temperature=0.3, max_tokens=5000)
        self.conversation.append({"role": "assistant", "content": code_result})

        # 从输出中提取代码（可能包含思考过程）
        brute_code = self._extract_function_code(code_result, "brute_solve")
        if not brute_code:
            logger.debug(f"TestBuilder: 暴力解提取失败，输出:\n{code_result[:500]}")
            return None

        # 第二步：生成测试输入
        input_prompt = f"""现在请生成 {num_cases} 个测试输入。

要求：
- 每行一个测试用例
- 多参数用逗号分隔
- 不要输出任何解释、分析或 markdown
- 直接输出测试数据

示例格式：
1, []
2, [[1,2]]
3, [[1,2],[2,3]]

请直接输出："""

        self.conversation.append({"role": "user", "content": input_prompt})
        input_result = self._call_api(self.conversation, temperature=0.3, max_tokens=1000)
        self.conversation.append({"role": "assistant", "content": input_result})

        # 从输出中提取测试输入（可能包含思考过程）
        test_inputs = self._extract_test_inputs(input_result)
        if not test_inputs:
            logger.debug(f"TestBuilder: 测试输入提取失败，输出:\n{input_result[:500]}")
            return None

        return {"brute_force_code": brute_code, "test_inputs": test_inputs}

    def _parse_build_output(self, text: str) -> dict | None:
        """解析 AI 返回的暴力解+用例文本。失败返回 None。"""
        try:
            if "===BRUTE_FORCE_CODE===" not in text or "===TEST_INPUTS===" not in text:
                logger.debug(f"TestBuilder: 标记未找到，AI 输出前 500 字符:\n{text[:500]}")
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

    def _extract_function_code(self, text: str, func_name: str) -> str | None:
        """从 AI 输出中提取指定函数的代码。

        支持从 markdown 代码块或纯文本中提取。
        """
        import re

        # 尝试从 markdown 代码块提取
        code_block_pattern = r"```(?:python)?\s*\n(.*?)```"
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        for match in matches:
            if f"def {func_name}" in match:
                return match.strip()

        # 尝试从纯文本提取（查找 def func_name 开始的代码块）
        # 支持带类型注解的函数定义
        pattern = rf"(def\s+{func_name}\s*\([^)]*\)[^:]*:.*?)(?=\n\S|\ndef\s|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 如果还是找不到，尝试更宽松的匹配
        # 查找从 def func_name 开始到下一个非缩进行
        lines = text.split("\n")
        in_function = False
        function_lines = []
        for line in lines:
            if re.match(rf"^\s*def\s+{func_name}\s*\(", line):
                in_function = True
                function_lines = [line]
            elif in_function:
                if line.strip() == "" or line[0] == " " or line[0] == "\t":
                    function_lines.append(line)
                else:
                    break
        
        if function_lines:
            return "\n".join(function_lines).strip()

        return None

    def _extract_test_inputs(self, text: str) -> str | None:
        """从 AI 输出中提取测试输入。

        AI 可能输出思考过程，需要提取实际的测试数据。
        """
        import re

        lines = text.split("\n")
        test_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过明显的非测试数据行
            if any(skip in line for skip in ["首先", "用户", "要求", "示例", "格式", "请", "注意", "需要", "回忆", "测试用例应该", "具体想法", "输出格式"]):
                continue

            # 检查是否像测试数据（包含逗号分隔的参数）
            # 格式：数字, 列表 或 数字, 数字 等
            if re.match(r"^\d+,\s*[\[\(]", line) or re.match(r"^\d+,\s*\d+", line):
                test_lines.append(line)
            elif re.match(r"^\[.*\]$", line):
                # 可能是单独的列表
                test_lines.append(line)

        if test_lines:
            return "\n".join(test_lines)

        # 如果上面没找到，尝试更宽松的匹配
        # 查找包含数字和逗号的行
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 至少包含一个数字和一个逗号
            if re.search(r"\d", line) and "," in line:
                # 排除明显的非数据行
                if not any(skip in line for skip in ["def ", "class ", "import ", "return ", "print"]):
                    test_lines.append(line)

        if test_lines:
            return "\n".join(test_lines[:10])  # 最多取 10 行

        return None
