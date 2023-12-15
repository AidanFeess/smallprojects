class Solution:
    def destCity(self, paths: list[list[str]]) -> str:
        noPath = []
        for path in paths:
            for x in range(len(path)):
                if x != 0:
                    noPath.append(path[x])

        for path in paths:
            for x in range(len(path)):
                if x == 0 and path[x] in noPath:
                    noPath.remove(path[x])
                    
        return noPath[0]

x=Solution
z = x.destCity(x, [["B","C"],["D","B"],["C","A"]])
#print(z)