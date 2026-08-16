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

    def build(self, problem: dict, language: str, num_cases: int = 10) -> list[dict[str, Any]]:
        """构造带期望输出的测试用例列表。失败返回空列表(可降级)。

        Returns:
            [ {"args": [...], "expected": <value>, "source": "generated"}, ... ]
        """
        try:
            result = self.ai.build_testcases(problem, num_cases, language)
            if not result:
                logger.warning("TestBuilder: AI 输出解析失败，退回官方用例")
                return []

            brute_code = result.get("brute_force_code", "")
            test_inputs = result.get("test_inputs", "")

            brute_fn, param_names = self._load_brute_force(brute_code)
            if brute_fn is None:
                logger.warning("TestBuilder: 暴力解执行失败，退回官方用例")
                return []

            args_list = self._parse_inputs(test_inputs, len(param_names))
            if not args_list:
                logger.warning("TestBuilder: 用例输入解析失败，退回官方用例")
                return []

            cases: list[dict[str, Any]] = []
            for args in args_list:
                try:
                    expected = brute_fn(*args)
                except Exception as e:
                    logger.debug(f"TestBuilder: 暴力解运行出错，跳过该用例: {e}")
                    continue
                cases.append({"args": args, "expected": expected, "source": "generated"})

            logger.info(f"TestBuilder: 成功构造 {len(cases)} 个额外用例")
            return cases
        except Exception as e:
            logger.warning(f"TestBuilder: 构造失败，退回官方用例: {e}")
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
        """按每 num_params 行一个用例解析输入。"""
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        if num_params <= 0:
            num_params = 1
        args_list = []
        for i in range(0, len(lines), num_params):
            chunk = lines[i:i + num_params]
            if len(chunk) != num_params:
                break
            try:
                args = [eval(c, {"__builtins__": {}}) for c in chunk]
            except Exception as e:
                logger.debug(f"TestBuilder: 输入解析失败，跳过: {e}")
                continue
            args_list.append(args)
        return args_list
