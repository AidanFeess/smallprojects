import string
# asslang
# tape, n = 0 - 52
# a = add (to 52, then wrap)
# s = subtract (to 0, then wrap)
# $ = start loop
# h = print
# o = next
# l = end loop
# e = end the program and print the current tape

# [33, 30, 37, 37, 40, 48, 40, 43, 37, 29] = HELLOWORLD

def add(cell):
    return cell + 1 if cell < 52 else 0

def sub(cell):
    return cell - 1 if cell > 0 else 52 

def asslang(code, tape):
    rslt = ''
    pointer = 0
    for letter in code:
        letter = letter.lower()
        match letter:
            case "a":
                tape[pointer] = add(tape[pointer])
            case "s":
                tape[pointer] = sub(tape[pointer])
            case "o":
                pointer += 1
                if pointer > len(tape):
                    pointer = 0
    
    for ascii in tape:
        rslt += string.ascii_letters[ascii]

    return rslt

print(asslang('', [33, 30, 37, 37, 40, 48, 40, 43, 37, 29]))