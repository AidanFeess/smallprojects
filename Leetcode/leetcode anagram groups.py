from typing import List

def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
    result = {}
    for string in strs:
        count = [0] * 26
        for character in string:
            count[ord(character) - ord('a')] += 1
        result[tuple(count)].append(string)
    return result.values()