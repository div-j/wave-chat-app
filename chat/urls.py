from django.urls import path
from .views import (
    RoomViewSet, 
    MessageViewSet
    )

urlpatterns = [
    # Room endpoints
    path('rooms/', RoomViewSet.as_view({'get': 'list', 'post': 'create'}), name='room-list'),
    path('rooms/<int:pk>/', RoomViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='room-detail'),
    path('rooms/<int:pk>/add_participant/', RoomViewSet.as_view({'post': 'add_participant'}), name='room-add-participant'),
    
    # Message endpoints
    path('messages/', MessageViewSet.as_view({'get': 'list', 'post': 'create'}), name='message-list'),
    path('messages/<int:pk>/', MessageViewSet.as_view({'get': 'retrieve'}), name='message-detail'),
]