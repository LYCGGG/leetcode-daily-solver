class Solution:
    def stoneGameIX(self, values: List[int]) -> bool:
        cnt = [0, 0, 0]
        for v in values:
            cnt[v % 3] += 1
        if cnt[0] % 2 == 0:
            return abs(cnt[1] - cnt[2]) > 1
        else:
            return abs(cnt[1] - cnt[2]) > 1 and (cnt[1] > 0 or cnt[2] > 0)