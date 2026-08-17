"""CLI entry point for leetcode-daily-solver."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import schedule
import time
from loguru import logger

from .config import load_config
from .solver import DailySolver


def setup_logging(level: str) -> None:
    """Configure loguru."""
    logger.remove()
    logger.add(sys.stderr, level=level, format="{time:HH:mm:ss} | {level:<7} | {message}")
    logger.add("logs/{time:YYYY-MM-DD}.log", rotation="1 day", retention="7 days")


async def run_step(step: str, title_slug: str, config) -> None:
    """Run a single step of the pipeline."""
    async with DailySolver(config) as solver:
        if step == "fetch":
            result = await solver.fetch_problem(title_slug)
            problem_info = result["problem_info"]
            full_problem = result["full_problem"]
            logger.info(f"Fetched: {problem_info.get('questionFrontendId')}. {problem_info.get('title')}")
            logger.info(f"Difficulty: {problem_info.get('difficulty')}")
            logger.info(f"Tags: {[t.get('name') for t in full_problem.get('topicTags', [])]}")
            return result

        elif step == "analyze":
            fetched = await solver.fetch_problem(title_slug)
            full_problem = fetched["full_problem"]
            analysis = solver.generate_analysis(full_problem)
            logger.info(f"Analysis saved ({len(analysis)} chars)")
            return analysis

        elif step == "cases":
            fetched = await solver.fetch_problem(title_slug)
            full_problem = fetched["full_problem"]
            test_cases = solver.generate_test_cases(full_problem)
            logger.info(f"Generated {len(test_cases)} test cases")
            return test_cases

        elif step == "code":
            fetched = await solver.fetch_problem(title_slug)
            full_problem = fetched["full_problem"]
            question_id = int(full_problem.get("questionFrontendId", 0))
            analysis = solver.load_analysis(question_id, title_slug)
            if not analysis:
                logger.info("No existing analysis, generating...")
                analysis = solver.generate_analysis(full_problem)
            code = solver.generate_code(full_problem, analysis)
            logger.info(f"Code generated ({len(code)} chars)")
            return code

        elif step == "test-local":
            fetched = await solver.fetch_problem(title_slug)
            full_problem = fetched["full_problem"]
            question_id = int(full_problem.get("questionFrontendId", 0))
            analysis = solver.load_analysis(question_id, title_slug)
            if not analysis:
                analysis = solver.generate_analysis(full_problem)
            test_cases = solver.load_test_cases(question_id, title_slug)
            if not test_cases:
                test_cases = solver.generate_test_cases(full_problem)
            code = solver.generate_code(full_problem, analysis)
            result = solver.test_code_local(code, test_cases)
            return result

        else:
            logger.error(f"Unknown step: {step}")
            return None


async def run_once(title_slug: str | None = None, step: str | None = None) -> None:
    """Run the solver once."""
    config = load_config()

    if step:
        if not title_slug:
            logger.error("--problem is required when using --step")
            return
        return await run_step(step, title_slug, config)
    else:
        async with DailySolver(config) as solver:
            result = await solver.solve(title_slug=title_slug)
            return result


def run_scheduled() -> None:
    """Run the solver on schedule."""
    config = load_config()
    setup_logging(config.log_level)

    logger.info(f"Scheduled to run daily at {config.schedule.time}")

    async def job():
        async with DailySolver(config) as solver:
            await solver.solve()

    def run_job():
        asyncio.run(job())

    schedule.every().day.at(config.schedule.time).do(run_job)

    # Run immediately on first start
    logger.info("Running immediately on start...")
    run_job()

    # Then wait for schedule
    while True:
        schedule.run_pending()
        time.sleep(60)


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="LeetCode Daily Challenge Solver")
    parser.add_argument("--config", "-c", type=Path, help="Config file path")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--language", "-l", default="python3", help="Programming language")
    parser.add_argument("--problem", "-p", type=str, default=None, help="Solve a specific problem by titleSlug")
    parser.add_argument("--step", "-s", type=str, default=None,
                        choices=["fetch", "analyze", "cases", "code", "test-local"],
                        help="Run a single step (requires --problem)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    config = load_config(args.config)
    setup_logging("DEBUG" if args.verbose else config.log_level)

    if args.language:
        # NOTE: __replace__ 在 Python 3.13+ 才可用，3.12 及以下需用 dataclasses.replace()
        from dataclasses import replace
        config = replace(config, language=args.language)

    if args.step or args.run_once:
        asyncio.run(run_once(title_slug=args.problem, step=args.step))
    else:
        run_scheduled()


if __name__ == "__main__":
    main()
