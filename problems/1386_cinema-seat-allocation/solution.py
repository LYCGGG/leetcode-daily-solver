class Solution:
    def maxNumberOfFamilies(self, n: int, reservedSeats: List[List[int]]) -> int:
        from collections import defaultdict
        
        row_seats = defaultdict(set)
        for row, seat in reservedSeats:
            row_seats[row].add(seat)
        
        result = (n - len(row_seats)) * 2
        
        left_block = {2, 3, 4, 5}
        mid_block = {4, 5, 6, 7}
        right_block = {6, 7, 8, 9}
        
        for row, seats in row_seats.items():
            left_ok = not (seats & left_block)
            mid_ok = not (seats & mid_block)
            right_ok = not (seats & right_block)
            
            if left_ok and right_ok:
                result += 2
            elif left_ok or mid_ok or right_ok:
                result += 1
        
        return result