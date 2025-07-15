from django import forms
from .models import Room, Reservation

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'capacity', 'description', 'equipment', 'status']
        
class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['room', 'date', 'start_time', 'end_time', 'title', 'booker', 'department']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
