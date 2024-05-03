class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        total = 0
        for num in range(len(nums)):
            total = nums[num]
            for num2 in range(len(nums)):
                if num == num2: continue
                if total + nums[num2] == target:
                    return [num, num2]
                
x = Solution
print(x.twoSum(x, [2, 7, 11, 15], 9))
print(x.twoSum(x, [3, 2, 4], 6))
print(x.twoSum(x, [3, 3], 6))