from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Room, Reservation, Settings
import datetime

@csrf_exempt
@require_http_methods(["GET"])
def load_rooms(request):
    """加载会议室数据"""
    rooms = []
    for room in Room.objects.all():
        rooms.append({
            'id': str(room.id),
            'name': room.name,
            'capacity': room.capacity,
            'description': room.description or '',
            'equipment': room.equipment or '',
            'status': room.status
        })
    return JsonResponse(rooms, safe=False)

@csrf_exempt
@require_http_methods(["GET"])
def load_reservations(request):
    """加载预约数据"""
    reservations = []
    for res in Reservation.objects.all():
        reservations.append({
            'id': res.id,
            'room': str(res.room.id),
            'date': res.date.isoformat(),
            'start': res.start_time.strftime('%H:%M'),
            'end': res.end_time.strftime('%H:%M'),
            'title': res.title,
            'booker': res.booker
        })
    return JsonResponse(reservations, safe=False)

@csrf_exempt
@require_http_methods(["GET"])
def load_settings(request):
    """加载设置数据"""
    settings = {s.key: s.value for s in Settings.objects.all()}
    return JsonResponse(settings)

@csrf_exempt
@require_http_methods(["POST"])
def save_rooms(request):
    """保存会议室数据"""
    try:
        data = json.loads(request.body)
        
        # 获取所有现有的房间ID
        existing_ids = set(Room.objects.values_list('id', flat=True))
        received_ids = set()
        
        for room_data in data:
            room_id = room_data.get('id')
            if room_id and room_id.startswith('room'):
                # 处理字符串ID，尝试从现有房间中找到匹配的
                try:
                    existing_room = Room.objects.filter(id__isnull=False).first()
                    if existing_room:
                        # 如果是编辑现有房间，通过名称匹配
                        room, created = Room.objects.update_or_create(
                            name=room_data.get('name', ''),
                            defaults={
                                'capacity': room_data.get('capacity', 0),
                                'description': room_data.get('description', ''),
                                'equipment': room_data.get('equipment', ''),
                                'status': room_data.get('status', 'available')
                            }
                        )
                        received_ids.add(room.id)
                    else:
                        # 创建新房间
                        new_room = Room.objects.create(
                            name=room_data.get('name', ''),
                            capacity=room_data.get('capacity', 0),
                            description=room_data.get('description', ''),
                            equipment=room_data.get('equipment', ''),
                            status=room_data.get('status', 'available')
                        )
                        received_ids.add(new_room.id)
                except Exception:
                    # 创建新房间
                    new_room = Room.objects.create(
                        name=room_data.get('name', ''),
                        capacity=room_data.get('capacity', 0),
                        description=room_data.get('description', ''),
                        equipment=room_data.get('equipment', ''),
                        status=room_data.get('status', 'available')
                    )
                    received_ids.add(new_room.id)
            elif room_id and room_id.isdigit():
                # 处理数字ID
                received_ids.add(int(room_id))
                room, created = Room.objects.update_or_create(
                    id=int(room_id),
                    defaults={
                        'name': room_data.get('name', ''),
                        'capacity': room_data.get('capacity', 0),
                        'description': room_data.get('description', ''),
                        'equipment': room_data.get('equipment', ''),
                        'status': room_data.get('status', 'available')
                    }
                )
            else:
                # 创建新房间
                new_room = Room.objects.create(
                    name=room_data.get('name', ''),
                    capacity=room_data.get('capacity', 0),
                    description=room_data.get('description', ''),
                    equipment=room_data.get('equipment', ''),
                    status=room_data.get('status', 'available')
                )
                received_ids.add(new_room.id)
        
        # 删除未接收到的房间
        ids_to_delete = existing_ids - received_ids
        if ids_to_delete:
            Room.objects.filter(id__in=ids_to_delete).delete()
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_reservations(request):
    """保存预约数据"""
    try:
        data = json.loads(request.body)
        
        # 获取所有现有的预约ID
        existing_ids = set(Reservation.objects.values_list('id', flat=True))
        received_ids = set()
        
        for res_data in data:
            res_id = res_data.get('id')
            
            # 解析日期和时间
            date_str = res_data.get('date')
            date_obj = datetime.date.fromisoformat(date_str) if date_str else None
            
            start_str = res_data.get('start')
            start_time = datetime.datetime.strptime(start_str, '%H:%M').time() if start_str else None
            
            end_str = res_data.get('end')
            end_time = datetime.datetime.strptime(end_str, '%H:%M').time() if end_str else None
            
            # 获取房间
            room_id = res_data.get('room')
            try:
                room = Room.objects.get(id=room_id)
            except Room.DoesNotExist:
                continue
                
            if res_id:
                received_ids.add(int(res_id))
                # 更新现有预约
                try:
                    reservation = Reservation.objects.get(id=res_id)
                    reservation.room = room
                    reservation.date = date_obj
                    reservation.start_time = start_time
                    reservation.end_time = end_time
                    reservation.title = res_data.get('title', '')
                    reservation.booker = res_data.get('booker', '')
                    reservation.save()
                except Reservation.DoesNotExist:
                    # 如果ID不存在，创建新预约
                    Reservation.objects.create(
                        id=res_id,
                        room=room,
                        date=date_obj,
                        start_time=start_time,
                        end_time=end_time,
                        title=res_data.get('title', ''),
                        booker=res_data.get('booker', '')
                    )
            else:
                # 创建新预约
                new_res = Reservation.objects.create(
                    room=room,
                    date=date_obj,
                    start_time=start_time,
                    end_time=end_time,
                    title=res_data.get('title', ''),
                    booker=res_data.get('booker', '')
                )
                received_ids.add(new_res.id)
        
        # 删除未接收到的预约
        ids_to_delete = existing_ids - received_ids
        if ids_to_delete:
            Reservation.objects.filter(id__in=ids_to_delete).delete()
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_settings(request):
    """保存设置数据"""
    try:
        data = json.loads(request.body)
        
        # 更新或创建设置
        for key, value in data.items():
            Settings.objects.update_or_create(
                key=key,
                defaults={'value': value}
            )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
