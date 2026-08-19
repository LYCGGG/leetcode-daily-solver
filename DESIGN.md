# 项目设计文档

## 目录

- [项目概述](#项目概述)
- [项目结构](#项目结构)
- [核心模块](#核心模块)
- [流程图](#流程图)
- [时序图](#时序图)
- [数据流](#数据流)
- [设计决策](#设计决策)
- [已知问题](#已知问题)

---

## 项目概述

LeetCode Daily Solver 是一个基于 AI 的自动刷题工具，能够：

1. 自动获取 LeetCode 每日挑战或指定题目
2. 使用 AI 分析题目并生成解题思路
3. 生成代码并通过本地测试 + LeetCode 在线验证
4. 失败时自动修复并重试

### 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| HTTP 客户端 | httpx |
| AI SDK | openai |
| 配置 | PyYAML |
| 日志 | loguru |
| 测试 | pytest + pytest-asyncio |
| 构建 | hatchling |

---

## 项目结构

```
leetcode-daily-solver/
├── src/
│   └── leetcode_daily_solver/
│       ├── __init__.py
│       ├── cli.py              # CLI 入口
│       ├── config.py           # 配置管理
│       ├── solver.py           # 核心求解器
│       ├── ai_client.py        # AI 客户端
│       ├── leetcode_client.py  # LeetCode API 客户端
│       ├── local_tester.py     # 本地测试运行器
│       ├── test_builder.py     # 差分测试用例生成
│       └── storage.py          # 文件存储管理
├── tests/
│   ├── conftest.py             # pytest 配置
│   ├── unit/                   # 单元测试
│   │   ├── test_ai_client.py
│   │   ├── test_leetcode_client.py
│   │   └── test_storage.py
│   └── integration/            # 集成测试
│       ├── conftest.py         # 集成测试 fixtures
│       ├── test_flow_cases.py  # 用例生成流程测试
│       └── test_flow_full.py   # 完整流程测试
├── problems/                   # 题目保存目录
│   └── {id}_{title-slug}/
│       ├── problem.md
│       ├── analysis.md
│       ├── solution.py
│       └── test_cases.json
├── config.yaml                 # 配置文件
├── config.example.yaml         # 配置示例
├── pyproject.toml              # 项目配置
├── README.md                   # 英文文档
├── README.zh-CN.md             # 中文文档
└── DESIGN.md                   # 本文档
```

---

## 核心模块

### 1. CLI (`cli.py`)

命令行入口，支持两种模式：

- **完整流程**：`--run-once` 或定时执行
- **单步执行**：`--step {fetch|analyze|cases|code|test-local}`

```python
# 关键函数
async def run_step(step, title_slug, config)  # 单步执行
async def run_once(title_slug, step)           # 一次性执行
def run_scheduled()                            # 定时执行
```

### 2. Solver (`solver.py`)

核心求解器，将流程拆分为独立方法：

```python
class DailySolver:
    # 独立步骤方法
    async def fetch_problem(title_slug)        # 获取题目
    def generate_analysis(full_problem)        # 生成分析
    def generate_test_cases(full_problem)      # 生成测试用例
    def generate_code(full_problem, analysis)  # 生成代码
    def test_code_local(code, test_cases)      # 本地测试
    async def test_code_leetcode(...)          # LeetCode 测试
    async def submit_solution(...)             # 提交解答
    
    # 辅助方法
    def load_analysis(question_id, title_slug) # 加载已有分析
    def load_test_cases(question_id, title_slug) # 加载已有用例
    
    # 完整流程
    async def solve(title_slug)                # 运行完整流程
```

### 3. AI Client (`ai_client.py`)

封装 OpenAI API 调用，管理对话上下文：

```python
class AIClient:
    conversation: list[dict]  # 对话历史
    
    def analyze_problem(problem)      # 分析题目
    def generate_code(problem, analysis, language)  # 生成代码
    def fix_code(problem, code, error, language)    # 修复代码
    def fix_analysis(problem, analysis, error, code)  # 重新分析
    def build_testcases(problem, num_cases, language)  # 生成测试用例
```

**关键设计**：`generate_code` 会检查对话历史，如果为空则自动用 `analysis` 重建上下文。

### 4. LeetCode Client (`leetcode_client.py`)

封装 LeetCode GraphQL API：

```python
class LeetCodeClient:
    async def get_daily_challenge()    # 获取每日挑战
    async def get_problem(title_slug)  # 获取题目详情
    async def run_code(...)            # 运行代码测试
    async def submit_solution(...)     # 提交解答
```

### 5. Test Builder (`test_builder.py`)

差分测试用例生成器：

```python
class TestBuilder:
    def build(problem, language, num_cases) -> list[dict]
```

工作流程：
1. 让 AI 生成暴力解（brute_solve）
2. 让 AI 生成测试输入
3. 执行暴力解获取期望输出
4. 返回 `{args, expected, source}` 格式的用例

### 6. Storage (`storage.py`)

文件存储管理：

```python
class Storage:
    def save_problem(...)       # 保存题目
    def save_analysis(...)      # 保存分析
    def save_solution(...)      # 保存解答
    def save_test_cases(...)    # 保存测试用例
    def load_test_cases(...)    # 加载测试用例
```

---

## 流程图

### 主流程

```mermaid
flowchart TD
    A[开始] --> B{指定题目?}
    B -->|是| C[获取指定题目]
    B -->|否| D[获取每日挑战]
    C --> E[保存题目信息]
    D --> E
    E --> F[AI 分析题目]
    F --> G[保存分析 + 生成用例]
    G --> H[尝试次数 = 1]

    H --> I{尝试 <= 最大次数?}
    I -->|否| J[结束: 失败]
    I -->|是| K{第一次?}
    K -->|是| L[生成代码]
    K -->|否| M[修复代码]
    L --> N[本地测试 → LeetCode测试 → 提交]
    M --> N

    N --> O{结果}
    O -->|通过| P[保存解答]
    P --> Q[结束: 成功]
    O -->|失败| R[回填隐藏用例 + AI 重新分析]
    R --> S[尝试次数 + 1]
    S --> I
```

### 单步执行流程

```mermaid
flowchart LR
    subgraph fetch [fetch]
        F1[获取题目] --> F2[保存题目]
    end
    
    subgraph analyze [analyze]
        A1[加载题目] --> A2[AI 分析] --> A3[保存分析]
    end
    
    subgraph cases [cases]
        C1[加载题目] --> C2[解析官方用例]
        C2 --> C3[生成差分用例]
        C3 --> C4[保存用例]
    end
    
    subgraph code [code]
        D1[加载题目] --> D2[加载分析]
        D2 --> D3[生成代码]
    end
    
    subgraph test [test-local]
        T1[加载题目] --> T2[加载分析]
        T2 --> T3[加载用例]
        T3 --> T4[生成代码]
        T4 --> T5[本地测试]
    end
```

---

## 时序图

### 完整流程时序图

```mermaid
sequenceDiagram
    participant User as 用户
    participant CLI as CLI
    participant Solver as Solver
    participant LC as LeetCodeClient
    participant AI as AIClient
    participant TB as TestBuilder
    participant Storage as Storage
    
    User->>CLI: leetcode-daily --run-once
    CLI->>Solver: solve(title_slug)
    
    rect rgb(200, 220, 240)
        Note over Solver,LC: Step 1: 获取题目
        Solver->>LC: get_problem(title_slug)
        LC-->>Solver: full_problem
        Solver->>Storage: save_problem()
    end
    
    rect rgb(200, 240, 220)
        Note over Solver,AI: Step 2: AI 分析
        Solver->>AI: analyze_problem(problem)
        AI-->>Solver: analysis
        Solver->>Storage: save_analysis()
    end
    
    rect rgb(240, 220, 200)
        Note over Solver,TB: Step 3: 生成用例
        Solver->>TB: build(problem, language, n)
        TB->>AI: build_testcases()
        AI-->>TB: brute_code + test_inputs
        TB-->>Solver: test_cases
        Solver->>Storage: save_test_cases()
    end
    
    rect rgb(240, 200, 240)
        Note over Solver,AI: Step 4-6: 生成、测试、提交
        loop 重试循环（最多5次）
            Solver->>AI: generate_code / fix_code
            AI-->>Solver: code

            Solver->>Solver: 本地测试
            Solver->>LC: LeetCode 测试
            LC-->>Solver: test_result

            alt 任一环节失败
                Solver->>Solver: 回填隐藏用例（提交失败时）
                Solver->>AI: fix_analysis(error, code)
                AI-->>Solver: new_analysis
            else 全部通过
                Solver->>LC: submit_solution(code)
                LC-->>Solver: submit_result
                Solver->>Storage: save_solution()
            end
        end
    end
    
    Solver-->>CLI: result
    CLI-->>User: 输出结果
```

### 单步执行时序图

```mermaid
sequenceDiagram
    participant User as 用户
    participant CLI as CLI
    participant Solver as Solver
    participant AI as AIClient
    participant Storage as Storage
    
    User->>CLI: --step code --problem two-sum
    CLI->>Solver: fetch_problem(title_slug)
    Solver-->>CLI: full_problem
    
    CLI->>Solver: load_analysis(id, slug)
    Solver->>Storage: load file
    Storage-->>Solver: analysis
    
    CLI->>Solver: generate_code(problem, analysis)
    
    rect rgb(240, 220, 200)
        Note over Solver,AI: 重建上下文
        Solver->>AI: conversation 为空?
        AI-->>Solver: 是
        Solver->>AI: 用 analysis 构建对话历史
    end
    
    Solver->>AI: generate_code()
    AI-->>Solver: code
    Solver-->>CLI: code
    CLI-->>User: 输出代码
```

---

## 数据流

### 测试用例格式

```mermaid
flowchart LR
    subgraph 官方用例
        O1[LeetCode API] --> O2[exampleTestcases]
        O2 --> O3[parse_test_cases]
        O3 --> O4["{args, expected: null, source: official}"]
    end
    
    subgraph 生成用例
        G1[AI 生成暴力解] --> G2[AI 生成输入]
        G2 --> G3[执行暴力解]
        G3 --> G4["{args, expected, source: generated}"]
    end
    
    subgraph 隐藏用例
        H1[提交失败] --> H2[提取 input/expected]
        H2 --> H3["{args, expected, source: hidden}"]
    end
    
    O4 --> Merge[合并]
    G4 --> Merge
    H3 --> Merge
    Merge --> Save[test_cases.json]
```

### 上下文传递

```mermaid
flowchart TD
    subgraph 完整流程
        A1[analyze_problem] -->|conversation| A2[generate_code]
        A2 -->|conversation| A3[fix_code]
        A3 -->|conversation| A4[fix_analysis]
    end
    
    subgraph 单步运行
        B1[load_analysis] -->|analysis 文本| B2[generate_code]
        B2 -->|重建 conversation| B3[AI 调用]
    end
```

---

## 设计决策

### 1. 可降级设计

TestBuilder 采用可降级策略：

```
生成暴力解失败 → 退回官方用例
解析输出失败 → 退回官方用例
执行暴力解失败 → 跳过该用例
```

**原因**：差分测试是增强功能，不应阻塞主流程。

### 2. 上下文保持

AI 对话上下文在完整流程中保持连续：

```
analyze → generate_code → fix_code → fix_analysis
         (共享 conversation)
```

单步运行时通过 `load_analysis` + 自动重建解决。

### 3. 统一用例格式

所有测试用例统一为 `{args, expected, source}` 格式：

- `official`：官方用例，expected 为 null
- `generated`：AI 生成用例，expected 由暴力解计算
- `hidden`：提交失败回填的隐藏用例

### 4. 单步执行支持

Solver 拆分为独立方法，支持：

- 单独调试某个步骤
- 从任意步骤开始执行
- 复用已有结果（如加载已有分析）

---

## 已知问题

| # | 问题 | 位置 | 状态 |
|---|------|------|------|
| 1 | MiMo API 使用 `max_completion_tokens` 而非 `max_tokens` | `ai_client.py:30` | 已适配 |
| 2 | `__replace__` 在 Python 3.13+ 才可用 | `cli.py:155` | 已用 `dataclasses.replace()` |
| 3 | TestBuilder AI 输出偶尔格式不规范 | `test_builder.py:26` | 可降级，考虑增加重试 |
| 4 | pytest-asyncio teardown 事件循环关闭报错 | 测试框架 | 已知问题，不影响结果 |
| 5 | Cookie 字段检查 bug | `leetcode_client.py:44` | ✅ 已修复 |
| 6 | HTTP 客户端未关闭导致资源泄漏 | `solver.py`, `cli.py` | ✅ 已修复 |
| 7 | eval()/exec() 安全风险 | `local_tester.py`, `test_builder.py` | 个人项目，暂不处理 |

---

## 扩展点

### 添加新 AI 提供商

在 `ai_client.py` 中扩展 `_call_api` 方法。

### 添加新题目来源

在 `leetcode_client.py` 中实现新的 API 客户端。

### 自定义测试用例

在 `test_builder.py` 中扩展 `build` 方法，支持手动输入用例。

---

*文档最后更新：2026-08-17*
