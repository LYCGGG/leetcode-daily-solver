"""Storage module for saving problems and solutions to files."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from loguru import logger


# Language to file extension mapping
LANG_EXTENSIONS: dict[str, str] = {
    "python3": "py",
    "python": "py",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "csharp": "cs",
    "javascript": "js",
    "typescript": "ts",
    "go": "go",
    "rust": "rs",
    "kotlin": "kt",
    "swift": "swift",
    "ruby": "rb",
    "scala": "scala",
}


class Storage:
    """Handles saving problems and solutions to files."""

    def __init__(self, base_dir: Path | str = "problems") -> None:
        self.base_dir = Path(base_dir)

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as filename."""
        # Replace non-alphanumeric characters with hyphens
        sanitized = re.sub(r"[^\w\s-]", "", name.lower())
        sanitized = re.sub(r"[\s]+", "-", sanitized)
        return sanitized.strip("-")

    def _get_problem_dir(self, question_id: int, title_slug: str) -> Path:
        """Get the directory path for a problem."""
        dir_name = f"{question_id:04d}_{title_slug}"
        return self.base_dir / dir_name

    def _get_lang_extension(self, language: str) -> str:
        """Get file extension for a programming language."""
        return LANG_EXTENSIONS.get(language, language)

    def save_problem(
        self,
        question_id: int,
        date: str,
        title: str,
        title_slug: str,
        difficulty: str,
        tags: list[str],
        content: str,
    ) -> Path:
        """Save problem information to problem.md.

        Args:
            question_id: Problem number (e.g., 1, 15, 200)
            date: Date string (YYYY-MM-DD)
            title: Problem title
            title_slug: URL-friendly title
            difficulty: EASY/MEDIUM/HARD
            tags: List of topic tags
            content: Problem content (HTML or markdown)

        Returns:
            Path to the saved file
        """
        problem_dir = self._get_problem_dir(question_id, title_slug)
        problem_dir.mkdir(parents=True, exist_ok=True)

        # Build markdown content
        md_content = f"""# {title}

**Date:** {date}
**Difficulty:** {difficulty}
**Tags:** {', '.join(tags) if tags else 'N/A'}

---

{content}
"""
        file_path = problem_dir / "problem.md"
        file_path.write_text(md_content, encoding="utf-8")
        logger.info(f"Saved problem to {file_path}")
        return file_path

    def save_analysis(
        self,
        question_id: int,
        date: str,
        title_slug: str,
        analysis: str,
    ) -> Path:
        """Save AI analysis to analysis.md.

        Args:
            question_id: Problem number (e.g., 1, 15, 200)
            date: Date string (YYYY-MM-DD)
            title_slug: URL-friendly title
            analysis: AI-generated analysis text

        Returns:
            Path to the saved file
        """
        problem_dir = self._get_problem_dir(question_id, title_slug)
        problem_dir.mkdir(parents=True, exist_ok=True)

        md_content = f"""# AI Analysis

**Date:** {date}
**Problem:** {title_slug}

---

{analysis}
"""
        file_path = problem_dir / "analysis.md"
        file_path.write_text(md_content, encoding="utf-8")
        logger.info(f"Saved analysis to {file_path}")
        return file_path

    def save_solution(
        self,
        question_id: int,
        date: str,
        title_slug: str,
        code: str,
        language: str,
    ) -> Path:
        """Save solution code to a language-specific file.

        Args:
            question_id: Problem number (e.g., 1, 15, 200)
            date: Date string (YYYY-MM-DD)
            title_slug: URL-friendly title
            code: Solution code
            language: Programming language (e.g., python3, java, cpp)

        Returns:
            Path to the saved file
        """
        problem_dir = self._get_problem_dir(question_id, title_slug)
        problem_dir.mkdir(parents=True, exist_ok=True)

        ext = self._get_lang_extension(language)
        file_path = problem_dir / f"solution.{ext}"
        file_path.write_text(code, encoding="utf-8")
        logger.info(f"Saved solution to {file_path}")
        return file_path

    def save_test_cases(
        self,
        question_id: int,
        title_slug: str,
        test_cases: str,
    ) -> Path:
        """Save test cases to a JSON file.

        Args:
            question_id: Problem number (e.g., 1, 15, 200)
            title_slug: URL-friendly title
            test_cases: Raw test cases string from LeetCode

        Returns:
            Path to the saved file
        """
        problem_dir = self._get_problem_dir(question_id, title_slug)
        problem_dir.mkdir(parents=True, exist_ok=True)

        file_path = problem_dir / "test_cases.json"
        file_path.write_text(test_cases, encoding="utf-8")
        logger.info(f"Saved test cases to {file_path}")
        return file_path

    def load_test_cases(
        self,
        question_id: int,
        title_slug: str,
    ) -> str | None:
        """Load test cases from local file.

        Args:
            question_id: Problem number (e.g., 1, 15, 200)
            title_slug: URL-friendly title

        Returns:
            Test cases string or None if not found
        """
        problem_dir = self._get_problem_dir(question_id, title_slug)
        file_path = problem_dir / "test_cases.json"

        if file_path.exists():
            test_cases = file_path.read_text(encoding="utf-8")
            logger.info(f"Loaded test cases from {file_path}")
            return test_cases

        return None

    def save_all(
        self,
        question_id: int,
        date: str,
        title: str,
        title_slug: str,
        difficulty: str,
        tags: list[str],
        content: str,
        analysis: str,
        code: str,
        language: str,
    ) -> dict[str, Path]:
        """Save problem, analysis, and solution at once.

        Args:
            question_id: Problem number (e.g., 1, 15, 200)
            date: Date string (YYYY-MM-DD)
            title: Problem title
            title_slug: URL-friendly title
            difficulty: EASY/MEDIUM/HARD
            tags: List of topic tags
            content: Problem content (HTML or markdown)
            analysis: AI-generated analysis text
            code: Solution code
            language: Programming language (e.g., python3, java, cpp)

        Returns:
            Dictionary with keys 'problem', 'analysis', 'solution' and their paths
        """
        paths = {
            "problem": self.save_problem(question_id, date, title, title_slug, difficulty, tags, content),
            "analysis": self.save_analysis(question_id, date, title_slug, analysis),
            "solution": self.save_solution(question_id, date, title_slug, code, language),
        }
        logger.info(f"All files saved to {self._get_problem_dir(question_id, title_slug)}")
        return paths
