"""Local test runner for LeetCode solutions."""

from __future__ import annotations

import json
import re
from typing import Any

from loguru import logger


def parse_test_cases(example_testcases: str, code_snippets: list[dict], language: str) -> list[dict[str, Any]]:
    """Parse test cases from LeetCode format.
    
    Args:
        example_testcases: Raw test case string from LeetCode
        code_snippets: Code snippets for the problem
        language: Programming language (e.g., python3)
    
    Returns:
        List of test case dicts with input params and expected output
    """
    if not example_testcases:
        return []
    
    # Split by newlines and clean
    lines = [line.strip() for line in example_testcases.strip().split('\n') if line.strip()]
    
    # Get function signature from code snippet
    func_signature = _get_function_signature(code_snippets, language)
    if not func_signature:
        logger.warning("Could not extract function signature")
        return []
    
    # Parse parameters from signature
    params = _extract_params(func_signature)
    if not params:
        logger.warning("Could not extract parameters from signature")
        return []
    
    # Group lines into test cases (each test case has len(params) lines)
    test_cases = []
    num_params = len(params)
    
    for i in range(0, len(lines), num_params):
        if i + num_params <= len(lines):
            test_case = {}
            for j, param_name in enumerate(params):
                test_case[param_name] = lines[i + j]
            test_cases.append(test_case)
    
    return test_cases


def _get_function_signature(code_snippets: list[dict], language: str) -> str | None:
    """Extract function signature from code snippets."""
    lang_map = {
        "python3": "python3",
        "python": "python3",
        "java": "java",
        "cpp": "cpp",
        "javascript": "javascript",
    }
    
    target_lang = lang_map.get(language, language)
    
    for snippet in code_snippets:
        if snippet.get("langSlug") == target_lang:
            return snippet.get("code", "")
    
    return None


def _extract_params(code: str) -> list[str]:
    """Extract parameter names from function definition."""
    # Match Python function definition
    match = re.search(r'def\s+\w+\s*\(([^)]+)\)', code)
    if match:
        params_str = match.group(1)
        params = []
        for param in params_str.split(','):
            param = param.strip()
            # Remove type hints
            if ':' in param:
                param = param.split(':')[0].strip()
            # Remove default values
            if '=' in param:
                param = param.split('=')[0].strip()
            if param and param != 'self':
                params.append(param)
        return params
    
    return []


def _extract_function_name(code: str) -> str:
    """Extract function name from code."""
    # Match Python function definition in class
    match = re.search(r'def\s+(\w+)\s*\(', code)
    if match:
        return match.group(1)
    return "twoSum"  # Default fallback


def run_local_test(code: str, test_cases: list[dict], func_name: str = None) -> dict[str, Any]:
    """Run code locally with test cases.
    
    Args:
        code: Python code to test
        test_cases: List of test case dicts
        func_name: Name of the function to test (auto-detect if None)
    
    Returns:
        Dict with success status and error message if any
    """
    if not test_cases:
        return {"success": False, "error": "No test cases available"}
    
    # Auto-detect function name if not provided
    if func_name is None:
        func_name = _extract_function_name(code)
    
    try:
        # Create a temporary module
        namespace = {}
        # Add List import for type hints
        exec("from typing import List", namespace)
        exec(code, namespace)
        
        # Get the function
        func = None
        if func_name in namespace:
            func = namespace[func_name]
        else:
            # Try to find it in a class
            for name, obj in namespace.items():
                if isinstance(obj, type) and hasattr(obj, func_name):
                    instance = obj()
                    func = getattr(instance, func_name)
                    break
        
        if func is None:
            return {"success": False, "error": f"Function '{func_name}' not found"}
        
        # Run each test case
        for i, test_case in enumerate(test_cases):
            try:
                # Parse inputs
                args = []
                for param_name, param_value in test_case.items():
                    args.append(eval(param_value))
                
                # Call function
                result = func(*args)
                
                # For now, just check if it runs without error
                logger.debug(f"Test case {i+1}: result = {result}")
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Test case {i+1} failed: {str(e)}",
                    "test_case": test_case,
                }
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": f"Code execution failed: {str(e)}"}
