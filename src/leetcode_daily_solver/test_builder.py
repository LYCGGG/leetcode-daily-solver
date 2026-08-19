"""Test case builder using differential testing with a brute-force reference.

可降级设计：若暴力解生成或执行失败，返回空列表，调用方退回官方用例，不中断流程。
"""

from __future__ import annotations

import re
from typing import Any

from loguru import logger


class TestBuilder:
    """用暴力解做参照，为题目构造带期望输出的额外用例。"""

    def __init__(self, ai) -> None:
        self.ai = ai

    def build(self, problem: dict, language: str, num_cases: int = 10, max_retries: int = 3) -> list[dict[str, Any]]:
        """构造带期望输出的测试用例列表。失败返回空列表(可降级)。

        Returns:
            [ {"args": [...], "expected": <value>, "source": "generated"}, ... ]
        """
        # NOTE: AI 偶尔输出格式不规范导致解析失败，可降级退回官方用例。增加重试机制。
        for attempt in range(max_retries):
            try:
                result = self.ai.build_testcases(problem, num_cases, language)
                if not result:
                    logger.debug(f"TestBuilder: 尝试 {attempt + 1}/{max_retries}，AI 输出解析失败")
                    continue

                brute_code = result.get("brute_force_code", "")
                test_inputs = result.get("test_inputs", "")

                brute_fn, param_names = self._load_brute_force(brute_code)
                if brute_fn is None:
                    logger.debug(f"TestBuilder: 尝试 {attempt + 1}/{max_retries}，暴力解执行失败")
                    continue

                args_list = self._parse_inputs(test_inputs, len(param_names))
                if not args_list:
                    logger.debug(f"TestBuilder: 尝试 {attempt + 1}/{max_retries}，用例输入解析失败")
                    continue

                cases: list[dict[str, Any]] = []
                for args in args_list:
                    try:
                        expected = brute_fn(*args)
                    except Exception as e:
                        logger.debug(f"TestBuilder: 暴力解运行出错，跳过该用例: {e}")
                        continue
                    cases.append({"args": args, "expected": expected, "source": "generated"})

                if cases:
                    logger.info(f"TestBuilder: 成功构造 {len(cases)} 个额外用例（第 {attempt + 1} 次尝试）")
                    return cases

            except Exception as e:
                logger.debug(f"TestBuilder: 尝试 {attempt + 1}/{max_retries}，异常: {e}")
                continue

        logger.warning("TestBuilder: 所有尝试失败，退回官方用例")
        return []

    def _load_brute_force(self, code: str) -> tuple[Any, list[str]]:
        """执行暴力解代码，返回 (函数对象, 参数名列表)。失败返回 (None, [])。"""
        try:
            ns: dict[str, Any] = {}
            exec("from typing import List, Dict, Optional, Tuple\n", ns)
            exec(code, ns)
            fn = ns.get("brute_solve")
            if not callable(fn):
                logger.warning("TestBuilder: 未找到 brute_solve 函数")
                return None, []
            param_names = self._extract_params(code)
            return fn, param_names
        except Exception as e:
            logger.warning(f"TestBuilder: 暴力解执行错误: {e}")
            return None, []

    def _extract_params(self, code: str) -> list[str]:
        """从 brute_solve 定义中提取参数名(去掉 self)。"""
        match = re.search(r"def\s+brute_solve\s*\(([^)]*)\)", code)
        if not match:
            return []
        params = []
        for p in match.group(1).split(","):
            p = p.strip()
            if ":" in p:
                p = p.split(":")[0].strip()
            if "=" in p:
                p = p.split("=")[0].strip()
            if p and p != "self":
                params.append(p)
        return params

    def _parse_inputs(self, text: str, num_params: int) -> list[list[Any]]:
        """解析测试输入。

        支持两种格式：
        1. 每行一个参数（多行组成一个用例）
        2. 每行一个用例（参数用逗号分隔）
        """
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        if not lines:
            return []

        args_list = []

        # 尝试格式2：每行一个用例（参数用逗号分隔）
        for line in lines:
            try:
                # 尝试按逗号分割（但要注意列表中的逗号）
                # 先尝试 eval 整行
                result = eval(line, {"__builtins__": {}})
                if isinstance(result, tuple):
                    args_list.append(list(result))
                else:
                    args_list.append([result])
            except Exception:
                # 如果 eval 整行失败，尝试按逗号分割
                try:
                    # 简单分割：假设第一个逗号前是第一个参数
                    # 这种方式对简单情况有效
                    parts = line.split(",", 1)
                    if len(parts) == num_params:
                        args = [eval(p.strip(), {"__builtins__": {}}) for p in parts]
                        args_list.append(args)
                except Exception as e:
                    logger.debug(f"TestBuilder: 输入解析失败，跳过: {e}")
                    continue

        # 如果格式2没有结果，尝试格式1：每行一个参数
        if not args_list and num_params > 1:
            for i in range(0, len(lines), num_params):
                chunk = lines[i:i + num_params]
                if len(chunk) != num_params:
                    break
                try:
                    args = [eval(c, {"__builtins__": {}}) for c in chunk]
                    args_list.append(args)
                except Exception as e:
                    logger.debug(f"TestBuilder: 输入解析失败，跳过: {e}")
                    continue

        return args_list
