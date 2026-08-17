"""Tests for AI client module."""

import pytest
from leetcode_daily_solver.config import load_config
from leetcode_daily_solver.ai_client import AIClient


@pytest.fixture
def ai_client():
    """Create AI client for testing."""
    config = load_config()
    return AIClient(config.ai)


@pytest.fixture
def sample_problem():
    """Sample problem for testing."""
    return {
        "title": "Two Sum",
        "translatedTitle": "两数之和",
        "difficulty": "Easy",
        "topicTags": [
            {"name": "Array", "slug": "array"},
            {"name": "Hash Table", "slug": "hash-table"},
        ],
        "content": "<p>Given an array of integers...</p>",
        "translatedContent": "<p>给定一个整数数组...</p>",
    }


def test_analyze_problem(ai_client, sample_problem):
    """Test AI analysis generation."""
    analysis = ai_client.analyze_problem(sample_problem)
    assert len(analysis) > 0
    assert isinstance(analysis, str)
    print(f"[OK] Analysis length: {len(analysis)}")


def test_generate_code(ai_client, sample_problem):
    """Test code generation."""
    code = ai_client.generate_code(sample_problem, "", "python3")
    assert len(code) > 0
    assert isinstance(code, str)
    # Check if code contains Python syntax
    assert any(keyword in code for keyword in ["def ", "class ", "return"])
    print(f"[OK] Code length: {len(code)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
