#!/usr/bin/env python3

import sys
import os
import signal
import argparse
import logging
import time
import threading
import gc
import asyncio
import websockets
import json
from typing import Dict, Set

import RPi.GPIO as gpio

# gc.disable()

# Configure logging
logger = logging.getLogger(__name__)

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
                        logger.info(f"Buzzer pressed: {c}")
                        if self.callback:
                            self.callback(c)
                        break

class BuzzerClient:
    def __init__(self, game_id: int, buzzers: BuzzerThread, server_url: str):
        self.game_id = game_id
        self.buzzers = buzzers
        self.server_url = server_url
        self.websocket = None
    
    async def connect(self):
        uri = f"ws://{self.server_url}/ws/game/{self.game_id}/?client_type=buzzer"
        self.websocket = await websockets.connect(
            uri,
            ping_interval=15,
            ping_timeout=5
        )
        logger.info(f"Connected to {uri}")

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
                elif data['type'] == 'buzzer_set_log_level':
                    level = data.get('level', 'INFO')
                    numeric_level = getattr(logging, level.upper(), None)
                    if isinstance(numeric_level, int):
                        logging.getLogger().setLevel(numeric_level)
                        logger.info(f"Log level changed to {level}")

            except websockets.ConnectionClosed:
                logger.warning("Disconnected, attempting to reconnect...")
                # Disable buzzers when connection is lost
                self.buzzers.enabled = False
                await asyncio.sleep(1)
                await self.connect()
                # Continue the loop with the new connection
            except Exception as e:
                logger.error(f"Error in listen_for_messages: {e}")
                # Disable buzzers on error
                self.buzzers.enabled = False
                await asyncio.sleep(1)
                # Attempt to reconnect in case of persistent errors
                try:
                    await self.connect()
                except Exception as reconnect_error:
                    logger.error(f"Reconnection failed: {reconnect_error}")

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
            logger.error(f"Failed to send buzzer press: {e}")

    def schedule_buzzer_press(self, buzzer_id: int):
        asyncio.run_coroutine_threadsafe(
            self.handle_buzzer_press(buzzer_id), self.loop)

    async def run_async(self):
        self.loop = asyncio.get_running_loop()
        self.buzzers.callback = self.schedule_buzzer_press
        self.buzzers.start()
        await self.connect()
        asyncio.create_task(self.listen_for_messages())


def cleanup_gpio(signum=None, frame=None):
    """Cleanup GPIO pins on shutdown"""
    logger.info("Cleaning up GPIO...")
    gpio.cleanup()
    sys.exit(0)


def setup_logging(log_level: str):
    """Configure logging with the specified level"""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Hardware buzzer client for Quizzer game system'
    )
    parser.add_argument(
        'game_id',
        type=int,
        help='Game ID to connect to'
    )
    parser.add_argument(
        '--server',
        type=str,
        default=os.getenv('QUIZZER_SERVER', 'quasar.local:8000'),
        help='Server URL (default: quasar.local:8000, or QUIZZER_SERVER env var)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default=os.getenv('QUIZZER_LOG_LEVEL', 'INFO'),
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO, or QUIZZER_LOG_LEVEL env var)'
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.log_level)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, cleanup_gpio)
    signal.signal(signal.SIGINT, cleanup_gpio)
    
    thread = BuzzerThread()
    client = BuzzerClient(args.game_id, thread, args.server)
    try:
        asyncio.get_event_loop().run_until_complete(client.run_async())
        asyncio.get_event_loop().run_forever()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        gpio.cleanup()
        raise
