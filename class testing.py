def printSquare(x):
    [print(("* "*y+"\n")*y) for y in range(x,x+1)]

def printSquareOutside(x):
    txt = ""
    for col in range(x):
        for row in range(x):
            if row < 1 or col == 0 or col == x-1 or row == x-1:
                txt += "* " 
            else:
                txt += "  "
        txt += "\n"
    print(txt)

printSquareOutside(7)