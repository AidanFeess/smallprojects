#################################################################
# Name: Aidan Feess
# Date: May 13 2024
# Description: A calculator with a GUI
#################################################################
from tkinter import *
# the main GUI
class MainGUI(Frame):
    # the constructor
    def __init__(self, parent):
        Frame.__init__(self, parent, bg="white")
        parent.attributes("-fullscreen", True)
        self.setupGUI()
        self.clear_next = False
    # sets up the GUI
    def setupGUI(self):
        # the calculator uses the TexGyreAdventor font (see
        # https://www.fontsquirrel.com/fonts/tex-gyre-adventor)
        # on most Linux system, simply double-click the font files
        # and install them
        # on the RPi, copy them to /usr/local/share/fonts (with
        # sudo):
        # sudo cp tex*.otf /usr/local/share/fonts
        # then reboot
        # the display
        # right-align text in the display; and set its background to
        # white, its height to 2 characters, and its font to 50
        # point TexGyreAdventor
        self.display = Label(self, text="", anchor=E, bg="white",
        height=1, font=("TexGyreAdventor", 45))
        # put it in the top row, spanning across all four columns;
        # and expand it on all four sides
        self.display.grid(row=0, column=0, columnspan=4,
        sticky=E+W+N+S)
        # the button layout
        # ( ) AC <-
        # 7 8 9 /
        # 4 5 6 *
        # 1 2 3 -
        # 0 . x +
        # = = ** %
        # configure the rows and columns of the Frame to adjust to
        # the window
        # there are 6 rows (0 through 5)
        for row in range(6):
            Grid.rowconfigure(self, row, weight=1)
        # there are 4 columns (0 through 3)
        for col in range(4):
            Grid.columnconfigure(self, col, weight=1)
        # the first row
        # (
        # first, fetch and store the image
        # to work best on the RPi, images should be 115x115 pixels
        # otherwise, may need to add .subsample(n)
        img = PhotoImage(file="images/lpr.gif")
        # next, create the button (white background, no border, no
        # highlighting, no color when clicked)
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("("))
        # set the button's image
        button.image = img
        # put the button in its proper row and column
        button.grid(row=1, column=0, sticky=N+S+E+W)
        # the same is done for the rest of the buttons
        # )
        img = PhotoImage(file="images/rpr.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process(")"))
        button.image = img
        button.grid(row=1, column=1, sticky=N+S+E+W)
        # AC
        img = PhotoImage(file="images/clr.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("AC"))
        button.image = img
        button.grid(row=1, column=2, sticky=N+S+E+W)
        # back
        img = PhotoImage(file="images/bak.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("back"))
        button.image = img
        button.grid(row=1, column=3, sticky=N+S+E+W)
        # the second row
        # 7
        img = PhotoImage(file="images/7.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("7"))
        button.image = img
        button.grid(row=2, column=0, sticky=N+S+E+W)
        # 8
        img = PhotoImage(file="images/8.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("8"))
        button.image = img
        button.grid(row=2, column=1, sticky=N+S+E+W)
        # 9
        img = PhotoImage(file="images/9.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("9"))
        button.image = img
        button.grid(row=2, column=2, sticky=N+S+E+W)
        # /
        img = PhotoImage(file="images/div.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("/"))
        button.image = img
        button.grid(row=2, column=3, sticky=N+S+E+W)
        # the third row
        # 4
        img = PhotoImage(file="images/4.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("4"))
        button.image = img
        button.grid(row=3, column=0, sticky=N+S+E+W)
        # 5
        img = PhotoImage(file="images/5.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("5"))
        button.image = img
        button.grid(row=3, column=1, sticky=N+S+E+W)
        # 6
        img = PhotoImage(file="images/6.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("6"))
        button.image = img
        button.grid(row=3, column=2, sticky=N+S+E+W)
        # *
        img = PhotoImage(file="images/mul.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("*"))
        button.image = img
        button.grid(row=3, column=3, sticky=N+S+E+W)
        # the fourth row
        # 1
        img = PhotoImage(file="images/1.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("1"))
        button.image = img
        button.grid(row=4, column=0, sticky=N+S+E+W)
        # 2
        img = PhotoImage(file="images/2.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("2"))
        button.image = img
        button.grid(row=4, column=1, sticky=N+S+E+W)
        # 3
        img = PhotoImage(file="images/3.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("3"))
        button.image = img
        button.grid(row=4, column=2, sticky=N+S+E+W)
        # -
        img = PhotoImage(file="images/sub.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("-"))
        button.image = img
        button.grid(row=4, column=3, sticky=N+S+E+W)
        # the fifth row
        # 0
        img = PhotoImage(file="images/0.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("0"))
        button.image = img
        button.grid(row=5, column=0, sticky=N+S+E+W)
        # .
        img = PhotoImage(file="images/dot.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("."))
        button.image = img
        button.grid(row=5, column=1, sticky=N+S+E+W)
        # +
        img = PhotoImage(file="images/add.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("+"))
        button.image = img
        button.grid(row=5, column=3, sticky=N+S+E+W)
        
        #the sixth row
        # =
        img = PhotoImage(file="images/eql.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("="))
        button.image = img
        button.grid(row=6, column=0, sticky=N+S+E+W)
        # **
        img = PhotoImage(file="images/pow.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("**"))
        button.image = img
        button.grid(row=6, column=2, sticky=N+S+E+W)
        # %
        img = PhotoImage(file="images/mod.gif")
        button = Button(self, bg="white", image=img, borderwidth=0, highlightthickness=0, activebackground="white", command=lambda: self.process("%"))
        button.image = img
        button.grid(row=6, column=3, sticky=N+S+E+W)
        
        # the sixth row
        # pack the GUI
        self.pack(fill=BOTH, expand=1)

    #processes button presses
    def process(self, button):
        # AC clears the display
        if button == "AC":
            # clear the display
            self.display["text"] = ""
            return
        # = starts an evaluation of whatever is on the display
        elif button == "=":
            # get the expression in the display
            expression = self.display["text"]
            # the evaluation may return an error!
            try:
                # evaluate the expression
                result = str(eval(expression))
                # ensure the length is valid
                if len(result) > 14:
                    # if not then truncate it and add three dots
                    result = result[:11] + "..."
                # store the result to the display
                self.display["text"] = result
            # handle if an aerror occurs during evaluation
            except:
                # note the error in the display
                self.display["text"] = "ERROR"
            self.clear_next = True
            return
        # back removes the last entered character
        elif button == "back":
            self.display["text"] = self.display["text"][:-1]
            return
        
        # Check if the UI should be cleared
        if self.clear_next:
            # clear the display
            self.display["text"] = ""
            # reset
            self.clear_next = False

        # Clamp the amount of text to 14 characters if entering something
        if len(self.display["text"]) >= 14:
            return
        # otherwise, just tack on the appropriate operand/operator
        else:
            self.display["text"] += button
##############################
# the main part of the program
##############################
# create the window
window = Tk()
# set the window title
window.title("The Reckoner")
# generate the GUI
p = MainGUI(window)
# display the GUI and wait for user interaction
window.mainloop()