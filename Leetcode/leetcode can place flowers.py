class Solution:
    def canPlaceFlowers(self, flowerbed: list[int], n: int) -> bool:
        l = 0

        for x in range(len(flowerbed)):
            try:
                if flowerbed[x+1] == 1: continue
            except:
                pass
 
            if flowerbed[x] == 1 or l == 1:
                l=flowerbed[x]
                continue
            else:
                l = 1
                n -= 1
    
        return n <= 0