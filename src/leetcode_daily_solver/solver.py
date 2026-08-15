"""Core pipeline for solving daily challenges."""

from __future__ import annotations

import json
from datetime import datetime

from loguru import logger

from .ai_client import AIClient
from .config import Config
from .leetcode_client import LeetCodeClient
from .storage import Storage


class DailySolver:
    """Orchestrates the daily challenge solving pipeline."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.leetcode = LeetCodeClient(config.leetcode)
        self.ai = AIClient(config.ai)
        self.storage = Storage(config.problems_dir) if config.save_problems else None

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
                self.storage.save_problem(
                    question_id=question_id,
                    date=result["date"],
                    title=problem.get("title", ""),
                    title_slug=problem.get("titleSlug", ""),
                    difficulty=problem.get("difficulty", ""),
                    tags=tags,
                    content=full_problem.get("content", ""),
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

            # Step 4-6: Generate, test, fix (with retries)
            code = None
            for attempt in range(1, self.config.max_retries + 1):
                result["attempts"] = attempt
                logger.info(f"Step 4: Generating code (attempt {attempt})...")

                if attempt == 1:
                    code = self.ai.generate_code(full_problem, analysis, self.config.language)
                else:
                    # Use previous error for fixing
                    code = self.ai.fix_code(full_problem, code, last_error, self.config.language)

                logger.info(f"Generated code:\n{code[:500]}...")

                # Step 5: Test code
                logger.info("Step 5: Testing code...")
                test_result = await self.leetcode.run_code(
                    title_slug=problem["titleSlug"],
                    question_id=str(problem.get("questionId", "")),
                    lang=self.config.language,
                    typed_code=code,
                )

                if test_result.get("state") == "FINISHED" and test_result.get("accepted"):
                    logger.info("✓ Code accepted!")
                    break
                else:
                    last_error = self._extract_error(test_result)
                    logger.warning(f"✗ Test failed: {last_error}")
                    if attempt == self.config.max_retries:
                        logger.error("Max retries reached")

            # Step 6: Submit
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

            if submit_result.get("status_msg") == "Accepted":
                result["status"] = "success"
                logger.info("✓ Solution accepted!")

                # Save solution code
                if self.storage and code:
                    self.storage.save_solution(
                        question_id=question_id,
                        date=result["date"],
                        title_slug=problem.get("titleSlug", ""),
                        code=code,
                        language=self.config.language,
                    )
            else:
                logger.warning(f"✗ Submission: {submit_result.get('status_msg')}")

        except Exception as e:
            logger.error(f"Error: {e}")
            result["error"] = str(e)

        logger.info("=" * 50)
        logger.info(f"Result: {result['status']}")
        logger.info("=" * 50)

        return result

    def _extract_error(self, result: dict) -> str:
        """Extract error message from result."""
        if result.get("compile_error"):
            return f"Compile error: {result['compile_error']}"
        if result.get("runtime_error"):
            return f"Runtime error: {result['runtime_error']}"
        if result.get("last_testcase"):
            return f"Wrong answer on: {result['last_testcase']}"
        return f"State: {result.get('state', 'unknown')}"
