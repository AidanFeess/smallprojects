def dir_reduc(arr):
    cancels = {
        "SOUTH" : "NORTH",
        "NORTH" : "SOUTH",
        "WEST" : "EAST",
        "EAST" : "WEST"
    }
    for _loops in range(10):
        for direction in range(len(arr)):
            if direction+1 >= len(arr): break
            if arr[direction+1] == cancels[arr[direction]]:
                arr.pop(direction)
                arr.pop(direction)
                break
    return arr