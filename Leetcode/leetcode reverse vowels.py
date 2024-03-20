class Solution:
    def reverseVowels(self, s: str) -> str:
        vowels = ['a','e','i','o','u', 'A', 'E', 'I', 'O', 'U']
        tempchar = '<'
        val = False
        for l in s:
            if l in vowels: val = True; break
        if not val: return s
        inv = [x for x in s if x in vowels]
        inv.reverse()

        s = [tempchar if x in vowels else x for x in s]
        for letter in range(len(s)):
            if len(inv) <= 0: break
            s[letter] = inv[0] if s[letter] == tempchar else s[letter]
            if s[letter] == inv[0]: inv.pop(0)

        return ''.join([x for x in s])