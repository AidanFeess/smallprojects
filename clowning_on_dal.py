from math import ceil
def encrypt_message(message):
    oddMessage = ''
    evenMessage = ''
    charNum = 0
    for ch in message:
        if charNum % 2 == 0:
            evenMessage += ch
        else:
            oddMessage += ch
        charNum += 1
    return oddMessage + evenMessage

encrypted_message = encrypt_message(input('Input secret message here: '))
print(encrypted_message)
'''
def decrypt_message(scrambleMessage):
    midpoint = len(scrambleMessage) // 2
    evenMessage = scrambleMessage[midpoint:]
    oddMessage = scrambleMessage[:midpoint]
    decryptedMessage = ''
    for i in range(len(evenMessage)):
        decryptedMessage += evenMessage[i]
        
        if i < len(oddMessage):
            decryptedMessage += oddMessage[i]
    
    return decryptedMessage

decrypted_message = decrypt_message(encrypted_message)
print(decrypted_message)'''


def decode(msg):
    return ''.join([ msg[len(msg)//2+x] + msg[x] if x != ceil(len(msg)/2)-1 or (len(msg) % 2 == 0 and x+1 == ceil(len(msg)/2)) else msg[len(msg)//2+x] for x in range(ceil(len(msg)/2)) ])
            
print(decode(encrypted_message))