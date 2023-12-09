def DNA_strand(dna):
    dnadict = {
        'A' : 'T',
        'G' : 'C',
        'T' : 'A',
        'C' : 'G'
    }
    newstr = ""
    for letter in dna:
        letter.upper()
        newstr = newstr + dnadict[letter]
        
    return newstr