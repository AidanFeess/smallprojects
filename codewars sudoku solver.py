checkedcells = {}

def find_in_X(X, number):
    for num in X:
        if num == number:
            return True
        
    return False

def find_outsides(square, row, column):
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    # first find each valid solution for every number directly in contact with the current cell
    for num in range(len(row)):
        try:
            nums.remove(row[num])
        except:
            pass
    for num in range(len(column)):
        try:
            nums.remove(column[num])
        except:
            pass
    for list in range(len(square)):
        for num in range(3):
            try:
                nums.remove(square[list][num])
            except:
                pass

    return nums

def find_solutions(square, row, column, idxrow, idxcell, idxsquare, puzzle):
    if puzzle[idxrow][idxcell] != 0:
        return
    checkedcells[f'r{idxrow}c{idxcell}s{idxsquare}'] = find_outsides(square, row, column)

def newSols(squares, rows, columns, puzzle):
    for row in range(9):
        globalcurrentsquare = int(row/3)*3
        for cell in range(len(puzzle[row])):
            localcurrentsquare = globalcurrentsquare + int(cell/3)
            find_solutions(squares[localcurrentsquare], rows[row], columns[cell], row, cell, localcurrentsquare, puzzle)

def remove_from_other_in_square(key, value):
    for key2, value2 in checkedcells.items():
        if len(value2) > 1 and int(key[5]) == int(key2[5]):
            if value[0] in value2:
                checkedcells[key2].remove(value[0])

def update_rows_columns_squares(puzzle):
    rows = []
    columns = []
    squares = []
    # section it into 3x3 squares to check square validity
    for c in range(9):
        offset = int(c/3)*3
        c -= offset
        square = []
        for r in range(3):
            square.append(puzzle[r+offset][3*(c):3*(c+1)])
        squares.append(square)
    # then rows
    for r in range(9):
        rows.append(puzzle[r])
    # finally columns
    for r in range(9):
        newColumn = []
        for c in range(9):
            newColumn.append(puzzle[c][r])
        columns.append(newColumn)

    return rows, columns, squares

def sudoku(puzzle):
    for l in puzzle:
        print(l)
    print('___________________________\n')

    rows = []
    columns = []
    squares = []
    rows, columns, squares = update_rows_columns_squares(puzzle)
    
    # now we start solving
    # first we should figure out what each cell can't be

    newSols(squares, rows, columns, puzzle)
    
    for _pass in range(100):
        for key, value in checkedcells.items():
            row = int(key[1])
            column = int(key[3])
            square = int(key[5])

            # if there is only 1 value then just go ahead and solve the square
            if len(value) == 1:
                puzzle[row][column] = value[0]
                # now remove that number from every other cell in that square
                remove_from_other_in_square(key, value)
                rows, columns, squares = update_rows_columns_squares(puzzle)
                checkedcells[key] = []
            elif len(value) > 1:
                for number in value:
                    if find_in_X(columns[int(key[3])], number):
                        checkedcells[key].remove(number)
                    if find_in_X(squares[int(key[5])], number):
                        checkedcells[key].remove(number)
                    if find_in_X(rows[int(key[1])], number):
                        try:
                            checkedcells[key].remove(number)
                        except:
                            pass
            
    return puzzle

finished = sudoku(
    [
        [5,2,8,0,9,0,0,4,0],
        [9,4,3,0,5,0,0,0,8],
        [6,0,0,4,0,8,0,0,5],
        [7,0,0,9,3,5,0,8,2],
        [0,1,2,0,6,0,0,3,0],
        [3,9,5,0,0,0,4,0,6],
        [1,0,0,5,4,0,0,6,7],
        [0,3,7,8,0,6,9,5,0],
        [0,5,6,0,0,0,8,0,3]
    ]
    )

for row in finished:
    print(f'{row}')