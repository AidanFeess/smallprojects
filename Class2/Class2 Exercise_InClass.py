def smallest_num_sum(numbers):
    smallest1 = min(numbers)
    numbers.remove(smallest1)
    return smallest1 + min(numbers)

print(smallest_num_sum([1, 2, 20, 200]))