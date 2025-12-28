"""
Tests for WebSocket consumers.

These tests verify the WebSocket consumer behavior, including
connection handling, group management, and message relay.
"""
from channels.testing import WebsocketCommunicator
from django.test import TestCase
from ..consumers import GameConsumer
from .test_fixtures import BaseGameTestCase


class GameConsumerTestCase(BaseGameTestCase):
    """Tests for GameConsumer WebSocket behavior."""
    
    async def test_connect_and_join_group(self):
        """Test that WebSocket connection is accepted and joins correct group."""
        communicator = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f'/ws/board/{self.board.id}/'
        )
        communicator.scope['url_route'] = {'kwargs': {'board_id': self.board.id}}
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.disconnect()
    
    async def test_disconnect(self):
        """Test that WebSocket disconnects cleanly."""
        communicator = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f'/ws/board/{self.board.id}/'
        )
        communicator.scope['url_route'] = {'kwargs': {'board_id': self.board.id}}
        
        await communicator.connect()
        await communicator.disconnect()
        # If disconnect completes without error, test passes
    
    async def test_relay_coordination_message(self):
        """Test that coordination messages are relayed to all clients."""
        # Create two communicators for the same board
        communicator1 = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f'/ws/board/{self.board.id}/'
        )
        communicator1.scope['url_route'] = {'kwargs': {'board_id': self.board.id}}
        
        communicator2 = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f'/ws/board/{self.board.id}/'
        )
        communicator2.scope['url_route'] = {'kwargs': {'board_id': self.board.id}}
        
        await communicator1.connect()
        await communicator2.connect()
        
        # Send a coordination message from communicator1
        await communicator1.send_json_to({
            'type': 'select_question',
            'question_id': self.q1.id
        })
        
        # Both communicators should receive the message
        response1 = await communicator1.receive_json_from()
        response2 = await communicator2.receive_json_from()
        
        self.assertEqual(response1['type'], 'select_question')
        self.assertEqual(response1['question_id'], self.q1.id)
        self.assertEqual(response2['type'], 'select_question')
        self.assertEqual(response2['question_id'], self.q1.id)
        
        await communicator1.disconnect()
        await communicator2.disconnect()
    
    async def test_reject_malformed_message_non_dict(self):
        """Test that non-dict messages are rejected."""
        communicator = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f'/ws/board/{self.board.id}/'
        )
        communicator.scope['url_route'] = {'kwargs': {'board_id': self.board.id}}
        
        await communicator.connect()
        
        # Send a non-dict message (should be silently rejected)
        await communicator.send_json_to("not a dict")
        
        # Should not receive anything back (message was rejected)
        # We use receive_nothing to verify no message was sent
        result = await communicator.receive_nothing(timeout=0.1)
        self.assertTrue(result)
        
        await communicator.disconnect()
    
    async def test_reject_message_without_type(self):
        """Test that messages without 'type' field are rejected."""
        communicator = WebsocketCommunicator(
            GameConsumer.as_asgi(),
            f'/ws/board/{self.board.id}/'
        )
        communicator.scope['url_route'] = {'kwargs': {'board_id': self.board.id}}
        
        await communicator.connect()
        
        # Send a message without 'type' field
        await communicator.send_json_to({'data': 'some data'})
        
        # Should not receive anything back
        result = await communicator.receive_nothing(timeout=0.1)
        self.assertTrue(result)
        
        await communicator.disconnect()
