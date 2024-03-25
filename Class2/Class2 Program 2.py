
#####################################################################
# author: Aidan Feess
# date: 03 / 27 / 2024
# description: Program that calculates the frequency of population ranges in the given city population file
#####################################################################
# A function to read the contents of a text file. It receives a string
# representing the name of the file, and returns a list containing all
# the lines in the file. This function is also in charge of ensuring
# that the filename provided actually exists. If the file does not
# exist, the function prints an error message and prompts the user for a
# new file name.

def ReadContents(FileName: str) -> list:
    try: return [l.strip("\n").strip().lower() for l in open(FileName, "r").readlines()]
    except: return ReadContents(input("The file name you specified does not exist.\nEnter file name again: "))
    
# A function that prompts the user for a piece of information and
# returns that result to the calling statement. It receives a string
# describing the information that is required and uses that string to
# create the question that the user is asked.
    
def GetInfo(Question: str):
    return input(f"What population do you want as {Question}? ")

# A function that receives four pieces of information i.e. the minimum,
# maximum, and step sizes of the population table to be created, as well
# as the list that contains all the population values to be parsed. It
# then creates and returns a list containing as many elements as necessary
# to store a result for each required population range. Each element in
# that resulting list contains the number of cities in the original
# population list that have values in that range.

def CreateList(Min: int, Max: int, StepSize: int, PopList: list):
    # we create a dictionary mapping the step to an integer so it can be accessed later
    RetList = {Step:0 for Step in range(Min+StepSize, Max+StepSize, StepSize)}
    Step = StepSize
    while Step <= Max:
        for line in PopList:
            if int(line) < Step and int(line) >= Step - StepSize:
                RetList[Step] += 1
        Step += StepSize
    return RetList

####################### MAIN ####################################
# ask the user for the file name
# read the file and store the results in a list.
PopList = ReadContents(input("What is the name of the file with the population information? "))
# print out the information showing the number of cities in the original
# file.
print(f"This file has {len(PopList)} cities in it")
# Prompt the user for the minimum, maximum and interval populations.
# create a list containing the frequencies of those population ranges.
Minimum = int(GetInfo("minimum"))
Maximum = int(GetInfo("maximum"))
Interval = int(GetInfo("interval"))
FreqList = CreateList(Minimum, Maximum, Interval, PopList)
# print the table showing the population ranges and their frequency in
# the original file.
print("----------------------------------------")
print("Population                   Frequency")
for Step in range(Minimum+Interval, Maximum+Interval, Interval):
    print(f"{Step-Interval}-{Step}                  {FreqList[Step]}")
print("----------------------------------------")