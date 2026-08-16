"""LeetCode API client for fetching problems and submitting solutions."""

from __future__ import annotations

import json
from typing import Any

import httpx
from loguru import logger

from .config import LeetCodeConfig


class LeetCodeClient:
    """Async HTTP client for LeetCode API."""

    def __init__(self, config: LeetCodeConfig) -> None:
        self.config = config
        if config.site == "cn":
            self.base_url = "https://leetcode.cn"
            self.graphql_url = "https://leetcode.cn/graphql"
        else:
            self.base_url = "https://leetcode.com"
            self.graphql_url = "https://leetcode.com/graphql"

        self._client = httpx.AsyncClient(timeout=30.0)

    @property
    def headers(self) -> dict[str, str]:
        """Get default headers for authenticated requests."""
        headers = {
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
        }

        if self.config.session and self.config.csrf_token:
            cookie_parts = []
            if "LEETCODE_SESSION=" not in self.config.session:
                cookie_parts.append(f"LEETCODE_SESSION={self.config.session}")
            else:
                cookie_parts.append(self.config.session)

            if "csrftoken=" not in self.config.session:
                cookie_parts.append(f"csrftoken={self.config.csrf_token}")

            headers["Cookie"] = "; ".join(cookie_parts)
            headers["x-csrftoken"] = self.config.csrf_token

        return headers

    async def graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        logger.debug(f"GraphQL request: {query[:100]}...")

        response = await self._client.post(
            self.graphql_url,
            json=payload,
            headers=self.headers,
        )
        response.raise_for_status()

        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")

        return data.get("data", {})

    async def get_daily_challenge(self) -> dict[str, Any]:
        """Get today's daily challenge problem."""
        if self.config.site == "cn":
            query = """
            query questionOfToday {
                todayRecord {
                    date
                    question {
                        questionId
                        questionFrontendId
                        title
                        titleSlug
                        difficulty
                        acRate
                        topicTags {
                            name
                            slug
                        }
                    }
                }
            }
            """
            data = await self.graphql(query)
            today_list = data.get("todayRecord", [])
            today = today_list[0] if today_list else {}
            return {
                "date": today.get("date"),
                "problem": today.get("question"),
            }
        else:
            query = """
            query questionOfToday {
                activeDailyCodingChallengeQuestion {
                    date
                    link
                    question {
                        questionId
                        questionFrontendId
                        title
                        titleSlug
                        difficulty
                        acRate
                        topicTags {
                            name
                            slug
                        }
                    }
                }
            }
            """
            data = await self.graphql(query)
            challenge = data.get("activeDailyCodingChallengeQuestion", {})
            return {
                "date": challenge.get("date"),
                "problem": challenge.get("question"),
            }

    async def get_problem(self, title_slug: str) -> dict[str, Any]:
        """Get problem details."""
        query = """
        query problemDetail($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                questionId
                questionFrontendId
                title
                translatedTitle
                titleSlug
                content
                translatedContent
                difficulty
                acRate
                topicTags {
                    name
                    slug
                }
                hints
                codeSnippets {
                    lang
                    langSlug
                    code
                }
            }
        }
        """
        data = await self.graphql(query, {"titleSlug": title_slug})
        return data.get("question", {})

    async def run_code(
        self,
        title_slug: str,
        question_id: str,
        lang: str,
        typed_code: str,
        data_input: str = "",
    ) -> dict[str, Any]:
        """Run code against test cases."""
        url = f"{self.base_url}/problems/{title_slug}/interpret_solution/"
        payload = {
            "data_input": data_input,
            "lang": lang,
            "question_id": question_id,
            "typed_code": typed_code,
        }

        response = await self._client.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        start = response.json()

        # Poll for result
        interpret_id = start.get("interpret_id")
        check_url = f"{self.base_url}/submissions/detail/{interpret_id}/check/"

        for _ in range(60):  # Max 60 polls
            await asyncio.sleep(2)
            check_response = await self._client.get(check_url, headers=self.headers)
            check_data = check_response.json()

            if check_data.get("state") != "PENDING":
                return check_data

        return {"state": "TIMEOUT", "error": "Execution timed out"}

    async def submit_solution(
        self,
        title_slug: str,
        question_id: str,
        lang: str,
        typed_code: str,
    ) -> dict[str, Any]:
        """Submit code to LeetCode."""
        url = f"{self.base_url}/problems/{title_slug}/submit/"
        payload = {
            "lang": lang,
            "question_id": question_id,
            "typed_code": typed_code,
        }

        response = await self._client.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        start = response.json()

        # Poll for result
        submission_id = start.get("submission_id")
        check_url = f"{self.base_url}/submissions/detail/{submission_id}/check/"

        for _ in range(60):  # Max 60 polls
            await asyncio.sleep(2)
            check_response = await self._client.get(check_url, headers=self.headers)
            check_data = check_response.json()

            if check_data.get("state") != "PENDING":
                return check_data

        return {"state": "TIMEOUT", "error": "Submission timed out"}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


# Need asyncio for sleep
import asyncio
