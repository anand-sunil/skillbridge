from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('chat/<int:conversation_id>/', views.chat_view, name='chat_view'),
    path('start/<int:user_id>/', views.start_chat, name='start_chat'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('generate-reply/<int:conversation_id>/', views.generate_reply, name='generate_reply'),

]
