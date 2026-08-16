"""Core pipeline for solving daily challenges."""

from __future__ import annotations

import json
from datetime import datetime

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

    async def solve(self) -> dict:
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
            # Step 1: Get daily challenge
            logger.info("Step 1: Fetching daily challenge...")
            challenge = await self.leetcode.get_daily_challenge()
            problem = challenge.get("problem", {})
            question_id = int(problem.get("questionFrontendId", 0))
            result["problem"] = {
                "question_id": question_id,
                "title": problem.get("title"),
                "difficulty": problem.get("difficulty"),
                "title_slug": problem.get("titleSlug"),
            }
            logger.info(f"Problem: {question_id}. {problem.get('title')} ({problem.get('difficulty')})")

            # Step 2: Get full problem details
            logger.info("Step 2: Fetching problem details...")
            full_problem = await self.leetcode.get_problem(problem.get("titleSlug"))

            # Save problem info
            if self.storage:
                tags = [tag.get("name", "") for tag in full_problem.get("topicTags", [])]
                title = full_problem.get("translatedTitle", "") or problem.get("title", "")
                content = full_problem.get("translatedContent", "") or full_problem.get("content", "")
                self.storage.save_problem(
                    question_id=question_id,
                    date=result["date"],
                    title=title,
                    title_slug=problem.get("titleSlug", ""),
                    difficulty=problem.get("difficulty", ""),
                    tags=tags,
                    content=content,
                )
                
                # Save test cases
                example_testcases = full_problem.get("exampleTestcases", "")
                if example_testcases:
                    self.storage.save_test_cases(
                        question_id=question_id,
                        title_slug=problem.get("titleSlug", ""),
                        test_cases=example_testcases,
                    )

            # Step 3: AI analysis
            logger.info("Step 3: Analyzing problem with AI...")
            analysis = self.ai.analyze_problem(full_problem)
            logger.info(f"Analysis:\n{analysis[:500]}...")

            # Save analysis
            if self.storage:
                self.storage.save_analysis(
                    question_id=question_id,
                    date=result["date"],
                    title_slug=problem.get("titleSlug", ""),
                    analysis=analysis,
                )

            # Load test cases for local testing
            test_cases_str = None
            if self.storage:
                test_cases_str = self.storage.load_test_cases(
                    question_id=question_id,
                    title_slug=problem.get("titleSlug", ""),
                )
            if not test_cases_str:
                test_cases_str = full_problem.get("exampleTestcases", "")
            
            test_cases = parse_test_cases(
                test_cases_str,
                full_problem.get("codeSnippets", []),
                self.config.language,
            )

            # 差分测试补充用例（可降级：失败则只用官方用例）
            if self.config.num_generated_cases > 0:
                generated_cases = self.test_builder.build(
                    full_problem, self.config.language, self.config.num_generated_cases,
                )
                if generated_cases:
                    test_cases = test_cases + generated_cases
                    logger.info(f"已补充 {len(generated_cases)} 个差分测试用例，共 {len(test_cases)} 个")
                else:
                    logger.info("未生成分差用例，仅使用官方用例")

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
                    logger.info("Step 4: Generating code...")
                    code = self.ai.generate_code(full_problem, analysis, self.config.language)
                else:
                    # 修复环节 Step B：基于上一轮更新后的分析修复代码
                    logger.info(f"[Fix Step B] 基于更新后的分析修复代码，错误: {last_error}")
                    code = self.ai.fix_code(full_problem, code, last_error, self.config.language)

                logger.info(f"Generated code:\n{code[:500]}...")

                # Step 4.5: Local test
                logger.info("Step 4.5: Running local test...")
                if test_cases:
                    local_result = run_local_test(code, test_cases)
                    if not local_result["success"]:
                        last_error = local_result.get("error", "Local test failed")
                        logger.warning(f"✗ Local test failed: {last_error}")
                        analysis = self._handle_failure(
                            full_problem, analysis, last_error, code,
                            question_id, result["date"], problem.get("titleSlug", ""), attempt,
                        )
                        continue
                    else:
                        logger.info("✓ Local test passed!")
                else:
                    logger.warning("No test cases available for local testing")

                # Step 5: Test code on LeetCode
                logger.info("Step 5: Testing code on LeetCode...")
                test_result = await self.leetcode.run_code(
                    title_slug=problem["titleSlug"],
                    question_id=str(problem.get("questionId", "")),
                    lang=self.config.language,
                    typed_code=code,
                )

                test_state = test_result.get("state", "")
                test_accepted = test_result.get("status_msg") == "Accepted" or test_result.get("accepted")

                if test_state in ("FINISHED", "SUCCESS") and test_accepted:
                    logger.info("✓ Code accepted on LeetCode!")
                else:
                    last_error = self._extract_error(test_result)
                    logger.warning(f"✗ LeetCode test failed: {last_error}")
                    analysis = self._handle_failure(
                        full_problem, analysis, last_error, code,
                        question_id, result["date"], problem.get("titleSlug", ""), attempt,
                    )
                    continue

                # Step 6: Submit solution
                logger.info("Step 6: Submitting solution...")
                submit_result = await self.leetcode.submit_solution(
                    title_slug=problem["titleSlug"],
                    question_id=str(problem.get("questionId", "")),
                    lang=self.config.language,
                    typed_code=code,
                )
                
                result["submit_result"] = {
                    "status": submit_result.get("status_msg"),
                    "runtime": submit_result.get("status_runtime"),
                    "memory": submit_result.get("status_memory"),
                }
                logger.debug(f"Submit response keys: {list(submit_result.keys())}")

                if submit_result.get("status_msg") == "Accepted":
                    result["status"] = "success"
                    logger.info("✓ Solution accepted!")
                    
                    # Save final solution
                    if self.storage and code:
                        self.storage.save_solution(
                            question_id=question_id,
                            date=result["date"],
                            title_slug=problem.get("titleSlug", ""),
                            code=code,
                            language=self.config.language,
                        )
                    break
                else:
                    # Build detailed error message from submission result
                    last_error = self._extract_submit_error(submit_result)
                    logger.warning(f"✗ {last_error}")
                    analysis = self._handle_failure(
                        full_problem, analysis, last_error, code,
                        question_id, result["date"], problem.get("titleSlug", ""), attempt,
                    )

        except Exception as e:
            logger.error(f"Error: {e}")
            result["error"] = str(e)

        logger.info("=" * 50)
        logger.info(f"Result: {result['status']}")
        logger.info(f"Attempts: {result['attempts']}")
        logger.info("=" * 50)

        return result

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
        """修复环节 Step A：基于「错误信息 + 当前代码」让 AI 重新分析并保存。

        Returns:
            更新后的分析文本。若无下一轮尝试则原样返回旧分析。
        """
        # 若已是最后一轮，无需重新分析（不会有下一次 fix_code）
        if attempt >= self.config.max_retries:
            logger.error("Max retries reached, skip re-analyze")
            return analysis

        logger.info("[Fix Step A] 基于错误信息和当前代码，让 AI 重新分析...")
        new_analysis = self.ai.fix_analysis(full_problem, analysis, error, code)

        # 保存更新后的分析
        if self.storage:
            self.storage.save_analysis(
                question_id=question_id,
                date=date,
                title_slug=title_slug,
                analysis=new_analysis,
            )
        logger.info("[Fix Step B] 下一轮将基于新分析调用 fix_code 修复代码...")
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
