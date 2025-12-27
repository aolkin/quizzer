#!/usr/bin/env python3

import sys
import time
import threading
import gc
import asyncio
import websockets
import json
from typing import Dict, Set

import RPi.GPIO as gpio

# gc.disable()

S = (23, 24, 25)

EN = 16
IN = 18

LOOP_MAX = 5000

class BuzzerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        gpio.setmode(gpio.BCM)

        for pin in S:
            gpio.setup(pin, gpio.OUT, initial=gpio.LOW)

        gpio.setup(EN, gpio.OUT, initial=gpio.LOW)
        gpio.setup(IN, gpio.IN, pull_up_down=gpio.PUD_UP)

        self.enabled = False
        self.selected = None
        self.callback = None

    def _select_channel(self, channel):
        for i in range(3):
            s = channel & (1 << i) != 0
            # print(i, s)
            gpio.output(S[i], s)

    def run(self):
        loop = 0
        while True:
            if self.selected != None:
                # loop = (loop + 1) % (LOOP_MAX * 2)
                self._select_channel(c)
                gpio.output(EN, False) # loop < LOOP_MAX / 3)
                continue
            loop = (loop + 1) % LOOP_MAX
            for c in range(7):
                if c == 3:
                    continue
                gpio.output(EN, not (self.enabled or loop < LOOP_MAX / 2))
                self._select_channel(c)
                if self.enabled:
                    button = gpio.input(IN)
                    if not button:
                        self.selected = c
                        print("Buzzer pressed:", c)
                        if self.callback:
                            self.callback(c)
                        break

class BuzzerClient:
    def __init__(self, game_id: int, buzzers: BuzzerThread):
        self.game_id = game_id
        self.buzzers = buzzers
        self.websocket = None
    
    async def connect(self, reconnect=False):
        uri = f"ws://quasar.local:8000/ws/game/{self.game_id}/"
        self.websocket = await websockets.connect(uri)
        print("Connected")
        await self.websocket.send(json.dumps({
            'type': 'toggle_buzzers',
            'enabled': self.buzzers.enabled
        }))
        asyncio.create_task(self.listen_for_messages())

    async def listen_for_messages(self):
        while True:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)

                if data['type'] == 'toggle_buzzers':
                    self.buzzers.enabled = data['enabled']
                    if data['enabled']:
                        self.buzzers.selected = None
                        await self.websocket.send(json.dumps({
                            'type': 'buzzer_pressed',
                            'buzzerId': None
                        }))

            except websockets.ConnectionClosed:
                print("Disconnected, attempting to reconnect...")
                await asyncio.sleep(1)
                await self.connect(True)
                return
            except Exception as e:
                print(f"Error in listen_for_messages: {e}")
                await asyncio.sleep(1)

    async def handle_buzzer_press(self, buzzer_id: int):
        """
        Called by hardware when a buzzer is pressed
        """
        try:
            await self.websocket.send(json.dumps({
                'type': 'buzzer_pressed',
                'buzzerId': buzzer_id
            }))
        except Exception as e:
            print(f"Failed to send buzzer press: {e}")

    def schedule_buzzer_press(self, buzzer_id: int):
        asyncio.run_coroutine_threadsafe(
            self.handle_buzzer_press(buzzer_id), self.loop)

    async def run_async(self):
        self.loop = asyncio.get_running_loop()
        self.buzzers.callback = self.schedule_buzzer_press
        self.buzzers.start()
        await self.connect()


if __name__ == "__main__":
    thread = BuzzerThread()
    client = BuzzerClient(int(sys.argv[1]), thread)
    try:
        asyncio.get_event_loop().run_until_complete(client.run_async())
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        gpio.cleanup()
    except Exception as e:
        print(f"Unexpected error: {e}")
        gpio.cleanup()
        raise
