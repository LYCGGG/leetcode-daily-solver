# TODO

## 已知问题

| # | 问题 | 位置 | 优先级 | 状态 |
|---|------|------|--------|------|
| 1 | MiMo API 使用 `max_completion_tokens` 而非 `max_tokens`，其他模型可能需改回 | `ai_client.py:30` | 中 | 待确认 |
| 2 | `__replace__` 在 Python 3.13+ 才可用，3.12 及以下需用 `dataclasses.replace()` | `cli.py:155` | 低 | 待确认设备 |
| 3 | TestBuilder AI 输出偶尔格式不规范导致解析失败，考虑增加重试或放宽解析规则 | `test_builder.py:26` | 中 | 可降级 |
| 4 | pytest-asyncio teardown 事件循环关闭报错 | 测试框架 | 低 | 已知问题 |
| 5 | Cookie 字段检查 bug（已修复） | `leetcode_client.py:44` | - | ✅ 已修复 |
| 6 | HTTP 客户端未关闭导致资源泄漏（已修复） | `solver.py`, `cli.py` | - | ✅ 已修复 |
| 7 | eval()/exec() 执行 AI 代码有安全风险 | `local_tester.py`, `test_builder.py` | 低 | 个人项目暂不处理 |
| 8 | LeetCode session 会过期（IP 变化等），提交时 403 | `config.yaml` | 中 | 需手动更新 |

## 待优化

| # | 问题 | 优先级 | 说明 |
|---|------|--------|------|
| 1 | 对话上下文无限增长 | 中 | 重试 5 次后可能超限 |
| 2 | 本地测试只支持 Python | 中 | `--language java` 等无法本地测试 |
| 3 | 无类型检查 (mypy) | 低 | 添加 pyright/mypy 配置 |
| 4 | 无 ruff 配置 | 低 | 添加 linting 规则 |
| 5 | 无 API 重试/退避机制 | 低 | 添加 tenacity 重试 |
| 6 | 无 CI/CD 配置 | 低 | 添加 GitHub Actions |

## 待确认

| # | 问题 | 说明 |
|---|------|------|
| 1 | MiMo API `max_completion_tokens` | 在其他 OpenAI 兼容模型上测试是否需要改回 `max_tokens` |
| 2 | Python 3.13 `__replace__` | 在 Python 3.13+ 设备上确认是否可用 |

---

*最后更新：2026-08-19*
