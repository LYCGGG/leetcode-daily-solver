"""手动验证 TestBuilder 对当前每日题目生成差分用例的效果。(不属于自动化测试集)"""

import asyncio

from leetcode_daily_solver.ai_client import AIClient
from leetcode_daily_solver.config import load_config
from leetcode_daily_solver.leetcode_client import LeetCodeClient
from leetcode_daily_solver.test_builder import TestBuilder


async def main():
    config = load_config()
    client = LeetCodeClient(config.leetcode)
    ai = AIClient(config.ai)
    builder = TestBuilder(ai)

    challenge = await client.get_daily_challenge()
    problem = challenge.get("problem", {})
    title_slug = problem.get("titleSlug", "")
    full_problem = await client.get_problem(title_slug)

    print(f"Building test cases for: {title_slug}")
    cases = builder.build(full_problem, config.language, config.num_generated_cases)
    print(f"Generated {len(cases)} test cases")
    for c in cases:
        print(f"  args={c['args']}, expected={c['expected']}")


if __name__ == "__main__":
    asyncio.run(main())
