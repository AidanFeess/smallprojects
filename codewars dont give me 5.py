from math import dist
def dont_give_me_five(a,b):
    b+=1
    num = int(dist([a],[b]))
    
    for x in range(a,b):
        if '5' in str(x):
            num -= 1
    
    return num

# too slow