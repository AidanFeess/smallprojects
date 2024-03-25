def GetStrLengths(str_list : str) -> list[int]:
    return [len(string) for string in str_list]

print(GetStrLengths(["nih", "csc", "no"]))