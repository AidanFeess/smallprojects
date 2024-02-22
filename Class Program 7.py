####################################################################
# author: Aidan Feess
# date: 2 / 22 / 2024
# description: program that keeps track of how much a store is selling and how much they're making from each item sold
####################################################################
def Introduction():
    print("------------------------------------------------------------")
    print("Welcome to Cyber Groceries (v2)")
    print("------------------------------------------------------------")
# A function to print out the introduction to the program. It does not
# take any arguments or return any results.
def GetUserItemCount():
    return int(input("How many items does the store carry? "))
# A function that prompts the user for the number of items that the
# store carries. It does not take any arguments but it returns the
# number of items to the calling statement.
def GetUserItems(NumberOfItems): # A better way of doing this is just creating a dict with item = price but instructions say list so
    return [input(f"What is item number {x}? ") for x in range(1, NumberOfItems+1)]
# A function that creates a list of item names by repeatedly prompting
# the user for item names. It takes an argument representing the
# number of items, and returns a single list containing the item
# names.
def GetUserPrices(ItemNames):
    return [float(input(f"What is the price of {item}? ")) for item in ItemNames]
# A function that creates a list of prices by repeatedly prompting the
# user for the prices for different items. It takes the list of
# item names as a single argument, and then returns a single list
# containing the prices for each of the items.
def GetUserItemsSold(ItemNames):
    return [float(input(f"How many units of {item} were sold today? ")) for item in ItemNames]
# A function that creates a list that contains the number of units that
# were sold of each of the items in the store. It takes a single
# argument i.e. the list of item names, and after repeatedly asking the
# user for item amounts, returns the list of item units that were sold.
def PrintSummaryTable(ItemNames, ItemPrices, ItemsSold):
    print("------------------------------------------------------------")
    print("Item     Unit Price      Number      Total Cost")
    print("------------------------------------------------------------")
    for item in range(len(ItemNames)):
        print(f"{ItemNames[item]}       ${ItemPrices[item]}     {ItemsSold[item]}       ${round(ItemPrices[item]*ItemsSold[item], 2)}")
    print("============================================================")
# A function that prints out the summary table. It takes 3 arguments
# i.e. the list containing the item names, the list containing the item
# prices, and the list containing the item amounts. It uses these 3
# arguments to create a 4 column table that contains the name, unit
# price, number of units sold, and total amount made from that unit for
# each item. It does not return any arguments.
    
######################### MAIN #####################################
# In the space below, use the functions defined above to solve the
# outlined problem.
####################################################################
Introduction()
# print out the introduction
ItemCount = GetUserItemCount()
Items = GetUserItems(ItemCount)
ItemPrices = GetUserPrices(Items)
ItemsSold = GetUserItemsSold(Items)
# Prompt the user for the appropriate information
PrintSummaryTable(Items, ItemPrices, ItemsSold)
# Print out items and their costs.