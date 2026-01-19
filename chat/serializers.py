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
        required=False
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
        if self.instance is None and not value:
            raise serializers.ValidationError("At least one participant email is required.")
        return value

    def create(self, validated_data):
        participant_emails = validated_data.pop('participant_emails', [])
        request = self.context['request']

        if not participant_emails:
            raise serializers.ValidationError({'participant_emails': ['At least one participant email is required.']})

        users = []
        missing_emails = []
        for email in participant_emails:
            try:
                users.append(User.objects.get(email=email))
            except User.DoesNotExist:
                missing_emails.append(email)

        if missing_emails:
            raise serializers.ValidationError({'participant_emails': [f"User(s) not found: {', '.join(missing_emails)}"]})

        room = Room.objects.create(
            name=validated_data.get('name'),
            room_type=validated_data.get('room_type', 'direct'),
            created_by=request.user
        )

        room.participants.add(request.user, *users)

        return room


class AddParticipantSerializer(serializers.Serializer):
    email = serializers.EmailField()