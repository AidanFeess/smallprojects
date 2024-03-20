####################################################################
# author: Aidan Feess
# date: 1 / 25 / 2024
# description: a program that calculates the minimum number of soccer matches that a soccer league will have
# based on the number of teams that are in the league
####################################################################
# A function to prompt the user for the number of teams in a league. It
# does not take any arguments and returns the result to the calling
# statement.
def PromptUser():
    return int(input("How many teams are in this league?"))
# A function that calculates the number of matches in a league. It
# receives a single numerical argument representing the number of teams
# in the league, and uses RECURSION to calculate the minimum number of
# matches required. It then returns the result to the calling statement.
def CalculateNumMatches(teams):
    return CalculateNumMatches(teams-1) + (teams-1) if teams > 0 else 0
# A function that prints out the final results. It receives two
# arguments that represent the number of teams and matches.
def PrintFinal(teams, matches):
    print(f"A league of {teams} teams would require at least {matches} matches")
############################ MAIN #################################
# get the number of teams
numTeams = PromptUser()
# calculate the number of matches
# print the results to the screen.
PrintFinal(numTeams, CalculateNumMatches(numTeams))