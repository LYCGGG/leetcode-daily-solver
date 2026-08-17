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


async def run_once(title_slug: str | None = None) -> None:
    """Run the solver once. title_slug 指定时跑指定题目，否则跑每日题。"""
    config = load_config()
    solver = DailySolver(config)
    result = await solver.solve(title_slug=title_slug)
    return result


def run_scheduled() -> None:
    """Run the solver on schedule."""
    config = load_config()
    setup_logging(config.log_level)

    logger.info(f"Scheduled to run daily at {config.schedule.time}")

    async def job():
        solver = DailySolver(config)
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
    parser.add_argument("--problem", "-p", type=str, default=None, help="Solve a specific problem by titleSlug (default: daily challenge)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    config = load_config(args.config)
    setup_logging("DEBUG" if args.verbose else config.log_level)

    if args.language:
        # NOTE: __replace__ 在 Python 3.13+ 才可用，3.12 及以下需用 dataclasses.replace()
        from dataclasses import replace
        config = replace(config, language=args.language)

    if args.run_once:
        asyncio.run(run_once(title_slug=args.problem))
    else:
        run_scheduled()


if __name__ == "__main__":
    main()
