#!/usr/bin/env python3

import sys
import os
import signal
import argparse
import logging
import threading
import asyncio

import RPi.GPIO as gpio

from lib.websocket_client import HardwareWebSocketClient

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

class BuzzerClient(HardwareWebSocketClient):
    def __init__(
        self, game_id: int, buzzers: BuzzerThread, server_url: str, client_id: str = "main"
    ):
        super().__init__(
            host=server_url,
            game_id=game_id,
            client_type="buzzer",
            client_id=client_id,
            logger=logger,
        )
        self.buzzers = buzzers

    async def handle_message(self, message: dict):
        """Handle buzzer-specific messages."""
        if message["type"] == "toggle_buzzers":
            self.buzzers.enabled = message["enabled"]
            if message["enabled"]:
                self.buzzers.selected = None
                await self.send_message("buzzer_pressed", buzzerId=None)

        elif message["type"] == "buzzer_set_log_level":
            level = message.get("level", "INFO")
            numeric_level = getattr(logging, level.upper(), None)
            if isinstance(numeric_level, int):
                logging.getLogger().setLevel(numeric_level)
                self.logger.info(f"Log level changed to {level}")

    async def setup(self):
        """Initialize hardware when connection is established."""
        # Start the buzzer thread if not already running
        if not self.buzzers.is_alive():
            self.buzzers.callback = self.schedule_buzzer_press
            self.buzzers.start()

    async def teardown(self):
        """Cleanup when connection is lost."""
        # Disable buzzers when connection is lost
        self.buzzers.enabled = False

    async def handle_buzzer_press(self, buzzer_id: int):
        """Called by hardware when a buzzer is pressed."""
        await self.send_message("buzzer_pressed", buzzerId=buzzer_id)

    def schedule_buzzer_press(self, buzzer_id: int):
        """Schedule buzzer press message from hardware thread."""
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.handle_buzzer_press(buzzer_id), self.loop
            )


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
        asyncio.run(client.run())
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        gpio.cleanup()
        raise
