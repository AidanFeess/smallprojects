import pineworkslabs.RPi as GPIO
from time import sleep

# For pin naming convention
GPIO.setmode(GPIO.LE_POTATO_LOOKUP)

# Pin Variables
sensor = 24
light = 26
switch = 6

# Setup
GPIO.setup(sensor, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(light, GPIO.OUT)
GPIO.setup(switch, GPIO.IN)

# Main Code
try:
    while True:
        if GPIO.input(sensor) == GPIO.HIGH:
            GPIO.output(light, GPIO.HIGH)
            print("Motion detected! You have 3 seconds!")
            waits = 0
            while waits < 30:
                sleep(.1)
                waits += .1
                if GPIO.input(switch) == GPIO.HIGH:
                    break
                if waits >= 30:
                    print("Intruder alert!")
        else:
            GPIO.output(light, GPIO.LOW)
            print("No motion detected!")
        sleep(.1)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Closing")
                