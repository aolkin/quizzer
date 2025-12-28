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
        # Create two communicators for the same board
        communicator1 = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/board/{self.board.id}/")
        communicator1.scope["url_route"] = {"kwargs": {"board_id": self.board.id}}

        communicator2 = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/board/{self.board.id}/")
        communicator2.scope["url_route"] = {"kwargs": {"board_id": self.board.id}}

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
        communicator = WebsocketCommunicator(GameConsumer.as_asgi(), f"/ws/board/{self.board.id}/")
        communicator.scope["url_route"] = {"kwargs": {"board_id": self.board.id}}

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
