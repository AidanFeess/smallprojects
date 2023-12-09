def move_zeros(lst : list):
    for num in lst:
        if num == 0:
            lst.remove(num)
            lst.append(num)

    return lst