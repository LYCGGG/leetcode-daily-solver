"""Unit tests for pure parsing functions."""

import pytest
from leetcode_daily_solver.local_tester import parse_test_cases, _extract_params


class TestParseTestCases:
    """Test parse_test_cases function."""

    def test_single_param(self):
        """Test parsing single parameter test cases."""
        code_snippets = [{
            "langSlug": "python3",
            "code": "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        pass"
        }]
        example_testcases = "[2,7,11,15]\n9\n[3,2,4]\n6"
        
        result = parse_test_cases(example_testcases, code_snippets, "python3")
        
        assert len(result) == 2
        assert result[0]["source"] == "official"
        assert result[0]["expected"] is None
        assert len(result[0]["args"]) == 2

    def test_empty_input(self):
        """Test parsing empty input."""
        result = parse_test_cases("", [], "python3")
        assert result == []

    def test_no_code_snippets(self):
        """Test parsing with no code snippets."""
        result = parse_test_cases("[1,2,3]", [], "python3")
        assert result == []


class TestExtractParams:
    """Test _extract_params function."""

    def test_extract_simple_params(self):
        """Test extracting simple parameters."""
        code = "def twoSum(self, nums: List[int], target: int) -> List[int]:"
        result = _extract_params(code)
        
        assert "nums" in result
        assert "target" in result
        assert "self" not in result

    def test_extract_params_without_types(self):
        """Test extracting parameters without type hints."""
        code = "def twoSum(self, nums, target):"
        result = _extract_params(code)
        
        assert "nums" in result
        assert "target" in result

    def test_extract_params_with_defaults(self):
        """Test extracting parameters with default values."""
        code = "def twoSum(self, nums=[], target=0):"
        result = _extract_params(code)
        
        assert "nums" in result
        assert "target" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
