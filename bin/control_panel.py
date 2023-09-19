#!/usr/bin/env python3

import signal
import sys
import RPi.GPIO as GPIO
import os
import psutil
import logging


ROTARY_PINS = [ 6, 13, 19, 26 ]

# The sequence of values read from the encoder GPIO pins as the knob goes
# through all 16 positions.
ROTARY_SEQUENCE = [ 6, 7, 5, 4, 12, 13, 9, 8, 0, 1, 3, 2, 10, 11, 15, 14 ]

logger = logging.getLogger("panel")

class Rotary:
    ''' Rotary encoder connected to GPIO pins.

    The encoder outputs Gray-code sequence on its output pins,
    which can be translated into decimal.
    The exact sequence depends on the switch and the order of pins.
    It can be easily determined experimentally by simply reading
    the raw values of the encoder in sequence.
    '''

    def __init__(self, pins, sequence=None):
        logger.debug("Configuring control panel pins=%s seq=%s", pins, sequence)
        self.pins = pins
        self.sequence = sequence

        self.setupPinmux()
        self.value = self.readValue()


    def setupPinmux(self):
        GPIO.setmode(GPIO.BCM)
        for i in self.pins:
            GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_UP)


    def installChangeCallback(self, callback):
        self.changeCallback = callback
        for i in self.pins:
            GPIO.add_event_detect(i,
                                  GPIO.BOTH,
                                  callback=self.onPinChange,
                                  bouncetime=200)

    def onPinChange(self, pin):
        v = self.readValue()
        try: self.changeCallback(self.value, v)
        finally: self.value = v


    def readValue(self):
        v = 0
        for i in self.pins:
            v = (v << 1) | GPIO.input(i)

        return self.translate(v)

    def translate(self, v):
        if (self.sequence is None): return v
        return self.sequence.index(v)



# ------------------------------------------------------------------------------


class ControlPanel:
    ''' Main app logic
    '''

    def __init__(self, slideshow, rotary):
        self.slideshow = slideshow
        self.rotary = rotary
        self.rotary.installChangeCallback(self.onRotaryChange)


    def onRotaryChange(self, fromValue, toValue):
        logger.debug("Rotary: %d -> %d", fromValue, toValue)

        d = self.determineRotaryChangeDirection(fromValue, toValue)
        if d > 0:
            self.slideshow.nextImage()
        elif d < 0:
            self.slideshow.prevImage()


    def determineRotaryChangeDirection(self, fromValue, toValue):
        # Rotary values go from 0-15
        # Determine the direction of the change, taking into account
        # that the value can wrap around and it can change by more than 1

        # 3 ways to calculate the diffenrece:
        # no wrap, wrap end-to-start, wrap start-to-end
        deltas = [ toValue - fromValue,
                   (16 + toValue) - fromValue,
                   (-16 + toValue) - fromValue ]

        # the smallest absolute change is the most likely actual change
        deltas.sort(key=abs)
        return deltas[0]

# ------------------------------------------------------------------------------

def main(argv):
    setupSignalHandler()
    setupPinmux()

    slideshow = filesout.FehSlideshow()
    rotary = Rotary(ROTARY_PINS, ROTARY_SEQUENCE)

    controller = ControlPanel(slideshow, rotary)

    # sleep indefinitely
    signal.pause()


def setupSignalHandler():
    signal.signal(signal.SIGINT, onSignal)
    signal.signal(signal.SIGTERM, onSignal)


def onSignal(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import filesout
    main(sys.argv)
