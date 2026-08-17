"""Integration test: full solve flow."""

import pytest
import asyncio
from leetcode_daily_solver.solver import DailySolver


pytestmark = pytest.mark.integration


class TestFlowFull:
    """Test full solve flow."""

    def test_solve_specific_problem(self, config):
        """Test solving a specific problem (easy one)."""
        solver = DailySolver(config)
        result = asyncio.run(solver.solve(title_slug="two-sum"))

        assert result is not None
        assert result["status"] == "success"
        assert result["attempts"] >= 1
        assert result["problem"]["title_slug"] == "two-sum"
        print(f"[OK] Solved in {result['attempts']} attempt(s)")

    def test_solve_with_custom_storage(self, config, tmp_path):
        """Test solving with custom storage directory."""
        from dataclasses import replace
        custom_config = replace(config, problems_dir=str(tmp_path))

        solver = DailySolver(custom_config)
        result = asyncio.run(solver.solve(title_slug="two-sum"))

        assert result["status"] == "success"
        # Verify files were saved
        problem_dir = list(tmp_path.iterdir())[0]
        assert (problem_dir / "problem.md").exists()
        assert (problem_dir / "test_cases.json").exists()
        assert (problem_dir / "solution.py").exists()
        print(f"[OK] Files saved to {problem_dir}")
