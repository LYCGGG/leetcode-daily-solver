"""Integration test: flow up to test case generation."""

import pytest
from leetcode_daily_solver.local_tester import parse_test_cases


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestFlowCases:
    """Test flow up to test case generation."""

    async def test_fetch_problem(self, problem_2958):
        """Test fetching problem details."""
        assert problem_2958 is not None
        assert problem_2958.get("questionFrontendId") == "2958"
        assert "Length of Longest Subarray" in problem_2958.get("title", "")
        print(f"[OK] Fetched: {problem_2958.get('title')}")

    async def test_parse_official_cases(self, problem_2958, config):
        """Test parsing official test cases."""
        example_testcases = problem_2958.get("exampleTestcases", "")
        cases = parse_test_cases(
            example_testcases,
            problem_2958.get("codeSnippets", []),
            config.language,
        )
        assert len(cases) == 3
        assert all(c["source"] == "official" for c in cases)
        assert all(c["expected"] is None for c in cases)
        assert all("args" in c for c in cases)
        print(f"[OK] Parsed {len(cases)} official cases")

    async def test_generate_cases(self, problem_2958, test_builder, config):
        """Test generating differential test cases."""
        cases = test_builder.build(problem_2958, config.language, 3)
        if cases:
            assert len(cases) <= 3
            assert all(c["source"] == "generated" for c in cases)
            assert all("args" in c and "expected" in c for c in cases)
            print(f"[OK] Generated {len(cases)} cases")
        else:
            print("[SKIP] Test builder returned empty (degraded)")

    async def test_save_and_load_cases(self, problem_2958, test_builder, storage, config):
        """Test saving and loading unified test cases."""
        question_id = int(problem_2958.get("questionFrontendId", 0))
        title_slug = "length-of-longest-subarray-with-at-most-k-frequency"

        official_cases = parse_test_cases(
            problem_2958.get("exampleTestcases", ""),
            problem_2958.get("codeSnippets", []),
            config.language,
        )

        generated_cases = test_builder.build(problem_2958, config.language, 3)

        all_cases = official_cases + generated_cases
        storage.save_test_cases(question_id, title_slug, all_cases)

        loaded = storage.load_test_cases(question_id, title_slug)
        assert loaded is not None
        assert len(loaded) == len(all_cases)
        print(f"[OK] Saved and loaded {len(loaded)} cases")
