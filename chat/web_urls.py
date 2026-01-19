from django.urls import path
from .views import (
    login_page,
    register_page,
    room_list_page,
    chat_room_page,
    room_detail_page,
    profile_page,
)

urlpatterns = [
    path('', login_page, name='home'),
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('rooms/', room_list_page, name='rooms'),
    path('chat/<int:room_id>/', chat_room_page, name='chat-room'),
    path('rooms/<int:room_id>/details/', room_detail_page, name='room-detail-page'),
    path('profile/', profile_page, name='profile-page'),
]
