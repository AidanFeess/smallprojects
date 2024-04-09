from DeathFunc import death
from random import choice
import random
import numpy
###################################################################### PLAYER VARIABLES
Gold = 0
Inventory = []

MaxHealth = 100
Health = 100

Hunger = 10
MaxHunger = 10

MaxThirst = 10
Thirst = 10
# Amount of hunger/thirst lost per turn
HungerLoss = -1
ThirstLoss = -2
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

    def DealDamage(self, enemy):
        enemy.TakeDamage(self.damage)

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
        
    def Use(self):
        Health = numpy.clip(Health + self.healing, 0, MaxHealth)
        Hunger = numpy.clip(Hunger + self.hunger, 0, MaxHunger)
        Thirst = numpy.clip(Thirst + self.thirst, 0, MaxThirst)
        Inventory.remove(self)
        
class Character:
    def __init__(self, name, health, resistances, level):
        self.name = name
        self.health = health
        self.resistances = resistances
        self.level = level
        self.drops = {}

    def TakeDamage(self, damage):
        self.health -= damage

    def DealDamage(self, enemy, damage):
        enemy.TakeDamage(damage)

class Room:
# the constructor
    def __init__(self, name : str, isExit : bool, Position : tuple):
        # rooms have a name, exits (e.g., south), exit locations
        # (e.g., to the south is room n), items (e.g., table), item
        # descriptions (for each item), and grabbables (things that
        # can be taken into inventory)
        self.name = name
        self.isExit = isExit
        self.items = []
        self.Position = Position
    
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
    # Adding and removing items
    def addItem(self, item):
        # Create an item object with given parameters
        self._items.append(item)
    def delItem(self, item):
        self._items.remove(item)
    # returns a string description of the room
    def __str__(self):
    # first, the room name
        s = "You are in {}.\n".format(self.name)
    # next, the items in the room
        s += "You see: "
        for item in self.items:
            s += item.name + " "
            s += "\n"
        return s

# List of room flavor descriptors
RoomDescriptors = ["grand", "great", "dark", "dim"]
RoomCeilingHeight = ["low", "high", "normal"]
RoomMaterialState = [" pristine", " desolate", "n average"]

# List of items
OtherItems = [Item("Used 2006 Toyota Corolla", "A used 2006 model Toyota Corolla!", 0, False)]
WeaponItems = [Weapon("debugsword", "A developer's debug sword!", 100, 10)]
FoodItems = [Food("debugmeat", "A developer's debug meat!", 100, -25, 1, 1)]

# List of enemies
###################################################################### INTERACTION FUNCTIONS
# creates the rooms
def createRooms():
    # Randomly generate rooms
    global currentRoom
    MapSize = (3, 3)
    Rooms = []
    # Create a room for each X and Y
    for y in range(MapSize[1]):
        Row = []
        for x in range(MapSize[0]):
            RoomName = "a "
            RoomName += f"{choice(RoomDescriptors)} room with a {choice(RoomCeilingHeight)} ceiling. It appears to be in a{choice(RoomMaterialState)} condition"
            NewRoom = Room(RoomName, False, (x, y))
            # Add a random number of random foods
            for _ in range(random.randint(0, 2)):
                NewRoom.addItem(choice(FoodItems))
            # Add a random number of random weapons
            for _ in range(random.randint(0, 1)):
                NewRoom.addItem(choice(WeaponItems))
            
            Row.append(NewRoom)
        Rooms.append(Row)

    currentRoom = Rooms[0][0]
    
    
    
###################################################################### GAME
createRooms() # add the rooms to the game
# play forever (well, at least until the player dies or asks to quit)
while (True):
# set the status so the player has situational awareness
# the status has room and inventory information
    status = "{}\nYou are carrying: {}\n".format(currentRoom, ''.join([x.name + " " for x in Inventory]))
# if the current room is None, then the player is dead
# this only happens if the player goes south when in room 4
    if (currentRoom == None):
        status = "You are dead."
    # display the status
    print("========================================================")
    print(status)
    # if the current room is None (and the player is dead), exit the
    # game
    if (currentRoom == None):
        death()
        break
    # prompt for player input
    # the game supports a simple language of <verb> <noun>
    # valid verbs are go, look, and take
    # valid nouns depend on the verb
    action = input("What to do? ")
    # set the user's input to lowercase to make it easier to compare
    # the verb and noun to known values
    action = action.lower()
    # exit the game if the player wants to leave (supports quit,
    # exit, and bye)
    if (action == "quit" or action == "exit" or action == "bye"):
        break
    # set a default response
    response = "I don't understand. Try verb noun. Valid verbs are go, look, and take"
    words = action.split()
    if (len(words) == 2):
    # isolate the verb and noun
        verb = words[0]
        noun = words[1]
        if (verb == "look"):
            response = "I don't see that item."
            for i in range(len(currentRoom.items)):
                if (noun == currentRoom.items[i].name):
                    response = currentRoom.items[i].description
                    response += " It's grabbable." if item.grabbable else " It's not grabbable."
                    break
        elif (verb == "take"):
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
        elif verb == "eat":
            response = "I don't have that item."
            for item in Inventory:
                if noun == item.name and item.__name__ == "Food":
                    item.Use()
                    response = "Food eaten."
                    break
                elif not item.__name__ == "Food":
                    response = "I can't eat that!"
                    break
    print("\n{}".format(response))