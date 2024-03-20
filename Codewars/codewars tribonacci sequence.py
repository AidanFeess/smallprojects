def tribonacci(signature, n):
    if n == 0:
        return []
    for i in range(n):
        newnum = 0
        for x in range(3):
            newnum += signature[x+i]
        signature.append(newnum)

    return signature[0:n]

print(tribonacci([1, 3, 5], 100))