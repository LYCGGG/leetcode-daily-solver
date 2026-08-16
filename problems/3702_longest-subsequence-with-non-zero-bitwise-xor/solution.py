from typing import List

class Solution:
    def longestSubsequence(self, nums: List[int]) -> int:
        total_xor = 0
        for x in nums:
            total_xor ^= x
        
        # If XOR of entire array is non-zero, whole array is valid
        if total_xor != 0:
            return len(nums)
        
        # XOR is zero, check for non-zero elements
        # If any element is non-zero, we can remove one to get non-zero XOR
        if any(x != 0 for x in nums):
            return len(nums) - 1
        
        # All elements are zero, no valid subsequence
        return 0