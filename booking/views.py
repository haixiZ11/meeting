from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Room


@ensure_csrf_cookie
def index(request):
    """主页视图"""
    rooms = Room.objects.all()
    return render(request, "booking/index.html", {"rooms": rooms})


@ensure_csrf_cookie
def admin(request):
    """管理后台视图"""
    return render(request, "booking/admin.html")


@ensure_csrf_cookie
def room_status(request):
    """会议室状态视图"""
    return render(request, "booking/room_status.html")


@ensure_csrf_cookie
def status_display(request):
    """状态显示屏视图"""
    rooms = Room.objects.all()
    return render(request, "booking/status_display.html", {"rooms": rooms})
