from django.contrib import admin
from .models import Room, Reservation, Settings

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'status')
    list_filter = ('status',)
    search_fields = ('name', 'description')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('title', 'room', 'date', 'start_time', 'end_time', 'booker')
    list_filter = ('date', 'room')
    search_fields = ('title', 'booker')
    date_hierarchy = 'date'

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    search_fields = ('key',)
