def square_digits(num):
    return ''.join([str(int(str(num)[letter])**2) if letter < int(len(str(num)) / 2) else str(int(str(num)[letter])**2)[::-1] for letter in range(len(str(num)))])

print(square_digits(input("Number: ")))