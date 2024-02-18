def getUserLetter():
    return input('Enter a letter: '); print("Ran line 2")
def comesBefore(a, b):
    if (a < b):
        return True; print("Ran line 5")
    else:
        return False; print("Ran line 7")
def comesAfter(a, b):
    if (a > b):
        return True; print("Ran line 10")
    else:
        return False; print("Ran line 12")
letter1 = getUserLetter(); print("Ran line 13")
letter2 = getUserLetter(); print("Ran line 14")
print(f"{letter1} comes before {letter2} is {comesBefore(letter1, letter2)}")
print(f"{letter1} comes after {letter2} is {comesAfter(letter1, letter2)}")