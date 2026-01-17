import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from chat.models import Room, Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messaging
    """
    
    async def connect(self):
        """Called when WebSocket connection is established"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']
        
        # Reject if user is not authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user is participant of this room
        is_participant = await self.check_room_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection success message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to room {self.room_id}'
        }))
    
    async def disconnect(self, close_code):
        """Called when WebSocket connection is closed"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Called when message is received from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                content = data.get('message', '')
                
                if not content.strip():
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Message content cannot be empty'
                    }))
                    return
                
                # Save message to database
                message = await self.save_message(content)
                
                # Broadcast message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message.id,
                            'content': message.content,
                            'sender': {
                                'id': message.sender.id,
                                'email': message.sender.email,
                                'first_name': message.sender.first_name,
                                'last_name': message.sender.last_name,
                            },
                            'created_at': message.created_at.isoformat(),
                            'is_read': message.is_read,
                        }
                    }
                )
            
            elif message_type == 'typing':
                # Broadcast typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': self.user.id,
                        'email': self.user.email,
                        'is_typing': data.get('is_typing', False)
                    }
                )
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def chat_message(self, event):
        """Called when a message is sent to the group"""
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Called when typing indicator is sent to the group"""
        # Don't send typing indicator back to the sender
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'email': event['email'],
                'is_typing': event['is_typing']
            }))
    
    @database_sync_to_async
    def check_room_participant(self):
        """Check if user is a participant of the room"""
        try:
            room = Room.objects.get(id=self.room_id)
            return room.participants.filter(id=self.user.id).exists()
        except Room.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        room = Room.objects.get(id=self.room_id)
        message = Message.objects.create(
            room=room,
            sender=self.user,
            content=content
        )
        # Update room's updated_at timestamp
        room.save(update_fields=['updated_at'])
        return message