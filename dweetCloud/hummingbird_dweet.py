#Humming Bird Pan Tilt Dweet control
import signal
import json
import os
import sys
import logging
import adafruit_servokit
import time
from gpiozero import Device, LED
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
from uuid import uuid1
import requests                                                                    # (1)

default_angle = 90
# Global Variables
LED_GPIO_PIN = 21                    
THING_NAME_FILE = 'thing_name.txt'  
URL = 'https://dweet.io'            
last_led_state = None               
thing_name = None                   
led = None                          
magni = None


# Initialize Logging
logging.basicConfig(level=logging.WARNING)  # Global logging configuration
logger = logging.getLogger('main')  # Logger for this module
logger.setLevel(logging.INFO)  # Debugging for this file.                           # (2)


# Initialize GPIO
Device.pin_factory = PiGPIOFactory()

class dweetPy(object):
    default_angle = 90

    def __init__(self, num_ports):
        self.kit = adafruit_servokit.ServoKit(channels=16)
        self.num_ports = num_ports
        self.resetAll()

    def setAngle(self, port, angle):
        if angle < 0:
            self.kit.servo[port].angle = 0
        elif angle > 180:
            self.kit.servo[port].angle = 180
        else:
            self.kit.servo[port].angle = angle
    
    def getAngle(self, port):
        return self.kit.servo[port].angle

    def reset(self, port):
        self.kit.servo[port].angle = self.default_angle

    def resetAll(self):
        for i in range(self.num_ports):
            self.kit.servo[i].angle = self.default_angle
            
servoKit = dweetPy(2)
            
def test():
    servoKit = dweetPy(2)
    print("Start test")
    
    servoKit.setAngle(0, 120)#top 120 facing forward  lower the higher 0(up) 180 (down)
    servoKit.setAngle(1, 90)#bottom  90 facing forward higher to right(180) Left (0)
    time.sleep(.1)
##end here


# Function Definitions
def init_led():
    """Create and initialise an LED Object"""
    global led
    led = LED(LED_GPIO_PIN)
    led.off()
    


def resolve_thing_name(thing_file):
    """Get existing, or create a new thing name"""
    if os.path.exists(thing_file):                                                 # (3)
        with open(thing_file, 'r') as file_handle:
            name = file_handle.read()
            logger.info('Thing name ' + name + ' loaded from ' + thing_file)
            return name.strip()
    else:
        name = str(uuid1())[:8]  # UUID object to string.                          # (4)
        logger.info('Created new thing name ' + name)

        with open(thing_file, 'w') as f:                                           # (5)
            f.write(name)

    return name


def get_latest_dweet():
    """Get the last dweet made by our thing."""
    resource = URL + '/get/latest/dweet/for/' + thing_name                         # (6)
    logger.debug('Getting last dweet from url %s', resource)

    r = requests.get(resource)                                                     # (7)

    if r.status_code == 200:                                                       # (8)
        dweet = r.json()  # return a Python dict.
        logger.debug('Last dweet for thing was %s', dweet)

        dweet_content = None

        if dweet['this'] == 'succeeded':                                           # (9)
            # We're just interested in the dweet content property.
            dweet_content = dweet['with'][0]['content']                            # (10)

        return dweet_content

    else:
        logger.error('Getting last dweet failed with http status %s', r.status_code)
        return {}


def poll_dweets_forever(delay_secs=2):
    """Poll dweet.io for dweets about our thing."""
    while True:
        dweet = get_latest_dweet()                                                 # (11)
        if dweet is not None:
            process_dweet(dweet)                                                   # (12)

            sleep(delay_secs)                                                      # (13)


def stream_dweets_forever():
    """Listen for streaming for dweets"""
    resource = URL + '/listen/for/dweets/from/' + thing_name
    logger.info('Streaming dweets from url %s', resource)

    session = requests.Session()
    request = requests.Request("GET", resource).prepare()

    while True:  # while True to reconnect on any disconnections.
        try:
            response = session.send(request, stream=True, timeout=1000)

            for line in response.iter_content(chunk_size=None):
                if line:
                    try:
                        json_str = line.splitlines()[1]
                        json_str = json_str.decode('utf-8')
                        dweet = json.loads(eval(json_str))  # json_str is a string in a string.
                        logger.debug('Received a streamed dweet %s', dweet)

                        dweet_content = dweet['content']
                        process_dweet(dweet_content)
                    except Exception as e:
                        logger.error(e, exc_info=True)
                        logger.error('Failed to process and parse dweet json string %s', json_str)

        except requests.exceptions.RequestException as e:
            # Lost connection. The While loop will reconnect.
            #logger.error(e, exc_info=True)
            pass

        except Exception as e:
            logger.error(e, exc_info=True)


def process_dweet(dweet):
    """Inspect the dweet and set LED state accordingly"""
    global last_led_state
    z=0
    
    if not 'state' in dweet:
        return

    led_state = dweet['state']

    if led_state == last_led_state:                                                # (14)
        return  # LED is already in requested state.

    if led_state == 'alarm':                                                          # (15)
        led.on()
    elif led_state == 'alarmoff':
        led.off()
        #cam
    elif led_state == 'resetCam':
        servoKit.setAngle(0, 120)#top 120 facing forward  lower the higher 0(up) 180 (down)
        servoKit.setAngle(1, 90)#bottom  90 facing forward higher to right(180) Left (0)
        #cam
    elif led_state == 'up':
        #cam
        servoKit.setAngle(0, 50)#top 120 facing forward  lower the higher 0(up) 180 (down
        #servoKit.setAngle(1, 90)#bottom  90 facing forward higher to right(180) Left (0)
        time.sleep(.1)
        z = 1
    elif led_state == 'frontv':
        #cam
        servoKit.setAngle(0, 120)#top 120 facing forward  lower the higher 0(up) 180 (down
        #servoKit.setAngle(1, 90)#bottom  90 facing forward higher to right(180) Left (0)
        time.sleep(.1)
        z = 1
    elif led_state == 'fronth':
        #cam
        #servoKit.setAngle(0, 120)#top 120 facing forward  lower the higher 0(up) 180 (down
        servoKit.setAngle(1, 90)#bottom  90 facing forward higher to right(180) Left (0)
        time.sleep(.1)
        z = 1
    elif led_state == 'down':
        servoKit.setAngle(0, 170)#top 120 facing forward  lower the higher 0(up) 180 (down
        #servoKit.setAngle(1, 90)#bottom  90 facing forward higher to right(180) Left (0)
        time.sleep(.1)
        z = 1   
    elif led_state == 'left':
        servoKit.setAngle(1, 0)#bottom  90 facing forward higher to right(180) Left (0)
        #cam
        z = 1   
    elif led_state == 'right':
        servoKit.setAngle(1, 180)#bottom  90 facing forward higher to right(180) Left (0)
        #cam
        z = 1   
    elif led_state == 'magniStop':
        #cam
        z = 1
    elif led_state == 'magniStart':
        #cam 
        z = 1
    
    else:  # Off, including any unhandled state.
        led_state = 'off'
        led.off()
        test()

    if led_state != last_led_state:                                                # (16)
        last_led_state = led_state
        logger.info('LED ' + led_state)


def print_instructions():
    """Print instructions to terminal."""
    print("LED Control URLs - Try them in your web browser:")
    print("  Go Forward    : " + URL + "/dweet/for/" + thing_name + "?state=forward")
    print("  Go Right   : " + URL + "/dweet/for/" + thing_name + "?state=left")
    print("  Go Left   : " + URL + "/dweet/for/" + thing_name + "?state=right")
    print("  Stop  : " + URL + "/dweet/for/" + thing_name + "?state=stop\n")


def signal_handler(sig, frame):
    """Release resources and clean up as needed."""
    print('You pressed Control+C')
    led.off()
    sys.exit(0)


# Initialise Module
thing_name = resolve_thing_name(THING_NAME_FILE)
init_led()


# Main entry point
if __name__ == '__main__':
    test()
    
    signal.signal(signal.SIGINT, signal_handler)  # Capture CTRL + C
    print_instructions()                                                           # (17)

    #  last dweet.
    last_dweet = get_latest_dweet()                                                # (18)
    if (last_dweet):
        process_dweet(last_dweet)

    print('Waiting for dweets. Press Control+C to exit.')

    poll_dweets_forever()  # Get dweets by polling a URL on a schedule.            # (19)
