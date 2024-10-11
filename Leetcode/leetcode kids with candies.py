class Solution:
    def kidsWithCandies(self, candies: list[int], extraCandies: int) -> list[bool]:
        return [True if kid+extraCandies>=max(candies) else False for kid in candies]
    
x = Solution
print(x.kidsWithCandies(x, [1, 2, 3], 1))