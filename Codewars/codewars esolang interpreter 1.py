def my_first_interpreter(code):
    output = ''
    x = code.split('.')
    mem = 0
    for y in x:
        for char in y:
            if char == '+':
                mem+=1
                if mem > 255:
                    mem=0
        output += chr(mem)
    return output[0:-1]