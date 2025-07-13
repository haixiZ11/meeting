from django.test import TestCase
from .models import Room, Reservation
import datetime

class RoomModelTest(TestCase):
    def setUp(self):
        Room.objects.create(name="测试会议室", capacity=10)
        
    def test_room_creation(self):
        room = Room.objects.get(name="测试会议室")
        self.assertEqual(room.capacity, 10)
        self.assertEqual(room.status, 'available')

class ReservationModelTest(TestCase):
    def setUp(self):
        room = Room.objects.create(name="测试会议室", capacity=10)
        today = datetime.date.today()
        start_time = datetime.time(10, 0)
        end_time = datetime.time(11, 0)
        Reservation.objects.create(
            room=room,
            date=today,
            start_time=start_time,
            end_time=end_time,
            title="测试会议",
            booker="测试预约人"
        )
        
    def test_reservation_creation(self):
        reservation = Reservation.objects.get(title="测试会议")
        self.assertEqual(reservation.booker, "测试预约人")
        self.assertEqual(reservation.room.name, "测试会议室")
