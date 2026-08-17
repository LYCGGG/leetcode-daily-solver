class Solution:
    def longestSubsequence(self, nums: list[int]) -> int:
        if not nums:
            return 0
        
        n = len(nums)
        
        # 计算整个数组的异或和
        total_xor = 0
        for num in nums:
            total_xor ^= num
        
        # 如果异或和非零，整个数组就是一个解
        if total_xor != 0:
            return n
        
        # 如果异或和为零，检查是否有非零元素
        has_nonzero = False
        for num in nums:
            if num != 0:
                has_nonzero = True
                break
        
        # 如果有非零元素，最长子序列长度为n-1
        if has_nonzero:
            return n - 1
        else:
            # 所有元素都是0，没有非零异或的子序列
            return 0