def numSpecial(mat: list[list[int]]) -> int:
        cols = [idx for idx in zip(*mat)]
        special = 0

        for r in range(len(mat)):
            for c in range(len(mat[0])):
                amount_of_1s = 0
                # we're going to check every single cell
                if mat[r][c] != 1: continue # if its not a one, it doesn't matter
                amount_of_1s = 1
                # we can get the row by the 'r' index
                currentrow = mat[r]
                # we can get the column by the 'c' index
                currentcol = cols[c]
                # now that we know the row of the cell and the column of the cell
                # we can check to see if that row has any **other** 1s in it
                # we do this by iterating over that row and that column, making sure to skip that cell's index
                # in that row and that column. remember that the cell's index in the row is 'r' and the
                # cell's index in the column is 'c'

                for check_cell in range(len(currentrow)):
                    if check_cell != c and currentrow[check_cell] == 1:
                        amount_of_1s += 1
                        
                for check_cell in range(len(currentcol)):
                     if check_cell != r and currentcol[check_cell] == 1:
                        amount_of_1s += 1

                if amount_of_1s == 1:
                    special += 1
                 
        return special