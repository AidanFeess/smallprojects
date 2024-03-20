def generate_hashtag(s):
    if s == '' or len(s) == 0:
        return False
    s = s.split(' ')
    s = [i for i in s if i != '']
    final = '#'
    for word in s:
        word = word.lower()
        if len(word) > 1:
            final = final + word[0].upper() + word[1:-1] + word[-1]
        else:
            final = final + word.upper()

    if len(final) > 140 or len(final) <= 0:
        return False
    return final