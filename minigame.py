import os
import time
map = [ ['x','x','x','x','x'],
        ['x','0','0','0','x'],
        ['x','0','0','0','x'],
        ['x','0','0','0','x'],
        ['x','x','x','x','x'],
       ]
start = True

def get_map(plr):
    global start
    if not start:
        map[plr.last_index['y']][plr.last_index['x']] = plr.indicator
        os.system('cls')
        print('LAST MAP')
        for l in map:
            print(f"[> {l} <]")
        map[plr.last_index['y']][plr.last_index['x']] = '0'
        time.sleep(1)
    map[plr.position['y']][plr.position['x']] = plr.indicator
    os.system('cls')
    print('CURRENT MAP')
    for l in map:
        print(f"[> {l} <]")
    
    if start: start = False

class Character():

    def __init__(self, health=10, damage=1, position={'x':1,'y':1}, indicator='m'):
        self.health = health
        self.damage = damage
        self.position = position
        self.indicator = indicator
        self.last_index = {'x':1,'y':1}
        map[self.position['y']][self.position['x']] = self.indicator

    def move(self, direction):
        direction = direction.lower()
        self.last_index = {'y' : self.position['y'], 'x' : self.position['x']}
        match direction:
            case 'right':
                if self.position['x'] + 1 > len(map[0]) or map[self.position['y']][self.position['x']+1] != '0':
                    return
                map[self.position['y']][self.position['x']] = '0'
                self.position['x'] += 1
            case 'left':
                if self.position['x'] - 1 < 0 or map[self.position['y']][self.position['x']-1] != '0': return
                map[self.position['y']][self.position['x']] = '0'
                self.position['x'] -= 1
            case 'down':
                if self.position['y'] + 1 > len(map) or map[self.position['y']+1][self.position['x']] != '0': return
                map[self.position['y']][self.position['x']] = '0'
                self.position['y'] += 1
            case 'up':
                if self.position['y'] - 1 < 0 or map[self.position['y']-1][self.position['x']] != '0': return
                map[self.position['y']][self.position['x']] = '0'
                self.position['y'] -= 1
        

    def get_info(self):
        return f"[!] == CHARACTER INFO == \n[!] Health: {self.health}\n[!] Damage: {self.damage}\n"

def update(plr : Character):
    get_map(plr)
    time.sleep(1)
    print('\n')
    print(plr.get_info())

Player = Character(1, 1, {'x':1,'y':1}, 'p')

while True:
    update(Player)
    inpt = (input('[?] What would you like to do next?\n[!] Move (-direction) \n[!] Debug (-info)\n[>  ')).lower()
    if 'move' in inpt:
        Player.move(inpt.split('-')[-1])