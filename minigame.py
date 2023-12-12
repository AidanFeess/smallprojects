import os
import time
map = [ ['x','x','x','x','x','x','x'],
        ['x','0','0','0','0','0','x'],
        ['x','0','0','0','0','0','x'],
        ['x','0','0','0','0','0','x'],
        ['x','0','0','0','0','0','x'],
        ['x','0','0','0','0','0','x'],
        ['x','x','x','x','x','x','x'],
       ]
start = True

def get_map(plr, enemy):
    enemy_turn(enemy, plr)
    global start
    if not start:
        map[plr.last_index['y']][plr.last_index['x']] = plr.indicator
        map[enemy.last_index['y']][enemy.last_index['x']] = enemy.indicator
        os.system('cls')
        print('LAST MAP')
        for l in map:
            print(f"[> {l} <]")
        map[plr.last_index['y']][plr.last_index['x']] = '0'
        map[enemy.last_index['y']][enemy.last_index['x']] = '0'
        time.sleep(1)
    map[plr.position['y']][plr.position['x']] = plr.indicator
    map[enemy.position['y']][enemy.position['x']] = enemy.indicator
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
                    return False
                map[self.position['y']][self.position['x']] = '0'
                self.position['x'] += 1
            case 'left':
                if self.position['x'] - 1 < 0 or map[self.position['y']][self.position['x']-1] != '0':
                    return False
                map[self.position['y']][self.position['x']] = '0'
                self.position['x'] -= 1
            case 'down':
                if self.position['y'] + 1 > len(map) or map[self.position['y']+1][self.position['x']] != '0':
                    return False
                map[self.position['y']][self.position['x']] = '0'
                self.position['y'] += 1
            case 'up':
                if self.position['y'] - 1 < 0 or map[self.position['y']-1][self.position['x']] != '0':
                    return False
                map[self.position['y']][self.position['x']] = '0'
                self.position['y'] -= 1
        return True
        
    def dont_move(self):
        self.last_index = self.position

    def get_info(self):
        return f"[!] == CHARACTER INFO == \n[!] Health: {self.health}\n[!] Damage: {self.damage}\n"
    
def enemy_turn(enemy : Character, plr : Character):
    # AI BRAIN:
    # - HOW FAR?
    #   - TOO CLOSE
    #       - MOVE AWAY
    #   - FAR
    #       - STAY
    ydist = enemy.position['y'] - plr.position['y'] # neg is below
    xdist = enemy.position['x'] - plr.position['x'] # neg is right
    truey = abs(ydist)-1
    truex = abs(xdist)-1
    moved = False
    tried = 'z'
    tries = 0
    while moved == False:
        if ydist == xdist or tries > 3:
            enemy.dont_move()
            break
        
        if truex > truey and tried != 'x' or tried == 'y':
            tried = 'x'
            if xdist < 0:
                moved = enemy.move('left'); print('L')
            else:
                moved = enemy.move('right'); print('R')
        elif truey > truex and tried != 'y' or tried == 'x':
            tried = 'y'
            if ydist < 0:
                moved = enemy.move('up'); print('U')
            else:
                moved = enemy.move('down'); print('D')

        tries += 1

def update(plr : Character, enemy : Character):
    get_map(plr, enemy)
    time.sleep(1)
    print('\n')
    print(plr.get_info())

Player = Character(10, 1, {'x':1,'y':1}, 'p')
Enemy = Character(10, 1, {'x':2,'y':2}, 'e')

while True:
    update(Player, Enemy)
    inpt = (input('[?] What would you like to do next?\n[!] Move (-direction) \n[!] Debug (-info)\n[>  ')).lower()
    if 'move' in inpt:
        Player.move(inpt.split('-')[-1])