from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Room

@ensure_csrf_cookie
def index(request):
    """主页视图"""
    rooms = Room.objects.all()
    return render(request, 'booking/index.html', {'rooms': rooms})
