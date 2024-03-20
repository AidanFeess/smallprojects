import time

numberlist = [5, 10, 3, 1, 2, 8, 9, 4]

def bubble_sort():
    length = len(numberlist)
    while length > 0:
        for i in range(len(numberlist)):
            time.sleep(.01)
            if i == len(numberlist) or i + 1 > len(numberlist) - 1:
                length -= 1
                break
            if numberlist[i] > numberlist[i + 1]:
                old = numberlist[i]
                numberlist[i] = numberlist[i + 1]
                numberlist[i+1] = old
            print(numberlist)

def select_sort():
    start = 0
    while start < len(numberlist):
        smallest = numberlist[start]
        switch_index = 0
        for i in range(start, len(numberlist)):
            
            if i+1 > len(numberlist)-1: 
                numberlist[switch_index] = numberlist[start]
                numberlist[start] = smallest
                start += 1
                break
            if numberlist[i] < smallest:
                smallest = numberlist[i]
                switch_index = i
        print(numberlist)
select_sort()