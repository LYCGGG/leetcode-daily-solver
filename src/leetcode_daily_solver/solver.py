"""Core pipeline for solving daily challenges."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from .ai_client import AIClient
from .config import Config
from .leetcode_client import LeetCodeClient
from .local_tester import parse_test_cases, run_local_test
from .storage import Storage
from .test_builder import TestBuilder


class DailySolver:
    """Orchestrates the daily challenge solving pipeline."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.leetcode = LeetCodeClient(config.leetcode)
        self.ai = AIClient(config.ai)
        self.storage = Storage(config.problems_dir) if config.save_problems else None
        self.test_builder = TestBuilder(self.ai)

    # ========== 独立步骤方法 ==========

    async def fetch_problem(self, title_slug: str | None = None) -> dict:
        """Step 1: 获取题目详情。

        Args:
            title_slug: 题目 slug，为 None 时获取每日挑战。

        Returns:
            包含 problem_info 和 full_problem 的字典。
        """
        if title_slug:
            logger.info(f"Fetching problem: {title_slug}...")
            full_problem = await self.leetcode.get_problem(title_slug)
            problem_info = {
                "questionId": full_problem.get("questionId", ""),
                "questionFrontendId": full_problem.get("questionFrontendId", "0"),
                "title": full_problem.get("title", ""),
                "difficulty": full_problem.get("difficulty", ""),
                "titleSlug": title_slug,
            }
        else:
            logger.info("Fetching daily challenge...")
            challenge = await self.leetcode.get_daily_challenge()
            problem_info = challenge.get("problem", {})
            full_problem = await self.leetcode.get_problem(problem_info.get("titleSlug"))

        question_id = int(problem_info.get("questionFrontendId", 0))
        logger.info(f"Problem: {question_id}. {problem_info.get('title')} ({problem_info.get('difficulty')})")

        # 保存题目信息
        if self.storage:
            tags = [tag.get("name", "") for tag in full_problem.get("topicTags", [])]
            title = full_problem.get("translatedTitle", "") or problem_info.get("title", "")
            content = full_problem.get("translatedContent", "") or full_problem.get("content", "")
            self.storage.save_problem(
                question_id=question_id,
                date=datetime.now().strftime("%Y-%m-%d"),
                title=title,
                title_slug=problem_info.get("titleSlug", ""),
                difficulty=problem_info.get("difficulty", ""),
                tags=tags,
                content=content,
            )

        return {"problem_info": problem_info, "full_problem": full_problem}

    def generate_analysis(self, full_problem: dict) -> str:
        """Step 2: AI 分析题目。

        Args:
            full_problem: 题目完整信息。

        Returns:
            分析文本。
        """
        logger.info("Analyzing problem with AI...")
        analysis = self.ai.analyze_problem(full_problem)
        logger.info(f"Analysis:\n{analysis[:500]}...")

        # 保存分析
        if self.storage:
            question_id = int(full_problem.get("questionFrontendId", 0))
            title_slug = full_problem.get("titleSlug", "")
            self.storage.save_analysis(
                question_id=question_id,
                date=datetime.now().strftime("%Y-%m-%d"),
                title_slug=title_slug,
                analysis=analysis,
            )

        return analysis

    def generate_test_cases(self, full_problem: dict) -> list[dict]:
        """Step 3: 生成测试用例（官方 + 差分）。

        Args:
            full_problem: 题目完整信息。

        Returns:
            测试用例列表。
        """
        logger.info("Generating test cases...")

        # 解析官方用例
        example_testcases = full_problem.get("exampleTestcases", "")
        test_cases = parse_test_cases(
            example_testcases,
            full_problem.get("codeSnippets", []),
            self.config.language,
        )
        logger.info(f"Official cases: {len(test_cases)}")

        # 差分测试补充用例
        if self.config.num_generated_cases > 0:
            generated_cases = self.test_builder.build(
                full_problem, self.config.language, self.config.num_generated_cases,
            )
            if generated_cases:
                test_cases = test_cases + generated_cases
                logger.info(f"Generated {len(generated_cases)} cases, total: {len(test_cases)}")
            else:
                logger.info("No generated cases, using official only")

        # 保存用例
        if self.storage and test_cases:
            question_id = int(full_problem.get("questionFrontendId", 0))
            title_slug = full_problem.get("titleSlug", "")
            self.storage.save_test_cases(
                question_id=question_id,
                title_slug=title_slug,
                test_cases=test_cases,
            )

        return test_cases

    def generate_code(self, full_problem: dict, analysis: str) -> str:
        """Step 4: 生成代码。

        Args:
            full_problem: 题目完整信息。
            analysis: 分析文本（提供上下文）。

        Returns:
            生成的代码。
        """
        logger.info("Generating code...")
        code = self.ai.generate_code(full_problem, analysis, self.config.language)
        logger.info(f"Generated code:\n{code[:500]}...")
        return code

    def test_code_local(self, code: str, test_cases: list[dict]) -> dict:
        """Step 4.5: 本地测试代码。

        Args:
            code: 代码字符串。
            test_cases: 测试用例列表。

        Returns:
            测试结果字典。
        """
        logger.info("Running local test...")
        if not test_cases:
            logger.warning("No test cases available")
            return {"success": False, "error": "No test cases"}

        result = run_local_test(code, test_cases)
        if result["success"]:
            logger.info("✓ Local test passed!")
        else:
            logger.warning(f"✗ Local test failed: {result.get('error')}")
        return result

    async def test_code_leetcode(self, title_slug: str, question_id: str, code: str) -> dict:
        """Step 5: 在 LeetCode 上测试代码。

        Args:
            title_slug: 题目 slug。
            question_id: 题目 ID。
            code: 代码字符串。

        Returns:
            测试结果。
        """
        logger.info("Testing code on LeetCode...")
        result = await self.leetcode.run_code(
            title_slug=title_slug,
            question_id=question_id,
            lang=self.config.language,
            typed_code=code,
        )

        test_state = result.get("state", "")
        test_accepted = result.get("status_msg") == "Accepted" or result.get("accepted")

        if test_state in ("FINISHED", "SUCCESS") and test_accepted:
            logger.info("✓ Code accepted on LeetCode!")
        else:
            logger.warning(f"✗ LeetCode test failed")

        return result

    async def submit_solution(self, title_slug: str, question_id: str, code: str) -> dict:
        """Step 6: 提交解答。

        Args:
            title_slug: 题目 slug。
            question_id: 题目 ID。
            code: 代码字符串。

        Returns:
            提交结果。
        """
        logger.info("Submitting solution...")
        result = await self.leetcode.submit_solution(
            title_slug=title_slug,
            question_id=question_id,
            lang=self.config.language,
            typed_code=code,
        )

        if result.get("status_msg") == "Accepted":
            logger.info("✓ Solution accepted!")
        else:
            logger.warning(f"✗ Submission failed: {result.get('status_msg')}")

        return result

    def save_solution(self, full_problem: dict, code: str) -> Path | None:
        """保存解答代码。

        Args:
            full_problem: 题目完整信息。
            code: 代码字符串。

        Returns:
            保存路径或 None。
        """
        if not self.storage:
            return None

        question_id = int(full_problem.get("questionFrontendId", 0))
        title_slug = full_problem.get("titleSlug", "")
        return self.storage.save_solution(
            question_id=question_id,
            date=datetime.now().strftime("%Y-%m-%d"),
            title_slug=title_slug,
            code=code,
            language=self.config.language,
        )

    # ========== 完整流程 ==========

    async def solve(self, title_slug: str | None = None) -> dict:
        """Run the complete solving pipeline."""
        logger.info("=" * 50)
        logger.info("Starting Daily Challenge Solver")
        logger.info("=" * 50)

        result = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "failed",
            "problem": None,
            "attempts": 0,
            "submit_result": None,
        }

        try:
            # Step 1: Fetch problem
            fetched = await self.fetch_problem(title_slug)
            problem_info = fetched["problem_info"]
            full_problem = fetched["full_problem"]
            question_id = int(problem_info.get("questionFrontendId", 0))
            result["problem"] = {
                "question_id": question_id,
                "title": problem_info.get("title"),
                "difficulty": problem_info.get("difficulty"),
                "title_slug": problem_info.get("titleSlug"),
            }

            # Step 2: AI analysis
            analysis = self.generate_analysis(full_problem)

            # Step 3: Test cases
            test_cases = self.generate_test_cases(full_problem)

            # Step 4-6: Generate, test, submit with auto-fix
            code = None
            last_error = None

            for attempt in range(1, self.config.max_retries + 1):
                result["attempts"] = attempt
                logger.info(f"{'=' * 50}")
                logger.info(f"Attempt {attempt}/{self.config.max_retries}")
                logger.info(f"{'=' * 50}")

                # Step 4: Generate / Fix code
                if attempt == 1:
                    code = self.generate_code(full_problem, analysis)
                else:
                    logger.info(f"[Fix Step B] Fixing code based on error: {last_error}")
                    code = self.ai.fix_code(full_problem, code, last_error, self.config.language)

                # Step 4.5: Local test
                local_result = self.test_code_local(code, test_cases)
                if not local_result["success"]:
                    last_error = local_result.get("error", "Local test failed")
                    analysis = self._handle_failure(
                        full_problem, analysis, last_error, code,
                        question_id, result["date"], problem_info.get("titleSlug", ""), attempt,
                    )
                    continue

                # Step 5: Test on LeetCode
                test_result = await self.test_code_leetcode(
                    problem_info["titleSlug"],
                    str(problem_info.get("questionId", "")),
                    code,
                )

                test_state = test_result.get("state", "")
                test_accepted = test_result.get("status_msg") == "Accepted" or test_result.get("accepted")

                if not (test_state in ("FINISHED", "SUCCESS") and test_accepted):
                    last_error = self._extract_error(test_result)
                    analysis = self._handle_failure(
                        full_problem, analysis, last_error, code,
                        question_id, result["date"], problem_info.get("titleSlug", ""), attempt,
                    )
                    continue

                # Step 6: Submit
                submit_result = await self.submit_solution(
                    problem_info["titleSlug"],
                    str(problem_info.get("questionId", "")),
                    code,
                )

                result["submit_result"] = {
                    "status": submit_result.get("status_msg"),
                    "runtime": submit_result.get("status_runtime"),
                    "memory": submit_result.get("status_memory"),
                }

                if submit_result.get("status_msg") == "Accepted":
                    result["status"] = "success"
                    self.save_solution(full_problem, code)
                    break
                else:
                    last_error = self._extract_submit_error(submit_result)
                    test_cases = self._add_failed_case(submit_result, test_cases)
                    analysis = self._handle_failure(
                        full_problem, analysis, last_error, code,
                        question_id, result["date"], problem_info.get("titleSlug", ""), attempt,
                    )

        except Exception as e:
            logger.error(f"Error: {e}")
            result["error"] = str(e)

        logger.info("=" * 50)
        logger.info(f"Result: {result['status']}")
        logger.info(f"Attempts: {result['attempts']}")
        logger.info("=" * 50)

        return result

    # ========== 辅助方法 ==========

    def load_analysis(self, question_id: int, title_slug: str) -> str | None:
        """从文件加载分析。"""
        if not self.storage:
            return None
        problem_dir = self.storage._get_problem_dir(question_id, title_slug)
        file_path = problem_dir / "analysis.md"
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            # 去掉 markdown header
            if "---" in content:
                parts = content.split("---", 1)
                if len(parts) > 1:
                    return parts[1].strip()
            return content
        return None

    def load_test_cases(self, question_id: int, title_slug: str) -> list[dict] | None:
        """从文件加载测试用例。"""
        if not self.storage:
            return None
        return self.storage.load_test_cases(question_id, title_slug)

    def _handle_failure(
        self,
        full_problem: dict,
        analysis: str,
        error: str,
        code: str,
        question_id: int,
        date: str,
        title_slug: str,
        attempt: int,
    ) -> str:
        """修复环节 Step A：基于错误信息让 AI 重新分析。"""
        if attempt >= self.config.max_retries:
            logger.error("Max retries reached, skip re-analyze")
            return analysis

        logger.info("[Fix Step A] Re-analyzing based on error...")
        new_analysis = self.ai.fix_analysis(full_problem, analysis, error, code)

        if self.storage:
            self.storage.save_analysis(
                question_id=question_id,
                date=date,
                title_slug=title_slug,
                analysis=new_analysis,
            )
        return new_analysis

    def _extract_error(self, result: dict) -> str:
        """Extract error message from run_code result."""
        if result.get("compile_error"):
            return f"Compile error: {result['compile_error']}"
        if result.get("runtime_error"):
            return f"Runtime error: {result['runtime_error']}"
        if result.get("last_testcase"):
            return f"Wrong answer on: {result['last_testcase']}"
        return f"State: {result.get('state', 'unknown')}"

    def _extract_submit_error(self, result: dict) -> str:
        """Extract detailed error from submit result."""
        status = result.get("status_msg", "Unknown")
        parts = [f"Status: {status}"]

        if result.get("input"):
            parts.append(f"Input: {result['input']}")
        if result.get("expected_output"):
            parts.append(f"Expected: {result['expected_output']}")
        if result.get("code_output"):
            parts.append(f"Actual: {result['code_output']}")
        if result.get("last_testcase"):
            parts.append(f"Last testcase: {result['last_testcase']}")
        if result.get("runtime_error"):
            parts.append(f"Runtime error: {result['runtime_error']}")
        if result.get("compile_error"):
            parts.append(f"Compile error: {result['compile_error']}")

        return "\n".join(parts)

    def _add_failed_case(self, submit_result: dict, test_cases: list) -> list:
        """把提交失败的隐藏用例回填到本地用例集。"""
        if not submit_result.get("input") or not submit_result.get("expected_output"):
            return test_cases

        try:
            input_str = str(submit_result["input"]).strip()
            expected_str = str(submit_result["expected_output"]).strip()

            lines = [ln.strip() for ln in input_str.split("\n") if ln.strip()]
            args = []
            for ln in lines:
                if ln in ("true", "false"):
                    args.append(ln == "true")
                elif ln in ("null", "None"):
                    args.append(None)
                else:
                    try:
                        args.append(json.loads(ln))
                    except Exception:
                        args.append(ln)

            if expected_str in ("true", "false"):
                expected = expected_str == "true"
            elif expected_str in ("null", "None"):
                expected = None
            else:
                try:
                    expected = json.loads(expected_str)
                except Exception:
                    expected = expected_str

            new_case = {"args": args, "expected": expected, "source": "hidden"}
            test_cases.append(new_case)
            logger.info(f"Added hidden test case: input={args}, expected={expected}")
        except Exception as e:
            logger.debug(f"Failed to add hidden case: {e}")
        return test_cases
