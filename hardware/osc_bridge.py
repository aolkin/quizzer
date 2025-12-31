#!/usr/bin/env python3

import argparse
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import yaml
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer

from lib.websocket_client import HardwareWebSocketClient

logger = logging.getLogger(__name__)


class OSCBridgeClient(HardwareWebSocketClient):
    """
    WebSocket ↔ OSC Bridge for hardware integration.
    
    Translates messages between WebSocket (Quizzer backend) and OSC
    (external hardware/software) based on YAML configuration.
    """

    def __init__(
        self,
        host: str,
        game_id: int,
        client_id: str,
        config: Dict[str, Any],
    ):
        super().__init__(
            host=host,
            game_id=game_id,
            client_type="osc",
            client_id=client_id,
            logger=logger,
        )
        self.config = config
        self.osc_clients: Dict[str, udp_client.SimpleUDPClient] = {}
        self.osc_server: Optional[AsyncIOOSCUDPServer] = None
        
    def _get_osc_client(self, host: str, port: int) -> udp_client.SimpleUDPClient:
        """
        Get or create an OSC client for a destination.
        
        Note: Clients are cached for the lifetime of the bridge. This is
        acceptable since destinations are defined in static configuration
        and typically number only a handful of endpoints.
        """
        key = f"{host}:{port}"
        if key not in self.osc_clients:
            self.osc_clients[key] = udp_client.SimpleUDPClient(host, port)
            logger.debug(f"Created OSC client for {key}")
        return self.osc_clients[key]
    
    async def handle_message(self, message: dict):
        """Handle incoming WebSocket messages and translate to OSC."""
        message_type = message.get("type")
        
        outgoing_rules = self.config.get("outgoing", [])
        for rule in outgoing_rules:
            if rule.get("websocket_type") == message_type:
                await self._send_osc_from_websocket(message, rule)
    
    async def _send_osc_from_websocket(self, message: dict, rule: dict):
        """Send OSC message(s) based on WebSocket message and rule."""
        destinations = rule.get("osc_destinations", [])
        
        for dest in destinations:
            try:
                host = dest["host"]
                port = dest["port"]
                address = dest["address"]
                args_config = dest.get("args", [])
                
                osc_args = []
                for arg_spec in args_config:
                    field_name = arg_spec["field"]
                    arg_type = arg_spec["type"]
                    
                    value = message.get(field_name)
                    if value is None:
                        logger.warning(
                            f"Field '{field_name}' not found in message {message}"
                        )
                        continue
                    
                    converted_value = self._convert_type(
                        value, arg_type, "to_osc"
                    )
                    osc_args.append(converted_value)
                
                client = self._get_osc_client(host, port)
                client.send_message(address, osc_args)
                logger.debug(
                    f"Sent OSC: {address} {osc_args} to {host}:{port}"
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to send OSC message to {dest.get('host')}:"
                    f" {dest.get('port')}: {e}"
                )
    
    def _convert_type(
        self, value: Any, target_type: str, direction: str = "to_osc"
    ) -> Any:
        """
        Convert value between WebSocket and OSC types.
        
        Args:
            value: Value to convert
            target_type: Target type (int, float, bool, string)
            direction: "to_osc" or "to_websocket"
        """
        if target_type == "int":
            if direction == "to_osc" and isinstance(value, bool):
                return 1 if value else 0
            return int(value)
        elif target_type == "float":
            return float(value)
        elif target_type == "bool":
            if direction == "to_websocket" and isinstance(value, (int, float)):
                return value > 0.5
            return bool(value)
        elif target_type == "string":
            return str(value)
        else:
            logger.warning(f"Unknown type '{target_type}', passing value as-is")
            return value
    
    async def _handle_osc_message(self, address: str, *args):
        """Handle incoming OSC messages and translate to WebSocket."""
        incoming_rules = self.config.get("incoming", [])
        
        for rule in incoming_rules:
            if rule.get("osc_address") == address:
                await self._send_websocket_from_osc(args, rule)
                return
        
        logger.debug(f"No rule found for OSC address: {address}")
    
    async def _send_websocket_from_osc(self, osc_args: tuple, rule: dict):
        """Send WebSocket message based on OSC message and rule."""
        try:
            websocket_type = rule["websocket_type"]
            args_config = rule.get("args", [])
            
            message_fields = {}
            for arg_spec in args_config:
                osc_index = arg_spec["osc_index"]
                websocket_field = arg_spec["websocket_field"]
                arg_type = arg_spec["type"]
                
                if osc_index >= len(osc_args):
                    logger.warning(
                        f"OSC arg index {osc_index} out of range for args {osc_args}"
                    )
                    continue
                
                value = osc_args[osc_index]
                converted_value = self._convert_type(value, arg_type, "to_websocket")
                message_fields[websocket_field] = converted_value
            
            await self.send_message(websocket_type, **message_fields)
            logger.debug(
                f"Sent WebSocket: {websocket_type} {message_fields}"
            )
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket message from OSC: {e}")
    
    async def setup_osc_server(self):
        """Set up OSC server to listen for incoming OSC messages."""
        osc_config = self.config.get("osc", {})
        listen_host = osc_config.get("listen_host", "0.0.0.0")
        listen_port = osc_config.get("listen_port", 7400)
        
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self._handle_osc_message)
        
        self.osc_server = AsyncIOOSCUDPServer(
            (listen_host, listen_port),
            dispatcher,
            asyncio.get_event_loop()
        )
        
        transport, protocol = await self.osc_server.create_serve_endpoint()
        logger.info(f"OSC server listening on {listen_host}:{listen_port}")
        
        return transport, protocol


def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file."""
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML configuration: {e}")
        raise


def setup_logging(log_level: str):
    """Configure logging with the specified level."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="WebSocket ↔ OSC bridge for Quizzer game system"
    )
    parser.add_argument(
        "config",
        type=str,
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("QUIZZER_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO, or QUIZZER_LOG_LEVEL env var)",
    )
    return parser.parse_args()


async def main():
    """Main async entry point."""
    args = parse_args()
    setup_logging(args.log_level)
    
    config = load_config(args.config)
    
    ws_config = config.get("websocket", {})
    host = ws_config.get("host", "quasar.local")
    game_id = ws_config.get("game_id", 1)
    client_id = ws_config.get("client_id", "osc-main")
    
    client = OSCBridgeClient(host, game_id, client_id, config)
    
    await client.setup_osc_server()
    
    try:
        await client.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        if client.osc_server:
            client.osc_server.close()


if __name__ == "__main__":
    asyncio.run(main())
