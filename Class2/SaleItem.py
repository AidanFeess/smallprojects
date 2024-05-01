#####################################################################
# author: Aidan Feess    
# date: 5/3/2024
# description: Program that defines classes for different types of store items
#####################################################################

# An Item has a name, cost and price, all of which are passed in as
# arguments to its constructor. It has accessors and mutators that carry
# out range checking. It also has profit, applySale, and __str__
# functions that carry out the tasks as described in the assignment
# documentation.
class Item:
    def __init__(self, name, cost, price):
        self.name = name
        self.cost = cost
        self.price = price

    # Create the cost property and setter to check for invalid changes
    @property
    def cost(self):
        return self._cost
    @cost.setter
    def cost(self, value):
        if value < 0:
            value = 0
        self._cost = value

    # Create the price property and setter to check for invalid changes
    @property
    def price(self):
        return self._price
    @price.setter
    def price(self, value):
        if value < 0:
            value = 0
        self._price = value

    # Calculate the profit gained from selling an item
    def profit(self):
        return self.price - self.cost
    
    # Apply a sale based on a percentage
    def applySale(self, priceMod):
        self.price -= self.price * (priceMod / 100)

    # string overload function
    def __str__(self):
        return f"{self.name}\t{self.cost:.2f}\t{self.price:.2f}"
#####################################################################
# A Clothing is an Item. In addition to name, cost and price, it also
# has a brand, and size. It receives all 5 pieces of information as
# arguments to its constructor. It overloads the __str__ function and
# also has appropriate accessors and mutators.
class Clothing(Item):
    def __init__(self, name, brand, cost, price, size):
        super().__init__(name, cost, price)
        self.brand = brand
        self.size = size

    @property
    def brand(self):
        return self._brand
    @brand.setter
    def brand(self, value):
        self._brand = value

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self, value):
        self._size = value if value > 0 else None

    def __str__(self):
        return f"{self.name}\t{self.cost:.2f}\t{self.price:.2f}\t|{self.brand}\tsize:{self.size}"

#####################################################################
# A Food is an Item. In addition to name, cost and price, it also has a
# shelfLife. It only receives name, cost and price as arguments to its
# constructor. It sets all objects created to have a shelfLife of 7 by
# default. It also overloads the __str__ function.
class Food(Item):
    def __init__(self, name, cost, price):
        super().__init__(name, cost, price)
        self.shelfLife = 7

    @property
    def shelfLife(self):
        return self._shelfLife
    @shelfLife.setter
    def shelfLife(self, value):
        self._shelfLife = value if value > 0 else None

    def __str__(self):
        return f"{self.name}\t{self.cost:.2f}\t{self.price:.2f}\t|expires in {self.shelfLife} days"

#####################################################################
# A Shoe is a Clothing. It only receives cost, price and size as
# arguments to its constructor. It sets all Shoe objects to have a name
# of "Sneakers" and brand of "Nike" by default.
class Shoe(Clothing):
    def __init__(self, cost, price, size):
        super().__init__("Crocs", "Nike", cost, price, size)
        
#####################################################################
# A Chips is a Food. It does not receive any arguments for its
# constructor. It sets the name, cost, price and shelfLife to be "Lays",
# 2, 3.50 and 21 respectively.
class Chips(Food):
    def __init__(self):
        super().__init__("Lays", 2, 3.50)
        self.shelfLife = 21

#####################################################################