"""Tests for storage module."""

import pytest
import tempfile
from pathlib import Path
from leetcode_daily_solver.storage import Storage


@pytest.fixture
def storage():
    """Create storage for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Storage(tmpdir)


def test_save_problem(storage):
    """Test saving problem."""
    path = storage.save_problem(
        question_id=1,
        date="2024-01-15",
        title="Two Sum",
        title_slug="two-sum",
        difficulty="Easy",
        tags=["Array", "Hash Table"],
        content="<p>Given an array...</p>",
    )
    assert path.exists()
    assert path.name == "problem.md"
    assert "0001_two-sum" in str(path)
    print(f"[OK] Problem saved to {path}")


def test_save_analysis(storage):
    """Test saving analysis."""
    path = storage.save_analysis(
        question_id=1,
        date="2024-01-15",
        title_slug="two-sum",
        analysis="Use hash table...",
    )
    assert path.exists()
    assert path.name == "analysis.md"
    print(f"[OK] Analysis saved to {path}")


def test_save_solution(storage):
    """Test saving solution."""
    path = storage.save_solution(
        question_id=1,
        date="2024-01-15",
        title_slug="two-sum",
        code="def twoSum(nums, target):\n    pass",
        language="python3",
    )
    assert path.exists()
    assert path.name == "solution.py"
    print(f"[OK] Solution saved to {path}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
