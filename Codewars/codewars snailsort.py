def snail(snail_map):
    snailed_map = []
    loops = 0
    xpos = 0
    ypos = 0
    mover = 'r'
    width = len(snail_map[0])
    height = len(snail_map)
    # 0,0 -> 0,1 -> 0, n-1
    # 0,n-1 -> 1,n-1 -> n-1, n-1
    for _ in range(height*width):

        print(ypos, xpos)
        snailed_map.append(snail_map[ypos][xpos])

        match mover:
            case 'r':
                xpos += 1
                ypos = 0 + loops
                if xpos >= width-1 - loops:
                    mover = 'd'
            case 'd':
                xpos = width-1 - loops
                ypos += 1
                if ypos >= height-1 - loops:
                    mover = 'l'
            case 'l':
                xpos -= 1
                ypos = height-1 - loops
                if xpos <= 0 + loops:
                    mover = 'u'
            case 'u':
                xpos = 0 + loops
                ypos -= 1
                if ypos <= 0 + (loops+1):
                    mover = 'r'
                    loops += 1
        
    return snailed_map
x = snail([[1,2,3,4],
           [12,13,14,5],
           [11,16,15,6],
           [10,9,8,7]])

print(x)