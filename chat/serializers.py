from rest_framework import serializers
from django.contrib.auth import get_user_model

from chat.models import (
    Room, 
    Message
    )

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for chat contexts"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    sender = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'room', 'sender', 'content', 'is_read', 'created_at', 'updated_at']
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class RoomSerializer(serializers.ModelSerializer):
    participants = UserMinimalSerializer(many=True, read_only=True)
    participant_emails = serializers.ListField(
        child=serializers.EmailField(),
        write_only=True,
        required=True
    )
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            'id', 'name', 'room_type',
            'participants', 'participant_emails', 'participant_count',
            'created_at'
        ]
        read_only_fields = ['id', 'participants', 'created_at']

    def get_participant_count(self, obj):
        return obj.participants.count()

    def validate_participant_emails(self, value):
        if not value:
            raise serializers.ValidationError("At least one participant email is required.")
        return value

    def create(self, validated_data):
        participant_emails = validated_data.pop('participant_emails')
        request = self.context['request']

        # Create the room
        room = Room.objects.create(
            name=validated_data.get('name'),
            room_type=validated_data.get('room_type', 'direct'),
            created_by=request.user
        )
        
        # Add creator as participant
        room.participants.add(request.user)
        
        # Find and add other participants by email
        for email in participant_emails:
            try:
                user = User.objects.get(email=email)
                room.participants.add(user)
            except User.DoesNotExist:
                # Skip non-existent users or raise error
                pass

        return room


