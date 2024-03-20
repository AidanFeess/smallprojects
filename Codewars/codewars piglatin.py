def pig_it(text):
    text=text.split(' ')
    newtext = ''
    for word in text:
        if word != '?' and word != '!':
            newword = word[1:len(word)] + word[0] + 'ay '
            newtext = newtext + newword
        else:
            newtext = newtext + word + ' '
    newtext = newtext[0:-1]
    return newtext