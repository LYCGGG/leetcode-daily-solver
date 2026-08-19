class Solution:
    def maxProductPath(self, grid: List[List[int]]) -> int:
        MOD = 10**9 + 7
        m, n = len(grid), len(grid[0])
        
        # 初始化最大和最小乘积表
        max_dp = [[0] * n for _ in range(m)]
        min_dp = [[0] * n for _ in range(m)]
        
        max_dp[0][0] = min_dp[0][0] = grid[0][0]
        
        # 初始化第一行
        for j in range(1, n):
            max_dp[0][j] = max_dp[0][j-1] * grid[0][j]
            min_dp[0][j] = min_dp[0][j-1] * grid[0][j]
        
        # 初始化第一列
        for i in range(1, m):
            max_dp[i][0] = max_dp[i-1][0] * grid[i][0]
            min_dp[i][0] = min_dp[i-1][0] * grid[i][0]
        
        # 填充剩余单元格
        for i in range(1, m):
            for j in range(1, n):
                candidates = [
                    max_dp[i-1][j] * grid[i][j],
                    min_dp[i-1][j] * grid[i][j],
                    max_dp[i][j-1] * grid[i][j],
                    min_dp[i][j-1] * grid[i][j]
                ]
                max_dp[i][j] = max(candidates)
                min_dp[i][j] = min(candidates)
        
        # 检查最大乘积是否为负
        if max_dp[m-1][n-1] < 0:
            return -1
        
        return max_dp[m-1][n-1] % MOD