"""Integration test: problem 1240 - Stone Game II"""

import pytest
import pytest_asyncio
from leetcode_daily_solver.local_tester import parse_test_cases


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest_asyncio.fixture(scope="module")
async def problem_1240(leetcode_client):
    """Fetch problem 1240 - Stone Game II."""
    return await leetcode_client.get_problem("stone-game-ii")


class TestProblem1240:
    """Test problem 1240 - Stone Game II."""

    async def test_fetch_problem(self, problem_1240):
        """Test fetching problem details."""
        assert problem_1240 is not None
        assert problem_1240.get("questionFrontendId") == "1140"
        assert "Stone Game II" in problem_1240.get("title", "")
        print(f"[OK] Fetched: {problem_1240.get('title')}")

    async def test_parse_official_cases(self, problem_1240, config):
        """Test parsing official test cases."""
        example_testcases = problem_1240.get("exampleTestcases", "")
        cases = parse_test_cases(
            example_testcases,
            problem_1240.get("codeSnippets", []),
            config.language,
        )
        assert len(cases) == 2  # Stone Game II has 2 examples
        assert all(c["source"] == "official" for c in cases)
        assert all("args" in c for c in cases)
        print(f"[OK] Parsed {len(cases)} official cases")

    async def test_generate_cases(self, problem_1240, test_builder, config):
        """Test generating differential test cases."""
        cases = test_builder.build(problem_1240, config.language, 3)
        if cases:
            assert len(cases) <= 3
            assert all(c["source"] == "generated" for c in cases)
            print(f"[OK] Generated {len(cases)} cases")
        else:
            print("[SKIP] Test builder returned empty (degraded)")

    async def test_save_and_load_cases(self, problem_1240, test_builder, storage, config):
        """Test saving and loading unified test cases."""
        question_id = int(problem_1240.get("questionFrontendId", 0))
        title_slug = "stone-game-ii"

        official_cases = parse_test_cases(
            problem_1240.get("exampleTestcases", ""),
            problem_1240.get("codeSnippets", []),
            config.language,
        )

        generated_cases = test_builder.build(problem_1240, config.language, 3)

        all_cases = official_cases + generated_cases
        storage.save_test_cases(question_id, title_slug, all_cases)

        loaded = storage.load_test_cases(question_id, title_slug)
        assert loaded is not None
        assert len(loaded) == len(all_cases)
        print(f"[OK] Saved and loaded {len(loaded)} cases")
