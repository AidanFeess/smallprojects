
for num in range(100):
    for num2 in range(100):
        letters_in_num1 = str(num)
        letters_in_num2 = str(num2)
        together = str(num+num2)
        if len(together) < 3 or len(str(num)) < 2 or len(str(num2)) < 2: continue
        if together[0] != "1" or together[2] != "1": continue
        if letters_in_num1[0] != letters_in_num2[1] or letters_in_num2[0] != letters_in_num1[1]: pass
        if together[1] not in letters_in_num1 and together[1] not in letters_in_num2:
            print(together, num, num2)