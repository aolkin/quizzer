#!/usr/bin/env python3

import gc
import RPi.GPIO as gpio

gc.disable()

gpio.setmode(gpio.BCM)

S = (23, 24, 25)

EN = 16
IN = 18

for pin in S:
    gpio.setup(pin, gpio.OUT, initial=gpio.LOW)

gpio.setup(EN, gpio.OUT, initial=gpio.LOW)
gpio.setup(IN, gpio.IN, pull_up_down=gpio.PUD_UP)

def select_channel(channel):
    for i in range(3):
        s = channel & (1 << i) != 0
        # print(i, s)
        gpio.output(S[i], s)

while True:
    for c in range(7):
        if c == 3:
            continue
        select_channel(c)
        button = gpio.input(IN)
        if not button:
            print("Button:", c)
            exit()
