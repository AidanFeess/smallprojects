def sq_in_rect(lng, wdth):
    if lng == wdth: return None
    return_rect = []
    rect = []
    for row in range(lng):
        row_arry = []
        for column in range(wdth):
            row_arry.append("X")
        rect.append(row_arry)

    while True:
        ypos = 0
        xpos = 0
        
        try:
            if rect[ypos][xpos] == "x":
                xpos += 1
        except:
            return_rect.append(xpos)
            for y in range(xpos):
                for x in range(xpos):
                    rect[x][y] = None
            break
            
    for line in rect:
        print(line)
            
    return None

sq_in_rect(3, 5)