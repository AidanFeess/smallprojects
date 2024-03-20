class Solution:
    def reverseWords(self, s: str) -> str:
        s=[x for x in s.split(" ") if len(x)>0]
        s.reverse()
        s=''.join([x+' ' for x in s])
        return s.strip()