from machine import Pin
import time

led = Pin(25, Pin.OUT)
a = 0

while True:
    led.value(a)
    if a == 0:
        a = 1
    else:
        a = 0
    print(a)
    time.sleep(0.2)
    











