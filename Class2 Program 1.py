#####################################################################
# author: Aidan Feess
# date: 3 / 20 / 2024
# description:
####################################################################
# A function to read the contents of a text file. It receives a string
# representing the name of the file, and returns a list containing all
# the names in the file. This function is also in charge of ensuring
# that the filename provided actually exists. If the file does not
# exist, the function prints an error message and prompts the user for a
# new file name.

def ReadContents(FileName: str) -> list:
    # works by stripping newline chars and leading/trailing whitespaces, then inserting into list, if it can't do that then it'll just error and try again with new input
    # also makes all text lowercase
    try: return [l.strip("\n").strip().lower() for l in open(FileName, "r").readlines()]
    except: return ReadContents(input("The file name you specified does not exist.\nEnter file name again: "))

# A function that receives two string arguments and returns a boolean
# that represents whether the first string begins with the second
# string.
    
def BeginsWith(String1: str, String2: str) -> bool:
    # probably not the most efficient method
    # works by splitting the original string into multiple, then checking the first string from index 0 to the end of String2 to check if it is a valid string
    if String2 in String1.split(" ")[0][:len(String2)]:
        return True
    return False

# A function that receives two string arguments and returns a boolean
# that represents whether the first string ends with the second string.

def EndsWith(String1: str, String2: str) -> bool:
    if String2 in String1.split(" ")[-1][-len(String2):]:
        return True
    return False

# A function that receives two string arguments and returns a boolean
# that represents whether the first string contains the second string.

def Contains(String1: str, String2: str) -> bool:
    if String2 in String1:
        return True
    return False

# A function that receives two arguments i.e. a list of names, and a
# substring. It then creates a short 3 element list that contains the
# number of times that the substring appears in the list. The first
# element is the number of names in which the substring appears at the
# beginning. The second element in the number of names in which the
# substring appears at the end. The third element in the number of
# names that contain the substring.

def GetNameInformation(NameList: list, Substring: str) -> list:
    # decided to use list comprehension because one liners are fun
    return [len([l for l in NameList if BeginsWith(l, Substring) == True]), len([l for l in NameList if EndsWith(l, Substring) == True]), len([l for l in NameList if Contains(l, Substring) == True])]

######################## MAIN #####################################
# prompt the user for the file name
FileName = input("What file do you want to open? ")
# store the names in the file in a list
NameList = ReadContents(FileName)
# print out the number of names in the list
print(f"the file has {len(NameList)} names in it")
# prompt the user for the substring they want to search for
SearchName = input("What name (or substring) are you interested in searching for? ")
# calculate the search statistics
NameInfo = GetNameInformation(NameList, SearchName)
# print out the results of the search.
print(f'''--------------------------------------------------
{NameInfo[0]} names start with this string
{NameInfo[1]} names end with this string
{NameInfo[2]} names contain this string
--------------------------------------------------''')