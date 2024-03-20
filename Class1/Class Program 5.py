##########################################################################
# name: Aidan Feess
# date: 02 / 05 / 2024
# description: Program that compares the population change of two countries
#########################################################################
# A function that prints out the introduction to the program. It doesn't
# take any arguments and does not return any results.
def Introduction():
    print("This program will compare the populations of two different countries over time")

# A function that prompts the user for the name of the country. It takes
# in a number that is used in the prompt as an argument. It then returns
# the name of the country.
def GetCountryName(num):
    return input(f"What is the name of Country #{num}: ")

# A function that prompts the user for the current population of a
# country. It takes the name of the country as an argument, and then
# returns the resulting population. The function also carries out range
# checking to make sure the value inputed by the user is valid (i.e. not
# negative)
def GetPopulation(CountryName):
    try:
        Population = int(input(f"What is the current population of {CountryName}? "))
        if Population < 0:
            print("Populations can only be non-negative whole numbers.")
            return GetPopulation(CountryName)
    except:
        print("Populations can only be non-negative whole numbers.")
        return GetPopulation(CountryName)
    return Population

# A function that prompts the user for the population growth rate of a
# country. It takes in the name of the country as an argument and then
# returns a value growth rate. It also carries out range checking to
# make sure that the result is not an unrealistic growth rate i.e. rate
# should be between -5 and 10 inclusive.
def GetPopGrowth(CountryName):
    try:
        GrowthRate = float(input(f"What is the annual population growth rate of {CountryName}? "))
        if GrowthRate < -5 or GrowthRate > 10:
            print("Growth rate must be an integer between -5 and 10, inclusive.")
            return GetPopGrowth(CountryName)
    except:
        print("Growth rate must be an integer between -5 and 10, inclusive.")
        return GetPopGrowth(CountryName)
    return GrowthRate

# A function that prompts the user for the number of years to show in
# the resulting table. The function doesn't take any arguments but
# returns a result. It is also in charge of range checking to make sure
# that the number of years is not less than 1.
def GetTableSize():
    Years = int(input("How many years of comparison should the table show? "))
    if Years < 1: print("You must enter a value >= 1"); return GetTableSize()
    return Years

# A function that prompts the user for the duration of the interval in
# the table i.e. how many years between each successive row of the
# resulting table. It doesn't take any arguments and does range checking
# to make sure that the user doesn't enter a value less than 1.
def GetInterval():
    Interval = int(input("How many years should the intervals be?"))
    if Interval < 1: print("You must enter a value >= 1"); return GetInterval()
    return Interval

# A function that calculates the population given an intial population,
# a growth rate, and the time. It takes 3 arguments (population, growth
# rate and time) and returns the resulting population.
def CalculatePopulation(Pop, GrowthRate, Time):
    return int(Pop * (1 + (GrowthRate / 100)) ** Time)

# A function to print out the header of the table. It takes two
# arguments i.e. the country names, and then prints out the formatting
# lines as well as the first row seen at the top of the table.
def PrintHeader(Country1, Country2):
    print(f"--------------------------------------------------\nYears    {Country1}     {Country2}\n--------------------------------------------------")

# A function to print out the rest of the table row by row. It receives
# 6 arguments: both country populations, both country rates, the
# duration of the analysis and the interval between each row. It then
# relies on calculate population function to calculate the population
# values for each row and print them out in order.
def PrintTableRow(Population1, Growth1, Population2, Growth2, Duration, Interval):
    print(f"{0}     {Population1:,}       {Population2:,}")
    for i in range(Interval, Duration+Interval, Interval):
        NewPop1 = CalculatePopulation(Population1, Growth1, i)
        NewPop2 = CalculatePopulation(Population2, Growth2, i)
        print(f"{i}     {NewPop1:,}       {NewPop2:,}")
        

############### MAIN ##################################
# print the introduction
Introduction()
# Get the country names
Country1 = GetCountryName(1)
Country2 = GetCountryName(2)
# Get the country initial populations
Pop1 = GetPopulation(Country1)
Pop2 = GetPopulation(Country2)
# get the country population growth rates
Growth1 = GetPopGrowth(Country1)
Growth2 = GetPopGrowth(Country2)
# get the analysis detais e.g. the duration and the interval
Duration = GetTableSize()
Interval = GetInterval()
# Print out the table
PrintHeader(Country1, Country2)
PrintTableRow(Pop1, Growth1, Pop2, Growth2, Duration, Interval)