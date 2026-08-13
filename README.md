# LeetCode Daily Solver

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Automated LeetCode daily challenge solver using AI.

## Features

- 🤖 **AI-Powered** - Uses GPT-4/Claude to analyze and solve problems
- 🔄 **Auto Retry** - Automatically fixes code based on test failures
- ⏰ **Scheduled Execution** - Run daily at specified time
- 📝 **Multiple Languages** - Support Python, Java, C++, etc.
- 📊 **Logging** - Detailed execution logs

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
  api_key: "your-openai-api-key"
  model: gpt-4o

leetcode:
  site: cn
  session: "your-session-cookie"
  csrf_token: "your-csrf-token"
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
| `ai.model` | Model name | gpt-4o |
| `ai.api_key` | API key | - |
| `leetcode.site` | LeetCode site (cn/global) | cn |
| `leetcode.session` | Session cookie | - |
| `leetcode.csrf_token` | CSRF token | - |
| `schedule.time` | Daily run time | 08:00 |
| `language` | Programming language | python3 |
| `max_retries` | Max code generation retries | 3 |

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
