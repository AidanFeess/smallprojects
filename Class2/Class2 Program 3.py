#####################################################################
# author: Aidan Feess 
# date: 10 April 2024
# description: Program that creates and modifies sellable items, and displays the profit from the items.
#####################################################################
import math

# The SaleItem class has a name, cost and price. All three are provided
# as arguments to the constructor. SaleItem also has a profit function
# that returns the profit that the sale of the item would provide.
# SaleItem also has a applySale function that adjusts the price of the
# item using the percentage provided as an argument to that function.
class SaleItem:
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
############################ MAIN ###################################
########## DO NOT MODIFY ANYTHING BELOW THIS POINT ##################
#####################################################################
# Create 3 items and print them
i1 = SaleItem("shoes", 50, 79.99)
i2 = SaleItem("jeans", 30, 44.99)
i3 = SaleItem("shirt", 20, 29.99)

print("Item\tCost\tPrice\tProfit")
print("-" * 30)
print(f"{i1.name}\t{i1.cost:.2f}\t{i1.price:.2f}\t{i1.profit():.2f}")
print(f"{i2.name}\t{i2.cost:.2f}\t{i2.price:.2f}\t{i2.profit():.2f}")
print(f"{i3.name}\t{i3.cost:.2f}\t{i3.price:.2f}\t{i3.profit():.2f}")
print("-" * 30)

# Try some changes that should be permitted
i1.cost = 30
i2.name = "jorts"
i2.applySale(50)
i3.price = 39.59
i3.applySale(25)

print(f"{i1.name}\t{i1.cost:.2f}\t{i1.price:.2f}\t{i1.profit():.2f}")
print(f"{i2.name}\t{i2.cost:.2f}\t{i2.price:.2f}\t{i2.profit():.2f}")
print(f"{i3.name}\t{i3.cost:.2f}\t{i3.price:.2f}\t{i3.profit():.2f}")
print("-" * 30)

# Try some changes that should NOT be permitted
i1.cost = -20   
i2.price = -2.99
i3.applySale(200)

print(f"{i1.name}\t{i1.cost:.2f}\t{i1.price:.2f}\t{i1.profit():.2f}")
print(f"{i2.name}\t{i2.cost:.2f}\t{i2.price:.2f}\t{i2.profit():.2f}")
print(f"{i3.name}\t{i3.cost:.2f}\t{i3.price:.2f}\t{i3.profit():.2f}")
print("-" * 30)
