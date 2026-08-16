"""Configuration management for leetcode-daily-solver."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class AIConfig:
    """AI model configuration."""
    provider: str = "openai"  # openai, claude, local
    model: str = "qwen3.8-max-preview"
    api_key: str = ""
    base_url: str | None = None


@dataclass(frozen=True)
class LeetCodeConfig:
    """LeetCode configuration."""
    site: str = "cn"  # cn, global
    session: str = ""
    csrf_token: str = ""


@dataclass(frozen=True)
class ScheduleConfig:
    """Schedule configuration."""
    enabled: bool = False
    time: str = "08:00"  # HH:MM format


@dataclass(frozen=True)
class Config:
    """Main configuration."""
    ai: AIConfig = field(default_factory=AIConfig)
    leetcode: LeetCodeConfig = field(default_factory=LeetCodeConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    language: str = "python3"
    max_retries: int = 5
    log_level: str = "INFO"
    save_problems: bool = True
    problems_dir: str = "problems"
    num_generated_cases: int = 10


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from YAML file and environment variables.
    
    Priority: environment variables > YAML file > defaults.
    """
    raw: dict = {}

    if config_path is None:
        config_path = Path.cwd() / "config.yaml"

    if config_path.is_file():
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                raw = data

    # Environment variable overrides
    if api_key := os.environ.get("OPENAI_API_KEY"):
        raw.setdefault("ai", {})["api_key"] = api_key
    if api_key := os.environ.get("ANTHROPIC_API_KEY"):
        raw.setdefault("ai", {})["api_key"] = api_key
        raw.setdefault("ai", {})["provider"] = "claude"
    if site := os.environ.get("LEETCODE_SITE"):
        raw.setdefault("leetcode", {})["site"] = site
    if session := os.environ.get("LEETCODE_SESSION"):
        raw.setdefault("leetcode", {})["session"] = session
    if csrf := os.environ.get("LEETCODE_CSRF"):
        raw.setdefault("leetcode", {})["csrf_token"] = csrf

    return Config(
        ai=AIConfig(
            provider=raw.get("ai", {}).get("provider", "openai"),
            model=raw.get("ai", {}).get("model", "qwen3.8-max-preview"),
            api_key=raw.get("ai", {}).get("api_key", ""),
            base_url=raw.get("ai", {}).get("base_url"),
        ),
        leetcode=LeetCodeConfig(
            site=raw.get("leetcode", {}).get("site", "cn"),
            session=raw.get("leetcode", {}).get("session", ""),
            csrf_token=raw.get("leetcode", {}).get("csrf_token", ""),
        ),
        schedule=ScheduleConfig(
            enabled=raw.get("schedule", {}).get("enabled", False),
            time=raw.get("schedule", {}).get("time", "08:00"),
        ),
        language=raw.get("language", "python3"),
        max_retries=raw.get("max_retries", 5),
        log_level=raw.get("log_level", "INFO"),
        save_problems=raw.get("save_problems", True),
        problems_dir=raw.get("problems_dir", "problems"),
        num_generated_cases=raw.get("num_generated_cases", 10),
    )
