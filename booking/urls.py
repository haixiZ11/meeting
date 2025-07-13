from django.urls import path
from . import views
from . import api

urlpatterns = [
    # 主页视图
    path('', views.index, name='index'),
    path('booking-admin/', views.admin, name='admin'),
    path('room_status/', views.room_status, name='room_status'),
    
    # API接口
    path('api/load_rooms/', api.load_rooms, name='load_rooms'),
    path('api/load_reservations/', api.load_reservations, name='load_reservations'),
    path('api/load_settings/', api.load_settings, name='load_settings'),
    path('api/save_rooms/', api.save_rooms, name='save_rooms'),
    path('api/save_reservations/', api.save_reservations, name='save_reservations'),
    path('api/save_settings/', api.save_settings, name='save_settings'),
]
