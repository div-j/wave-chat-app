from django.db import models
from django.conf import settings


class Room(models.Model):
    """
    Represents a chat room (one-to-one or group chat)
    """
    ROOM_TYPE_CHOICES = [
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
    ]
    
    name = models.CharField(max_length=255, blank=True, null=True)  # Only for group chats
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES, default='direct')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['room_type']),
        ]

    def __str__(self):
        if self.room_type == 'group':
            return self.name or f"Group {self.id}"
        # For direct messages, show participant emails
        participants = self.participants.all()[:2]
        if participants.count() == 2:
            return f"{participants[0].email} - {participants[1].email}"
        return f"Room {self.id}"
    
    def get_last_message(self):
        """Returns the last message in this room"""
        return self.messages.first()  # Already ordered by -created_at


class Message(models.Model):
    """
    Represents a chat message in a room
    """
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]

    def __str__(self):
        return f"{self.sender.email}: {self.content[:50]}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

