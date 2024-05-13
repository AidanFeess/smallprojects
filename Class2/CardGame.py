#####################################################################
# author: Aidan Feess
# date: May 10 2024
# description: Program that allows the user to play a card game 
#####################################################################

# import the shuffle and seed functions from the random library.
import random

# set the seed
random.seed(9876543210)

# define the possible suits that the cards can have using a list.
POSSIBLESUITS = ["clubs", "diamonds", "hearts", "spades"]

# CLass
class Card:
    def __init__(self, number, suit):
        self.number = number
        self.suit = suit

    @property
    def number(self):
        return self._number
    @number.setter
    def number(self, value):
        # Set the value to 2 if the value is less than 2 or more than 10, inclusive
        self._number = value if value <= 10 and value >= 2 and isinstance(value, int) else 2

    @property
    def suit(self):
        return self._suit
    @suit.setter
    def suit(self, value):
        # Set the suit to clubs if the given suit isn't in the list of possible suits
        self._suit = value if str.lower(value) in POSSIBLESUITS else POSSIBLESUITS[0]

    def __gt__(self, other):
        return self.number > other.number

    def __lt__(self, other):
        return self.number < other.number

    def __eq__(self, other):
        return self.number == other.number

    def __str__(self):
        return f"{self.number} of {self.suit}"

class Deck:
    def __init__(self):
        # Using list comprehension to create a list of cards for each suit, for each number between 2 and 10 inclusive
        self.cards : list = [Card(number, suit) for suit in POSSIBLESUITS for number in range(2, 11)]
    
    @property
    def cards(self):
        return self._cards
    @cards.setter
    def cards(self, value):
        self._cards = value

    # A function that shuffles the deck
    def shuffle(self, times=1):
        # Ensuring that the amount of times the deck is shuffled is more than 0, and that 'times' is a integer
        times = times if times > 0 and isinstance(times, int) else 1
        for i in range(times):
            random.shuffle(self.cards)

    def draw(self, amount=1):
        # Ensuring that the amount of cards drawn is more than 0, less than the amount of cards in the deck, and is an integer
        amount = amount if amount > 0 and isinstance(amount, int) else 2
        if amount > self.size(): return None
        # draw the first n cards
        drawn = []
        # define an iterator variable
        it = 0
        for card in range(amount):
            # subtract the current count by iteration because we are dynamically changing the size of the list
            drawn.append(self.cards[card-it])
            self.cards.pop(card-it)
            # increase the iteration
            it+=1
        self.shuffle()
        return drawn[0] if len(drawn) < 2 else drawn

    # A function that returns the size of the deck
    def size(self):
        return len(self.cards)
    
    def __repr__(self):
        return f"[{', '.join([str(card) for card in self.cards])}, ]" if self.size() > 0 else "[--empty--]"

class Game:
    def __init__(self):
        self.deck = Deck()
        self.deck.shuffle(2)

    @property
    def deck(self):
        return self._deck
    @deck.setter
    def deck(self, value):
        self._deck = value

    # Start function to begin the game, print out the start message, 
    # and handle playing/ending the game based on user input
    def start(self):
        print("-" * 40)
        print("Welcome to a basic game.\nYou and this program will take turns picking cards.\nThe one with the highest value card wins")
        print("-" * 40)
        self.play() if input("Are you ready to start? ") == "y" else self.end()

    # Play function that drives game
    # Draws 2 cards, if there are cards in the deck, then shuffles the deck
    # and compares the 2 cards, printing out the winner based on the comparison
    def play(self):
        if self.deck.size() >= 2:
            print(self.deck.size())
            # draw automatically shuffles the deck
            new_cards = self.deck.draw(2)
            # The user is the first card, the computer is the second
            print(f"You picked {new_cards[0]}, and I picked {new_cards[1]}")
            if new_cards[0] > new_cards[1]:
                print("YOU WIN")
            elif new_cards[1] > new_cards[0]:
                print("I WIN")
            else:
                # If the user's card is equal in weight
                print("TIE")
            # Recursively call the play function if the user decides to play again, otherwise call the end function
            self.play() if input("Would you like to play again? ") == "y" else self.end()
        else:
            # Automatically end the game if the deck is empty, and display custom message
            print("Not enough cards to play")
            self.end()

    # End function, called by other functions if the user decides to stop playing or the deck runs out of cards
    def end(self):
        print("Sorry to see you go\n" + "-"*4 + "Remaining Cards" + "-"*7 + f"\n{self.deck}")
        return