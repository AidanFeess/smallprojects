####################################################################
# author: Aidan Feess
# date: 2/19/2024
# description: 
####################################################################
def Introduction():
    print("------------------------------------------------------------\nWelcome to Cyber Groceries\n------------------------------------------------------------")
# A function to print out the introduction to the program. It does not
# take any arguments or return any results.
def GetUserItemCount():
    return int(input("How many items is the customer buying? "))
# A function that prompts the user for the number of items that the
# customer is buying. It does not take any arguments but it returns the
# number of items being bought to the calling statement.
def GetUserItems(NumberOfItems): # A better way of doing this is just creating a dict with item = price but instructions say list so
    return [input(f"What is item number {x}? ") for x in range(1, NumberOfItems+1)]
# A function that creates a list of item names by repeatedly prompting
# the user for product names. It takes an argument representing the
# number of items, and returns a single list containing the product
# names.
def GetUserPrices(ItemNames):
    return [float(input(f"What is the price of {item}? ")) for item in ItemNames]
# A function that creates a list of prices by repeatedly prompting the
# user for the prices for different products. It takes the list of
# product names as a single argument, and then returns a single list
# containing the prices for each of the products.
def ComputeItemPrices(ItemNames, ItemPrices):
    TotalPrice = sum(ItemPrices)
    Cheapest = list.index(ItemPrices, min(ItemPrices))
    Expensive = list.index(ItemPrices, max(ItemPrices))
    return TotalPrice, ItemNames[Cheapest], ItemNames[Expensive]
# A function that takes a list of items and prices and returns the 
# both the cheapest and most expensive item, and also calculates 
# the total price of all items

######################### MAIN #####################################
# In the space below, use the functions defined above to solve the
# outlined problem.
####################################################################
Introduction()
# print out the introduction
ItemCount = GetUserItemCount()
Items = GetUserItems(ItemCount)
Prices = GetUserPrices(Items)
# Prompt the user for the appropriate information
print("------------------------------------------------------------")
print(f"Items = {Items}")
print(f"Prices = {Prices}")
print("------------------------------------------------------------")
# Print out items and their costs.
# Figure out what the cheapest and most expensive items are as well as
# what the total cost would be.
ItemDetails = ComputeItemPrices(Items, Prices)
print(f"The cheapest item is {ItemDetails[1]}\nThe most expensive item is {ItemDetails[2]}\nThe total cost is {ItemDetails[0]}")
print("============================================================")
# Print out the information on cheapest, most expensive and total cost.