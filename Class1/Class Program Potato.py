## Aidan Feess 2/1/2024 ##
import pineworkslabs.RPi as GPIO
from time import sleep

# Set the GPIO mode to the potato
GPIO.setmode(GPIO.LE_POTATO_LOOKUP)
# Define the switch and pin's position
pin = 18
switch = 27

while True:
    try:
        # Setup the switch to recieve data and pin to give data
        GPIO.setup(switch, GPIO.IN)
        GPIO.setup(pin, GPIO.OUT)
        # Get switch input to determine if the LED should blink quickly or slowly
        if GPIO.input(switch) == 1:
            GPIO.output(pin, GPIO.HIGH)
            sleep(.1)
            GPIO.output(pin, GPIO.LOW)
            sleep(.1)
        else:
            GPIO.output(pin, GPIO.HIGH)
            sleep(.5)
            GPIO.output(pin, GPIO.LOW)
            sleep(.5)
    # Allow keyboard input to stop the program
    except KeyboardInterrupt:
        GPIO.cleanup()
