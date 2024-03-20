import random, string
def ispalindrome(p):
    if p.replace(' ', '').upper()==p.replace(' ', '').upper()[::-1]: return True
    return False