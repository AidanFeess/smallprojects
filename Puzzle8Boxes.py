from random import choice

positions = []
nums = [x+1 for x in range(8)]

def pickNew():
    newChoice = choice(nums)
    nums.remove(newChoice)
    return newChoice

for y in range(3):
    if y == 0 or y == 2:
        newNums = [pickNew() for x in range(2)]
        positions.append([-2, newNums[0], newNums[1], -2])
    if y == 1:
        newNums = [pickNew() for x in range(4)]
        positions.append([newNums[0], newNums[1], newNums[2], newNums[3]])

for x in positions:
    print(x)