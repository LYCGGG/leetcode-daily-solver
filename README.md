# LeetCode Daily Solver

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Automated LeetCode daily challenge solver using AI.

English | [中文](README.zh-CN.md)

## Features

- 🤖 **AI-Powered** - Uses AI to analyze and solve problems
- 🔄 **Auto Retry** - Automatically fixes code based on test failures
- ⏰ **Scheduled Execution** - Run daily at specified time
- 📝 **Multiple Languages** - Support Python, Java, C++, etc.
- 📊 **Logging** - Detailed execution logs
- 💾 **Save Problems** - Save problems, analysis and solutions to files
- 🇨🇳 **Chinese Support** - Fetch Chinese problem descriptions

## How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 1. Fetch    │ ──> │ 2. AI       │ ──> │ 3. Generate │
│ Daily       │     │ Analyze     │     │ Code        │
└─────────────┘     └─────────────┘     └─────────────┘
                                            │
┌─────────────┐     ┌─────────────┐         │
│ 6. Submit   │ <── │ 5. Fix      │ <── ┌───▼───────┐
│ Solution    │     │ Code        │     │ 4. Test   │
└─────────────┘     └─────────────┘     └───────────┘
```

## Quick Start

### 1. Install

```bash
git clone https://github.com/LYCGGG/leetcode-daily-solver.git
cd leetcode-daily-solver
pip install -e .
```

### 2. Configure

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`:

```yaml
ai:
  provider: openai
  model: mimo-v2.5-pro
  api_key: "your-api-key"
  base_url: "https://api.example.com/v1"

leetcode:
  site: cn
  session: "your-session-cookie"
  csrf_token: "your-csrf-token"

# Storage
save_problems: true
problems_dir: "problems"
```

Or use environment variables:

```bash
export OPENAI_API_KEY="your-api-key"
export LEETCODE_SESSION="your-session"
export LEETCODE_CSRF="your-csrf"
```

### 3. Run

```bash
# Run once
leetcode-daily --run-once

# Run on schedule (daily at 08:00)
leetcode-daily

# Run with different language
leetcode-daily --run-once --language java

# Verbose output
leetcode-daily --run-once -v
```

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `ai.provider` | AI provider (openai/claude) | openai |
| `ai.model` | Model name | qwen3.8-max-preview |
| `ai.api_key` | API key | - |
| `ai.base_url` | Custom API endpoint | - |
| `leetcode.site` | LeetCode site (cn/global) | cn |
| `leetcode.session` | Session cookie | - |
| `leetcode.csrf_token` | CSRF token | - |
| `schedule.time` | Daily run time | 08:00 |
| `language` | Programming language | python3 |
| `max_retries` | Max code generation retries | 5 |
| `save_problems` | Save problems to files | true |
| `problems_dir` | Directory to save problems | problems |
| `num_generated_cases` | Number of generated test cases | 5 |

## Output Structure

```
problems/
  0001_two-sum/
    problem.md      # Problem description (Chinese)
    analysis.md     # AI analysis
    solution.py     # Solution code
  0015_3sum/
    problem.md
    analysis.md
    solution.java
```

## Example Output

```
11:30:00 | INFO    | ==================================================
11:30:00 | INFO    | Starting Daily Challenge Solver
11:30:00 | INFO    | ==================================================
11:30:01 | INFO    | Step 1: Fetching daily challenge...
11:30:01 | INFO    | Problem: Two Sum (EASY)
11:30:02 | INFO    | Step 2: Fetching problem details...
11:30:03 | INFO    | Step 3: Analyzing problem with AI...
11:30:08 | INFO    | Step 4: Generating code (attempt 1)...
11:30:15 | INFO    | Step 5: Testing code...
11:30:20 | INFO    | ✓ Code accepted!
11:30:21 | INFO    | Step 6: Submitting solution...
11:30:25 | INFO    | ✓ Solution accepted!
11:30:25 | INFO    | ==================================================
11:30:25 | INFO    | Result: success
11:30:25 | INFO    | ==================================================
```

## License

MIT
