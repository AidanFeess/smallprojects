import keyboard
import sys
import time

text_file = input('[?] Enter the directory of the text file (ex: C:/Users/*USERNAME*/Documents/TestData.txt): ')
separator = input('[?] Enter the separator you want to use (This separates the term from the definition, i.e. Apple : Fruit): ')

#checks
try:
    text_file = open(text_file, mode='r', encoding="utf8")
except:
    sys.exit(f'[EXIT] Could not access the file [{text_file.split("/")[-1]}]. Did you type the directory correctly?')

try:
    separator = str(separator)
except:
    sys.exit(f'[EXIT] Could not convert {separator} to string. Make sure its a valid separator.')

#start
print("[!] Hopefully you didn't insert a massive text file")
time.sleep(.5)
print('[!] Beginning in 3 seconds! Make sure you have clicked on the first term!')
time.sleep(3)
runstart = int(time.time())

for line in text_file:
    
    if len(line) < 4 or 'chapter' in line.lower(): #hopefully this will prevent empty lines lol and not allow "Chapter" into the actual stuff
        continue
    lines = line.split(separator)
    # frontcard info <separator> backcard info --> [frontcard info, backcard info]
    keyboard.write(lines[0].strip())
    keyboard.press_and_release('tab')
    time.sleep(.2) # sleeps between tabs because otherwise it just loses its shit
    keyboard.write(lines[1].strip().capitalize())
    keyboard.press_and_release('tab')
    time.sleep(.2)

print(f"[!] Completed in {int(time.time()) - runstart} second(s)!" )