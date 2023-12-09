def solution(number):
    ttl = 0
    for x in range(number):
        if x%3==0 or x%5==0:
            ttl+=x
    return ttl

print(solution(6))