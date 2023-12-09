def duplicate_count(newStr):
    allLetters = []
    repeatedLetters = []
    for letter in newStr:
        letter = letter.lower()
        if letter in allLetters:
            if not letter in repeatedLetters:
                repeatedLetters.append(letter)
        allLetters.append(letter)

    return len(repeatedLetters)