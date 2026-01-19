from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model


from account.responseSerializers import ErrorResponseSerializer

from .models import (
    Message, 
    Room
)
from .serializers import( 
    MessageSerializer, 
    RoomSerializer,
    AddParticipantSerializer,
)


User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="List User's Rooms",
        description="Retrieve all chat rooms where the authenticated user is a participant.",
        responses={200: RoomSerializer(many=True), 403: ErrorResponseSerializer}
    ),
    retrieve=extend_schema(
        summary="Get Room Details",
        description="Retrieve detailed information about a specific room.",
        responses={200: RoomSerializer, 404: ErrorResponseSerializer}
    ),
    create=extend_schema(
        summary="Create Room",
        description="Create a new chat room (direct or group chat).",
        request=RoomSerializer,
        responses={201: RoomSerializer, 400: ErrorResponseSerializer}
    ),
    update=extend_schema(
        summary="Update Room",
        description="Update room details (name, etc.).",
        request=RoomSerializer,
        responses={200: RoomSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    partial_update=extend_schema(
        summary="Partially Update Room",
        description="Partially update room details.",
        request=RoomSerializer,
        responses={200: RoomSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    destroy=extend_schema(
        summary="Delete Room",
        description="Delete a chat room.",
        responses={204: None, 404: ErrorResponseSerializer}
    )
)
class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat rooms.
    
    Handles:
    - List user's rooms
    - Retrieve a room
    - Create direct or group rooms
    - Update room details
    - Delete rooms
    - Add participants
    """
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return rooms the user participates in
        return Room.objects.filter(
            participants=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        serializer.save()

    @extend_schema(
        summary="Add participant to group",
        description="Adds a participant to an existing group room using their email address.",
        request=AddParticipantSerializer,
        responses={200: RoomSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer}
    )
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        room = self.get_object()
        
        # Check permissions
        if room.room_type != 'group':
            return Response(
                {"error": "Cannot add participants to a direct message room."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only creator or existing participants can add others (depending on your logic)
        # For now, let's say any participant can add others
        if request.user not in room.participants.all():
            raise PermissionDenied("You are not a participant in this room.")

        serializer = AddParticipantSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = get_object_or_404(User, email=email)
            
            if user in room.participants.all():
                return Response(
                    {"error": "User is already a participant."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            room.participants.add(user)
            return Response(RoomSerializer(room).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    list=extend_schema(
        summary="List Messages",
        description="Retrieve messages from a specific room. Use 'room' query parameter to filter by room ID.",
        responses={200: MessageSerializer(many=True), 403: ErrorResponseSerializer}
    ),
    retrieve=extend_schema(
        summary="Get Message",
        description="Retrieve a specific message by ID.",
        responses={200: MessageSerializer, 404: ErrorResponseSerializer}
    ),
    create=extend_schema(
        summary="Send Message",
        description="Send a new message to a room.",
        request=MessageSerializer,
        responses={201: MessageSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer}
    )
)
class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat messages.
    
    Handles:
    - List messages in a room (filtered by 'room' query parameter)
    - Retrieve a specific message
    - Send new messages
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']  # No update or delete

    def get_queryset(self):
        room_id = self.request.query_params.get('room')
        if not room_id:
            return Message.objects.none()
        
        return Message.objects.filter(
            room_id=room_id,
            room__participants=self.request.user
        ).select_related('sender', 'room').order_by('-created_at')

    def perform_create(self, serializer):
        room = serializer.validated_data['room']
        if not room.participants.filter(id=self.request.user.id).exists():
            raise PermissionDenied("You are not a participant in this room")
        serializer.save(sender=self.request.user)



def login_page(request):
    return render(request, 'chat/login.html')

def register_page(request):
    return render(request, 'chat/register.html')

def room_list_page(request):
    return render(request, 'chat/room_list.html')

def chat_room_page(request, room_id):
    return render(request, 'chat/chat_room.html', {'room_id': room_id})

def room_detail_page(request, room_id):
    return render(request, 'chat/room_detail.html', {'room_id': room_id})

def profile_page(request):
    return render(request, 'chat/profile.html')