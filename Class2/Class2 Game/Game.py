from DeathFunc import death
from random import choice
from time import sleep
import random
import numpy
###################################################################### PLAYER VARIABLES
Gold = 0
EquippedWeapon = None
Inventory = []

MovedRooms = False
#DebugMap = [["X", "0", "0"],
#            ["0", "0", "0"],
#            ["0", "0", "0"]]

WonGame = False

Score = 0

MaxHealth = 100
Health = 100

Hunger = 10
MaxHunger = 10

MaxThirst = 10
Thirst = 10
# Amount of hunger/thirst lost per turn
HungerLoss = -1
ThirstLoss = -2
###################################################################### EXTRA VARIABLES
RoundPassed = False
###################################################################### CLASSES

class Item:
    def __init__(self, name : str, description : str, worth : int, grabbable : bool):
        self.name = name
        self.description = description
        self.worth = worth
        self.grabbable = grabbable

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        return self._description
    @description.setter
    def description(self, value):
        self._description = value

    @property
    def worth(self):
        return self._worth
    @worth.setter
    def worth(self, value):
        self._worth = value

    @property
    def grabbable(self):
        return self._grabbable
    @grabbable.setter
    def grabbable(self, value):
        self._grabbable = value

    @property
    def edible(self):
        return self._edible
    @edible.setter
    def edible(self, value):
        self._edible = value

class Weapon(Item):
    def __init__(self, name : str, description : str, worth : int, damage : int):
        self.name = name
        self.description = description
        self.worth = worth
        # Weapons are always grabbable
        self.grabbable = True

        self.damage = damage

    def DealDamage(self, enemy, Score):
        newScore = enemy.TakeDamage(self.damage, Score)
        healthpercent = int((enemy.health / enemy.maxhealth) * 10)
        healthbar = "#" * healthpercent + " " * (10 - healthpercent)
        return f"Dealt {self.damage} damage to the {enemy.name}!\nHP Remaining:[{healthbar}]\n" if enemy.health > 0 else f"Killed the {enemy.name}!", newScore

    def Examine(self):
        return (f"The item is worth {self.worth} gold. It deals {self.damage} damage.")

class Food(Item):
    def __init__(self, name : str, description : str, worth : int, healing : int, hunger : int, thirst : int):
        self.name = name
        self.description = description
        self.worth = worth
        # Food is always grabbable
        self.grabbable = True
        
        self.healing = healing
        self.hunger = hunger
        self.thirst = thirst
        
    def Use(self, HP, Hunger, Thirst):
        HP = numpy.clip(Health + self.healing, 0, MaxHealth)
        Hunger = numpy.clip(Hunger + self.hunger, 0, MaxHunger)
        Thirst = numpy.clip(Thirst + self.thirst, 0, MaxThirst)
        Inventory.remove(self)
        g = "gained"
        l = "lost"
        print(f"You {g if self.healing >= 0 else l} {abs(self.healing)} health!")
        print(f"You {g if self.hunger >= 0 else l} {abs(self.hunger)} hunger!")
        print(f"You {g if self.thirst >= 0 else l} {abs(self.thirst)} thirst!")
        return HP, Hunger, Thirst
        
class Character:
    def __init__(self, name, health, resistances, level):
        self.name = name
        self.health = health
        self.maxhealth = health
        self.resistances = resistances
        self.level = level
        self.drops = {}

class Enemy(Character):
    def __init__(self, name, health, resistances, level, score_worth, attack_power):
        self.name = name
        self.health = health
        self.maxhealth = health
        self.resistances = resistances
        self.level = level
        self.drops = {}
        self.attack_power = attack_power
        self.score_worth = score_worth + int(self.maxhealth/3) + int(self.level*10) + int(self.attack_power*1.5)

    @property
    def attack_power(self):
        return self._attack_power
    @attack_power.setter
    def attack_power(self, value):
        self._attack_power = value

    def TakeDamage(self, damage, Score):
        self.health -= damage
        if self.health <= 0:
            currentRoom.delEnemy(self)
            return self.score_worth + Score
        return Score

    def Attack(self, health):
        NewHealth = health - self.attack_power
        print(f"{self.name} attacked and dealt {self.attack_power} damage!\nPlayer HP: {NewHealth}")
        return NewHealth

class Room:
# the constructor
    def __init__(self, name : str, isExit : bool, Position : tuple):
        self.name = name
        self.isExit = isExit
        self.Position = Position

        self.items = []
        self.Enemies = []

    
    # getters and setters for the instance variables
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, value):
        self._name = value
    @property
    def isExit(self):
        return self._isExit
    @isExit.setter
    def isExit(self, value):
        self._isExit = value
    @property
    def items(self):
        return self._items
    @items.setter
    def items(self, value):
        self._items = value
    @property
    def itemDescriptions(self):
        return self._itemDescriptions
    @itemDescriptions.setter
    def itemDescriptions(self, value):
        self._itemDescriptions = value
    @property
    def Position(self):
        return self._Position
    @Position.setter
    def Position(self, value):
        self._Position = value

    @property
    def Enemies(self):
        return self._Enemies
    @Enemies.setter
    def Enemies(self, value):
        self._Enemies = value

    # Adding and removing items
    def addItem(self, item):
        self._items.append(item)
    def delItem(self, item):
        self._items.remove(item)

    # Adding and removing enemies
    def addEnemy(self, enemy):
        self._Enemies.append(enemy)
    def delEnemy(self, enemy):
        self._Enemies.remove(enemy)

    # returns a string description of the room
    def __str__(self):
        # first, the room name
        PlayerStatus = f"You are in {self.name}.\n"
        # next, the items in the room
        repeatObjects = {}
        for item in self.items:
            if not item.name in repeatObjects:
                repeatObjects[item.name] = 1
            else:
                repeatObjects[item.name] += 1
        # Correctly format the objects in the room so that it appears in a more readable format
        if len(repeatObjects) > 0:
            PlayerStatus += "You see: "
            PlayerStatus += "".join([f"{repeatObjects[x]} {x}\n" if repeatObjects[x] > 1 else f"a {x}\n" for x in repeatObjects])
        # finally, the enemies in the room
        if len(self.Enemies) > 0:
            PlayerStatus += f"\nYou're about to be attacked by: "
            for enemy in self.Enemies:
                PlayerStatus += enemy.name + " \n"
        return PlayerStatus

# List of room flavor descriptors
RoomDescriptors = ["grand", "great", "dark", "dim"]
RoomCeilingHeight = ["low", "high", "normal"]
RoomMaterialState = [" pristine", " desolate", "n average"]

# Other Item Names
OtherNames = [
    "2009 Toyota Corolla",
    "couple unboxed boxing boxes",
    "Pair of gloves",
    "Bunch of crates of mysterious origin",
    "House, fit for ants",
    "Just a shadow.",
    "Torch",
    "Empty chest"
]
# Weapon Item Names
WeaponNames = [
    "Sword",
    "Spear",
    "Axe",
    "Bow",
    "Crossbow",
    "Mace",
    "Dagger",
    "Halberd",
    "Warhammer",
    "Flail",
    "Rapier",
    "Longbow",
    "Katana",
    "Morningstar",
    "Scimitar",
    "Trident",
    "Javelin",
    "Battleaxe",
    "War scythe",
    "Sling",
    "Nuclear-Missile-Launcher",
    "AK-47",
    "Glock-17",
    "Entire_M1_Abrams_tank",
    "Watergun",
    "Pineneedle"
]
# Food Item Names
FoodNames = [
    "Apple",
    "Banana",
    "Orange",
    "Strawberry",
    "Blueberry",
    "Grapes",
    "Watermelon",
    "Pineapple",
    "Kiwi",
    "Mango",
    "Peach",
    "Pear",
    "Cherry",
    "Grapefruit",
    "Plum",
    "Apricot",
    "Pomegranate",
    "Lemon",
    "Lime",
    "Cantaloupe",
    "Beef",
    "Chicken",
    "Pork",
    "Turkey",
    "Lamb",
    "Duck",
    "Salmon",
    "Tuna",
    "Shrimp",
    "Crab",
    "Lobster",
    "Sausage",
    "Bacon",
    "Ham",
    "Venison",
    "Bison",
    "Trout",
    "Cod",
    "Sardine",
    "Mackerel"
]
# Enemy names
EnemyNames = [
    "Goblin",
    "Skeleton",
    "Orc",
    "Dragon",
    "Troll",
    "Witch",
    "Zombie",
    "Werewolf",
    "Ghost",
    "Demon",
    "Giant",
    "Slime",
    "Kobold",
    "Beholder",
    "Mimic",
    "Jeff",
    "A particularly evil ant",
    "A gigantic cow that wants to turn you into food",
    "A tree with evil intentions",
    "3 Bushes (of evil)"
]

# List of items
OtherItems = [
    Item(choice(OtherNames), "An interesting object!", 0, False) for x in range(15)
    ]
WeaponItems = [
    Weapon(choice(WeaponNames), "A mighty weapon!", random.randint(100, 500), random.randint(1, 100)) for x in range(30)
    ]
FoodItems = [
    Food(choice(FoodNames), "A hearty meal!", random.randint(1, 100), random.randint(-5, 25), random.randint(1, 4), random.randint(1, 6)) for x in range(30)
    ]

# List of enemies
EnemyList = [
    Enemy(name=choice(EnemyNames),health=random.randint(1, 150),resistances=None,level=1,score_worth=10,attack_power=random.randint(1, 25)) for x in range(20)
]
###################################################################### INTERACTION FUNCTIONS
# creates the rooms
def createRooms():
    # Randomly generate rooms
    global currentRoom
    global MapSize 
    global Rooms

    MapSize = (random.randint(3, 6), random.randint(3, 6))
    Rooms = []
    # Create a room for each X and Y
    for y in range(MapSize[1]):
        Row = []
        for x in range(MapSize[0]):
            RoomName = "a "
            RoomName += f"{choice(RoomDescriptors)} room with a {choice(RoomCeilingHeight)} ceiling. It appears to be in a{choice(RoomMaterialState)} condition"
            NewRoom = Room(RoomName, False, (x, y))
            # Add a random number of random foods
            for _ in range(random.randint(1, 4)):
                NewRoom.addItem(choice(FoodItems))
            # Add a random number of random weapons
            for _ in range(random.randint(0, 1)):
                NewRoom.addItem(choice(WeaponItems))
            # Add a random number of objects
            for _ in range(random.randint(2, 6)):
                NewRoom.addItem(choice(OtherItems))

            for _ in range(random.randint(0, 2)):
                NewRoom.addEnemy(choice(EnemyList))
            
            Row.append(NewRoom)
        Rooms.append(Row)

    currentRoom = Rooms[0][0]
    # Add the boss to the farthest room
    Rooms[MapSize[0]-1][MapSize[1]-1].addEnemy(Enemy(name="Boss"+choice(EnemyNames),health=random.randint(150,350), resistances=None,level=5,score_worth=100,attack_power=random.randint(12,37)))

def CalculateScore():
    return Gold + Score + sum([item.worth for item in Inventory])

def OnDeath():
    death()
    print(f"Your final score:\nGold: {Gold}\nInventory: {[x.name for x in Inventory]}\nScore: {CalculateScore()}")

def OnVictory():
    print("YOU WON THE GAME!!!")
    print(f"Your final score:\nGold: {Gold}\nInventory: {[x.name for x in Inventory]}\nScore: {CalculateScore()}")

###################################################################### GAME
createRooms() # add the rooms to the game
# play forever (well, at least until the player dies or asks to quit)
while (True):
    # Set the state back to normal
    MovedRooms = False
    RoundPassed = False
    # set the status so the player has situational awareness
    # the status has room and inventory information
    status = "{}".format(currentRoom)
    if len(Inventory) > 0:
        repeatObjects = {}
        for item in Inventory:
            if not item.name in repeatObjects:
                repeatObjects[item.name] = 1
            else:
                repeatObjects[item.name] += 1
        currentItems = "".join([f"{repeatObjects[x]} {x}\n" if repeatObjects[x] > 1 else f"a {x}\n" for x in repeatObjects])
        status += f"\nYou are carrying: {currentItems}"
    status += f"\nYou have {Hunger} hunger left\nYou have {Thirst} thirst left."
    # status = "{}\nYou are carrying: {}\n".format(currentRoom, ''.join([x.name + " " for x in Inventory]))
    # if the current room is None, then the player is dead
    if Hunger == 0:
        Health -= 10
        status += "\nYou are starving, you will lose 10 hp!"
    if Thirst == 0:
        Health -= 10
        status += "\nYou are dehydrated, you will lose 10 hp!"
    if currentRoom == None or Health <= 0:
        status = "You are dead."
    elif WonGame:
        status = "You won!"
    # display the status
    print("="*56)
    print(status)
    print("="*56)
    # if the current room is None (and the player is dead), exit the
    # game
    if currentRoom == None or Health <= 0:
        OnDeath()
        break
    elif WonGame:
        OnVictory()
        break
    # prompt for player input
    # the game supports a simple language of <verb> <noun>
    # valid verbs are go, look, and take
    # valid nouns depend on the verb
    actions = [
        "look",
        "take",
        "eat",
        "examine",
        "attack",
        "equip",
        "move",
    ]
    action_list = "".join([x + '\n' for x in actions])
    action = input(f"What to do? \n{action_list}")
    # set the user's input to lowercase to make it easier to compare
    # the verb and noun to known values
    # exit the game if the player wants to leave (supports quit,
    # exit, and bye)
    if (action == "quit" or action == "exit" or action == "bye"):
        OnDeath()
        break
    # set a default response
    response = "I don't understand."
    words = action.split()
    if (len(words) == 2):
    # isolate the verb and noun
        verb = words[0]
        noun = words[1]
        # Switch statement is more efficient and cleaner than if/else statements
        match verb:
            case "look":
                response = "I don't see that item."
                for i in range(len(currentRoom.items)):
                    if (noun == currentRoom.items[i].name):
                        response = currentRoom.items[i].description
                        response += " It's grabbable." if currentRoom.items[i].grabbable else " It's not grabbable."
                        if type(currentRoom.items[i]).__name__ == "Food":
                            print(f"The {currentRoom.items[i].name} will restore {currentRoom.items[i].hunger} hunger and {currentRoom.items[i].thirst} thirst.")
                        break
            case "take":
                response = "I don't see that item."
                for item in currentRoom.items:
                    if noun == item.name and item.grabbable:
                        Inventory.append(item)
                        currentRoom.delItem(item)
                        response = "Item grabbed."
                        break
                    elif not item.grabbable:
                        response = "That item isn't grabbable."
                        break
            case "eat":
                response = "I don't have that item."
                for item in Inventory:
                    if noun == item.name and type(item).__name__ == "Food":
                        RoundPassed = True
                        Health, Hunger, Thirst = item.Use(Health, Hunger, Thirst)
                        response = "Food eaten."
                        break
                    elif not type(item).__name__ == "Food":
                        response = "I can't eat that!"
            case "examine":
                response = "I can't examine this. Did you remember to pick it up first?"
                for item in Inventory:
                    if noun == item.name and type(item).__name__ == "Weapon":
                        response = item.Examine()
                        break
                    elif not type(item).__name__ == "Weapon":
                        response = "I can't examine this."
            case "attack":
                # Save on efficiency by not allowing a player to attack without a weapon
                if EquippedWeapon == None: response = "I don't have a weapon!"
                else:
                    RoundPassed = True
                    response = "I couldn't find that enemy."
                    for enemy in currentRoom.Enemies:
                        if noun == enemy.name:
                            response, Score = EquippedWeapon.DealDamage(enemy, Score)
                            if enemy.health <= 0 and str.find(enemy.name, "Boss"):
                                WonGame = True
                                print("You won the game!")
                            break
            case "equip":
                for item in Inventory:
                    if type(item).__name__ == "Weapon":
                        if noun == item.name:
                            EquippedWeapon = item
                            response = f"Equipped {item.name}!"
                            break
            case "move":
                response = "Couldn't find a room that direction! Did I say left, right, up, or down?"
                try:
                    if noun == "right" and currentRoom.Position[0]+1 <= MapSize[0]:
                        #DebugMap[currentRoom.Position[1]][currentRoom.Position[0]] = "0"
                        #DebugMap[currentRoom.Position[1]][currentRoom.Position[0]+1] = "X"
                        currentRoom = Rooms[currentRoom.Position[1]][currentRoom.Position[0]+1]
                        response = "Went right!"
                        MovedRooms = True

                    elif noun == "left" and currentRoom.Position[0]-1 >= 0:
                        currentRoom = Rooms[currentRoom.Position[1]][currentRoom.Position[0]-1]
                        response = "Went left!"
                        MovedRooms = True

                    elif noun == "up" and currentRoom.Position[1]-1 >= 0:
                        currentRoom = Rooms[currentRoom.Position[1]-1][currentRoom.Position[0]]
                        response = "Went up!"
                        MovedRooms = True

                    elif noun == "down" and currentRoom.Position[1] <= MapSize[1]:
                        currentRoom = Rooms[currentRoom.Position[1]+1][currentRoom.Position[0]]
                        response = "Went down!"
                        MovedRooms = True
                except:
                    pass
    # Debug menu
    elif len(words) >= 3:
        if words[0] == "debug":
            verb = words[1]
            noun = words[2]
            amount = 1
            try:
                amount = int(words[3]) if int(words[3]) > 1 else 1
            except:
                pass
            match verb:
                case "place":
                    response = "No such item."
                    PlaceItem = None

                    # Check each list for an item matching the given name
                    for item in OtherItems:
                        if item.name == noun:
                            response = "Placed the item."
                            PlaceItem = item
                            break
                    
                    for item in FoodItems:
                        if item.name == noun:
                            response = "Placed the item."
                            PlaceItem = item
                            break

                    for item in WeaponItems:
                        if item.name == noun:
                            response = "Placed the item."
                            PlaceItem = item
                            break

                    # Place the items as many times as indicated
                    if PlaceItem: 
                        for x in range(amount):
                            currentRoom.addItem(PlaceItem)
                case "spawn":
                    for enemy in EnemyList:
                        if enemy.Name == noun:
                            for x in range(amount):
                                currentRoom.addEnemy(enemy)
                case "tp":
                    try:
                        currentRoom = Rooms[noun.split(":")[0]][noun.split(":")[1]]
                        response = "Teleported."
                    except:
                        response = "Failed to teleport."
                        
    # Turn is over here
    print(f"\n{response}\n")
    sleep(1)
    if MovedRooms or RoundPassed:
        Hunger += HungerLoss if Hunger + HungerLoss >= 0 else 0
        Thirst += ThirstLoss if Thirst + ThirstLoss >= 0 else 0
    if len(currentRoom.Enemies) > 0 and not MovedRooms and RoundPassed:
        print("\nThe enemies will now attack!\n")
        for enemy in currentRoom.Enemies:
            sleep(.3)
            Health = enemy.Attack(Health)
        sleep(2)