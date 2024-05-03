import random as rand
import time
start = time.time()
def smaller(arr):
    ret = []
    for i in range(len(arr)):
        num = 0
        for j in range(i, len(arr)):
            if arr[j] < arr[i]:
                num += 1
        ret.append(num)
    return ret

#print(smaller([5, 4, 3, 2, 1]), [4, 3, 2, 1, 0])
#print(smaller([1, 2, 3]), [0, 0, 0])
print(smaller([rand.randint(0, 9) for j in range(120000)]))
#print(smaller([1, 2, 1]), [0, 1, 0])
#print(smaller([1, 1, -1, 0, 0]), [3, 3, 0, 0, 0])
#print(smaller([5, 4, 7, 9, 2, 4, 4, 5, 6]), [4, 1, 5, 5, 0, 0, 0, 0, 0])
#print(smaller([5, 4, 7, 9, 2, 4, 1, 4, 5, 6]), [5, 2, 6, 6, 1, 1, 0, 0, 0, 0])

print(f"\nexec: {round(time.time() - start)}")