def isValid(self, s: str) -> bool:
    start, end = 0, len(s)-1
    ref = {
        "(" : ")",
        "{" : "}",
        "[" : "]",
    }
    while start < len(s) // 2:
        if ref[s[start]] == s[end]:
            start += 1
            end -= 1
            continue
        else:
            return False
    return True

print(isValid(None, "(])"))