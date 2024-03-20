def solution(args):
    ranges = ''
    cont = True
    pos = 0 # keeping track of our position inside the loop
    size = 1 # the size of the currently tracked range
    start = args[pos]
    for _ in range(len(args)):
        # for every number we need to look twice into the future to see if its a set or just a single number
        cont = True
        size = 1
        while cont == True: # keep repeating until the set ends or a set isn't found
            try:
                if args[pos+1] == args[pos]+1:
                    pos += 1
                    size += 1
                    continue
                else:
                    if size > 2:
                        ranges += f'{start}-{args[pos]},'
                    else:
                        if start == args[pos]:
                            ranges += f'{start},'
                        else:
                            ranges += f'{start},'
                            ranges += f'{args[pos]},'
                    cont = False
            except:
                if size > 2:
                    ranges += f'{start}-{args[pos]},'
                else:
                    if start == args[pos]:
                        ranges += f'{start},'
                    else:
                        ranges += f'{start},'
                        ranges += f'{args[pos]},'
                cont = False
        pos += 1
        if pos >= len(args): break
        start = args[pos]
    return ranges[:-1]