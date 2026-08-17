"""Integration test fixtures."""

import pytest
import pytest_asyncio
from leetcode_daily_solver.config import load_config, Config
from leetcode_daily_solver.ai_client import AIClient
from leetcode_daily_solver.leetcode_client import LeetCodeClient
from leetcode_daily_solver.storage import Storage
from leetcode_daily_solver.test_builder import TestBuilder


@pytest.fixture(scope="session")
def config() -> Config:
    """Load config once per session."""
    return load_config()


@pytest.fixture(scope="session")
def ai_client(config) -> AIClient:
    """Create AI client once per session."""
    return AIClient(config.ai)


@pytest_asyncio.fixture(scope="session")
async def leetcode_client(config) -> LeetCodeClient:
    """Create LeetCode client once per session."""
    client = LeetCodeClient(config.leetcode)
    yield client
    await client.close()


@pytest.fixture(scope="session")
def test_builder(ai_client) -> TestBuilder:
    """Create test builder once per session."""
    return TestBuilder(ai_client)


@pytest_asyncio.fixture(scope="session")
async def problem_2958(leetcode_client):
    """Fetch problem 2958."""
    return await leetcode_client.get_problem("length-of-longest-subarray-with-at-most-k-frequency")


@pytest.fixture
def storage(tmp_path) -> Storage:
    """Create storage with temp directory per test."""
    return Storage(tmp_path)
