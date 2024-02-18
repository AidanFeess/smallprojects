def getBMI(height, weight):
    return weight / (height ** 2)
height = float(input("height: "))
weight = float(input("weight: "))
print(f"your bmi is {getBMI(height, weight)}")