def GetIncome():
    return float(input("What was your total income for this tax year?: "))
# Function to get the user's income. Returns a float value

def GetMarriageStatus():
    return input("Are you married? [y/n]: ") == "y"
# Function to get the user's marital status. Returns true or false

def GetMarriageLength():
    return int(input("How long have you been married?: "))
# Function to get how long a user has been married for. Returns an integer value

def GetElevation():
    return int(input("Is the elevation of your home address below - 1, at - 2, above - 3 sea level? [1/2/3]: "))
# Function to find out if a user's location is at, above, or below sea level. Returns an integer indicating the answer

def GetBedrooms():
    return int(input("How many bedrooms do you have?: "))
# Function to get the amount of bedrooms a user has. Returns an integer value

## MAIN ##

Income = GetIncome()
MarriageStatus = GetMarriageStatus()
MarriageLength = 0
Bedrooms = 0

Tax = 0
if Income < 10000:
    Tax = Income * 0.023
elif Income >= 10000 and Income <= 50000:
    Tax = Income * 0.045
elif Income > 50000:
    Tax = Income * 0.061

if MarriageStatus:
        MarriageLength = GetMarriageLength()
        Tax -= 1.62 * MarriageLength

Elevation = GetElevation()

if Elevation == 1:
    Tax += 18.32
elif Elevation == 2:
    Tax += Income * 0.016
elif Elevation == 3:
    Bedrooms = GetBedrooms()

print(f"The total tax for {Income} is : {Tax}")