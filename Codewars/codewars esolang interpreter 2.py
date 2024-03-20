def flip(pos, tape):
    bit = tape[pos]
    match bit:
        case '0':
            bit='1'
        case '1':
            bit='0'
    tape[pos] = bit
    return pos, tape

def next(pos, tape):
    pos+=1
    if pos >= len(tape):
        return -1, tape
    return pos, tape

def last(pos, tape):
    pos-=1
    if pos < 0:
        return -1, tape
    return pos, tape

def loop(pos, tape, code, codepos):
    end_loop_pos = 0
    loop_depth = 0 # basically how many other loops are between this loops start and end
    for command in range(codepos+1, len(code)): # codepos+1 so that we dont start at our loop bracket
        print(codepos)
        if code[command] == '[':
            loop_depth += 1
        if code[command] == ']' and loop_depth == 0:
            end_loop_pos = command
            break
        elif code[command] == ']' and loop_depth > 0:
            loop_depth -= 1

    if tape[pos] == '0':
        return pos, tape, end_loop_pos

    codepos += 1
    start_loop_pos = codepos

    while True:
        if code[codepos] != '[' and code[codepos] != ']':
            pos, tape = run(code[codepos], pos, tape)
        elif code[codepos] == '[':
            pos, tape, codepos = commands[code[codepos]](pos, tape, code, codepos)

        codepos += 1

        if pos == -1:
            return pos, tape, end_loop_pos
        
        if code[codepos] == ']' and codepos == end_loop_pos:
            if tape[pos] == '0':
                return pos, tape, end_loop_pos
            codepos = start_loop_pos
            
        
    return pos, tape, end_loop_pos

def endloop(pos, tape, code, codepos):
    return pos, tape, codepos

commands = {
        '>' : next,
        '<' : last,
        '*' : flip,
        '[' : loop,
        ']' : endloop
    }

def interpreter(code, tape):

    tape = [x for x in tape]
    pos = 0
    codepos = 0

    for x in range(len(code)):
        if not code[codepos] in commands:
            codepos += 1
            continue
        if code[codepos] != '[' and code[codepos] != ']':
            pos, tape = run(code[codepos], pos, tape)
        else:
            pos, tape, codepos = commands[code[codepos]](pos, tape, code, codepos)
        codepos += 1
        if pos == -1 or codepos >= len(code):
            reply = ''
            for x in tape:
                reply += x
            return reply
        
    reply = ''
    for x in tape:
        reply += x
    return reply

def run(command, pos, tape):
    pos, tape = commands[command](pos, tape)
    return pos, tape