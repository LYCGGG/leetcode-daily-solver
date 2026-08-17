"""Integration tests for LeetCode client module."""

import pytest
import pytest_asyncio
from leetcode_daily_solver.config import load_config
from leetcode_daily_solver.leetcode_client import LeetCodeClient


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest_asyncio.fixture
async def leetcode_client():
    """Create LeetCode client for testing."""
    config = load_config()
    client = LeetCodeClient(config.leetcode)
    yield client
    await client.close()


async def test_get_daily_challenge(leetcode_client):
    """Test fetching daily challenge."""
    challenge = await leetcode_client.get_daily_challenge()
    assert "date" in challenge
    assert "problem" in challenge
    problem = challenge.get("problem", {})
    assert "title" in problem
    assert "titleSlug" in problem
    print(f"[OK] Daily challenge: {problem.get('title')}")


async def test_get_problem(leetcode_client):
    """Test fetching problem details."""
    problem = await leetcode_client.get_problem("two-sum")
    assert "title" in problem
    assert "content" in problem
    assert "difficulty" in problem
    print(f"[OK] Problem: {problem.get('title')}")
