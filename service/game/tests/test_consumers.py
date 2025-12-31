"""
Tests for WebSocket consumers.

These tests verify the WebSocket consumer behavior, including
connection handling, group management, and message relay.
"""

from channels.testing import WebsocketCommunicator
from ..consumers import GameConsumer
from .test_fixtures import BaseGameTestCase


class GameConsumerTestCase(BaseGameTestCase):
    """Tests for GameConsumer WebSocket behavior."""

    async def test_relay_coordination_message(self):
        """Test relay pattern: messages are broadcast to all clients in the group."""
        # Create two communicators for the same game
        communicator1 = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/game/{self.game.id}/")
        communicator1.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        communicator2 = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/game/{self.game.id}/")
        communicator2.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        # Connect both (implicitly tests connection)
        await communicator1.connect()
        await communicator2.connect()

        # Send a coordination message from communicator1
        await communicator1.send_json_to({"type": "select_question", "question_id": self.q1.id})

        # Both communicators should receive the message
        response1 = await communicator1.receive_json_from()
        response2 = await communicator2.receive_json_from()

        self.assertEqual(response1["type"], "select_question")
        self.assertEqual(response1["question_id"], self.q1.id)
        self.assertEqual(response2["type"], "select_question")
        self.assertEqual(response2["question_id"], self.q1.id)

        # Disconnect (implicitly tests disconnection)
        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_reject_invalid_messages(self):
        """Test that malformed messages (non-dict or missing 'type') are rejected."""
        communicator = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/game/{self.game.id}/")
        communicator.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        await communicator.connect()

        # Non-dict message should be rejected
        await communicator.send_json_to("not a dict")
        result = await communicator.receive_nothing(timeout=0.1)
        self.assertTrue(result)

        # Message without 'type' field should be rejected
        await communicator.send_json_to({"data": "some data"})
        result = await communicator.receive_nothing(timeout=0.1)
        self.assertTrue(result)

        await communicator.disconnect()

    async def test_channel_id_injection(self):
        """Test that channel_id is injected into all outgoing messages."""
        communicator = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/game/{self.game.id}/")
        communicator.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        await communicator.connect()
        await communicator.send_json_to({"type": "test_message"})

        response = await communicator.receive_json_from()

        self.assertIn("channel_id", response)
        self.assertIsNotNone(response["channel_id"])

        await communicator.disconnect()

    async def test_targeted_message_channel_id(self):
        """Test targeted message delivery using channel_id."""
        communicator1 = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/game/{self.game.id}/")
        communicator1.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        communicator2 = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/game/{self.game.id}/")
        communicator2.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        await communicator1.connect()
        await communicator2.connect()

        await communicator1.send_json_to({"type": "ping"})
        msg1 = await communicator1.receive_json_from()
        channel_id_1 = msg1["channel_id"]
        await communicator2.receive_json_from()

        await communicator2.send_json_to(
            {
                "type": "pong",
                "recipient": {"channel_id": channel_id_1},
            }
        )

        response1 = await communicator1.receive_json_from()
        self.assertEqual(response1["type"], "pong")

        result = await communicator2.receive_nothing(timeout=0.1)
        self.assertTrue(result)

        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_targeted_message_client_id(self):
        """Test targeted message delivery using client_id."""
        communicator1 = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f"/ws/game/{self.game.id}/?client_type=buzzer&client_id=test-buzzer-1",
        )
        communicator1.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        communicator2 = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f"/ws/game/{self.game.id}/?client_type=buzzer&client_id=test-buzzer-2",
        )
        communicator2.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        await communicator1.connect()
        await communicator2.connect()

        await communicator1.receive_json_from()
        await communicator1.receive_json_from()
        await communicator2.receive_json_from()

        await communicator1.send_json_to(
            {
                "type": "command",
                "recipient": {"client_id": "test-buzzer-2"},
            }
        )

        response2 = await communicator2.receive_json_from()
        self.assertEqual(response2["type"], "command")

        result1 = await communicator1.receive_nothing(timeout=0.1)
        self.assertTrue(result1)

        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_targeted_message_client_type(self):
        """Test targeted message delivery using client_type."""
        communicator1 = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f"/ws/game/{self.game.id}/?client_type=buzzer&client_id=test-1",
        )
        communicator1.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        communicator2 = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f"/ws/game/{self.game.id}/?client_type=osc&client_id=test-2",
        )
        communicator2.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        communicator3 = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/game/{self.game.id}/")
        communicator3.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        await communicator1.connect()
        await communicator2.connect()
        await communicator3.connect()

        await communicator1.receive_json_from()
        await communicator1.receive_json_from()
        await communicator2.receive_json_from()

        await communicator1.send_json_to(
            {
                "type": "toggle_buzzers",
                "recipient": {"client_type": "buzzer"},
            }
        )

        response1 = await communicator1.receive_json_from()
        self.assertEqual(response1["type"], "toggle_buzzers")

        result2 = await communicator2.receive_nothing(timeout=0.1)
        self.assertTrue(result2)

        result3 = await communicator3.receive_nothing(timeout=0.1)
        self.assertTrue(result3)

        await communicator1.disconnect()
        await communicator2.disconnect()
        await communicator3.disconnect()

    async def test_targeted_message_multiple_criteria(self):
        """Test targeted message with multiple recipient criteria (AND logic)."""
        communicator1 = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f"/ws/game/{self.game.id}/?client_type=buzzer&client_id=test-1",
        )
        communicator1.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        communicator2 = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f"/ws/game/{self.game.id}/?client_type=buzzer&client_id=test-2",
        )
        communicator2.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        await communicator1.connect()
        await communicator2.connect()

        await communicator1.receive_json_from()
        await communicator1.receive_json_from()
        await communicator2.receive_json_from()

        await communicator1.send_json_to(
            {
                "type": "command",
                "recipient": {"client_type": "buzzer", "client_id": "test-2"},
            }
        )

        response2 = await communicator2.receive_json_from()
        self.assertEqual(response2["type"], "command")

        result1 = await communicator1.receive_nothing(timeout=0.1)
        self.assertTrue(result1)

        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_invalid_recipient_format(self):
        """Test that invalid recipient format is rejected."""
        communicator1 = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/game/{self.game.id}/")
        communicator1.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        communicator2 = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/game/{self.game.id}/")
        communicator2.scope["url_route"] = {"kwargs": {"game_id": self.game.id}}

        await communicator1.connect()
        await communicator2.connect()

        await communicator1.send_json_to(
            {
                "type": "test",
                "recipient": "not-a-dict",
            }
        )

        result1 = await communicator1.receive_nothing(timeout=0.1)
        self.assertTrue(result1)

        result2 = await communicator2.receive_nothing(timeout=0.1)
        self.assertTrue(result2)

        await communicator1.disconnect()
        await communicator2.disconnect()
