from django.db import models

class Room(models.Model):
    """会议室模型"""
    name = models.CharField(max_length=100, verbose_name="会议室名称")
    capacity = models.IntegerField(verbose_name="容量")
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    equipment = models.CharField(max_length=255, blank=True, null=True, verbose_name="设备")
    status = models.CharField(max_length=20, choices=[
        ('available', '可用'),
        ('maintenance', '维护中'),
        ('unavailable', '不可用')
    ], default='available', verbose_name="状态")

    def __str__(self):
        return f"{self.name} ({self.capacity}人)"
    
    class Meta:
        verbose_name = "会议室"
        verbose_name_plural = "会议室"

class Reservation(models.Model):
    """预约模型"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="会议室")
    date = models.DateField(verbose_name="日期")
    start_time = models.TimeField(verbose_name="开始时间")
    end_time = models.TimeField(verbose_name="结束时间")
    title = models.CharField(max_length=255, verbose_name="会议主题")
    booker = models.CharField(max_length=100, verbose_name="预约人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self):
        return f"{self.title} - {self.room.name} ({self.date})"
    
    class Meta:
        verbose_name = "预约记录"
        verbose_name_plural = "预约记录"

class Settings(models.Model):
    """系统设置模型"""
    key = models.CharField(max_length=100, unique=True, verbose_name="键")
    value = models.TextField(blank=True, null=True, verbose_name="值")

    def __str__(self):
        return self.key
    
    class Meta:
        verbose_name = "系统设置"
        verbose_name_plural = "系统设置"
