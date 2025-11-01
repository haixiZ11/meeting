from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Room, Reservation, Settings
from django.utils import timezone
import datetime
import requests
import logging

# 配置日志
logger = logging.getLogger(__name__)

def has_reservation_changed(original_reservation, new_data, room):
    """检查预约数据是否有变化"""
    try:
        # 解析新数据的日期和时间
        date_str = new_data.get('date')
        new_date = datetime.date.fromisoformat(date_str) if date_str else None
        
        # 修复字段名：前端发送的是 'start' 和 'end'，不是 'start_time' 和 'end_time'
        start_str = new_data.get('start')
        new_start_time = None
        if start_str:
            try:
                new_start_time = datetime.datetime.strptime(start_str, '%H:%M').time()
            except ValueError as e:
                logger.error(f"解析开始时间失败: {start_str}, 错误: {e}")
                return True, f"开始时间格式错误: {start_str}"
        
        end_str = new_data.get('end')
        new_end_time = None
        if end_str:
            try:
                new_end_time = datetime.datetime.strptime(end_str, '%H:%M').time()
            except ValueError as e:
                logger.error(f"解析结束时间失败: {end_str}, 错误: {e}")
                return True, f"结束时间格式错误: {end_str}"
        
        # 比较各个字段
        if original_reservation.room.id != room.id:
            return True, "会议室变更"
        if original_reservation.date != new_date:
            return True, "日期变更"
        if original_reservation.start_time != new_start_time:
            return True, "开始时间变更"
        if original_reservation.end_time != new_end_time:
            return True, "结束时间变更"
        if original_reservation.title != new_data.get('title', ''):
            return True, "会议主题变更"
        if original_reservation.booker != new_data.get('booker', ''):
            return True, "预约人变更"
        if original_reservation.department != new_data.get('department', ''):
            return True, "部门变更"
            
        return False, "无变化"
    except Exception as e:
        logger.error(f"检查预约变化时出错: {str(e)}, 数据: {new_data}")
        # 发生错误时，为了安全起见，假设有变化，这样不会阻止保存操作
        return True, f"检查出错: {str(e)}"

def send_wechat_notification(reservation, action='新增'):
    """发送企业微信群机器人通知（markdown_v2格式）"""
    try:
        # 检查调试模式
        debug_setting = Settings.objects.filter(key='debug_mode').first()
        debug_mode = debug_setting and debug_setting.value.lower() == 'true'
        
        # 从设置中获取企业微信Webhook URL；不存在则使用settings.DEFAULT_WEBHOOK_URL
        from django.conf import settings as django_settings
        webhook_setting = Settings.objects.filter(key='webhook_url').first()
        webhook_url = (webhook_setting.value.strip() if (webhook_setting and webhook_setting.value) else getattr(django_settings, 'DEFAULT_WEBHOOK_URL', '').strip())
        if not webhook_url:
            error_msg = "Webhook URL未配置"
            logger.warning(f"企业微信通知失败: {error_msg}")
            if debug_mode:
                print(f"[DEBUG] 企业微信通知失败: {error_msg}")
            return False, error_msg
        
        if debug_mode:
            print(f"[DEBUG] 使用的Webhook URL: {webhook_url}")
            print(f"[DEBUG] 通知动作: {action}")
            print(f"[DEBUG] 预约信息: {reservation.title} - {reservation.booker}")
        
        # 根据action确定标题
        title_map = {
            '新增': '新增会议室预约通知',
            '修改': '会议室预约修改通知',
            '编辑': '会议室预约修改通知',
            '删除': '会议室预约取消(删除）通知'
        }
        title = title_map.get(action, '会议室预约通知')
        
        # 特殊字符转义函数（markdown_v2格式要求）
        def escape_markdown_v2(text):
            """转义markdown_v2格式中的特殊字符"""
            if not text:
                return text
            # 需要转义的字符：_ * [ ] ( ) ~ ` > # + - = | { } . !
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text
        
        # 构建markdown_v2格式的通知消息（转义特殊字符）
        room_name = escape_markdown_v2(reservation.room.name)
        title_escaped = escape_markdown_v2(reservation.title)
        booker_escaped = escape_markdown_v2(reservation.booker)
        department_escaped = escape_markdown_v2(reservation.department or '未填写')
        
        # 预先定义需要转义的字符串
        dash_separator = "\\-"
        triple_dash = "\\-\\-\\-"
        date_format = reservation.date.strftime('%Y年%m月%d日')
        time_range = f"{reservation.start_time.strftime('%H:%M')} {dash_separator} {reservation.end_time.strftime('%H:%M')}"
        # 转为本地时区再格式化，避免显示为UTC
        created_local = timezone.localtime(reservation.created_at)
        created_time = created_local.strftime('%Y-%m-%d %H:%M:%S').replace('-', '\\-')
        
        markdown_content = f"""# 📅 {title}

## 📋 会议详情

| **项目** | **内容** |
| :--- | :--- |
| **会议室** | {room_name} |
| **预约日期** | {date_format} |
| **会议时间** | {time_range} |
| **会议主题** | {title_escaped} |
| **预约人** | {booker_escaped} |
| **预约部门** | {department_escaped} |

{triple_dash}

> 📌 创建时间：{created_time}"""

        # 发送请求到企业微信群机器人
        payload = {
            "msgtype": "markdown_v2",
            "markdown_v2": {
                "content": markdown_content
            }
        }
        
        if debug_mode:
            print(f"[DEBUG] 请求payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            # 添加编码调试信息
            print(f"[DEBUG] markdown_v2内容编码: {markdown_content.encode('utf-8')}")
            print(f"[DEBUG] markdown_v2内容长度: {len(markdown_content.encode('utf-8'))} 字节")
        
        logger.info(f"正在发送企业微信通知到: {webhook_url[:50]}...")
        
        try:
            # 禁用代理以避免代理连接问题
            proxies = {
                'http': None,
                'https': None
            }
            
            # 明确指定UTF-8编码的Content-Type头，确保中文字符正确传输
            headers = {
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            # 手动序列化JSON以确保UTF-8编码
            json_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            
            if debug_mode:
                print(f"[DEBUG] 发送的JSON数据: {json_data}")
                print(f"[DEBUG] 请求头: {headers}")
            
            response = requests.post(webhook_url, data=json_data, headers=headers, timeout=10, proxies=proxies)
            
            if debug_mode:
                print(f"[DEBUG] HTTP响应状态码: {response.status_code}")
                print(f"[DEBUG] HTTP响应头: {dict(response.headers)}")
                print(f"[DEBUG] HTTP响应内容: {response.text}")
            
            logger.info(f"企业微信API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if debug_mode:
                        print(f"[DEBUG] 解析后的响应JSON: {result}")
                    
                    if result.get('errcode') == 0:
                        success_msg = f"企业微信通知发送成功: {reservation.title}"
                        logger.info(success_msg)
                        if debug_mode:
                            print(f"[DEBUG] {success_msg}")
                        return True, "发送成功"
                    else:
                        errcode = result.get('errcode', 'unknown')
                        errmsg = result.get('errmsg', '未知错误')
                        error_msg = f"企业微信API错误 - errcode: {errcode}, errmsg: {errmsg}"
                        logger.error(error_msg)
                        if debug_mode:
                            print(f"[DEBUG] {error_msg}")
                        return False, f"API错误: {errcode} - {errmsg}"
                except json.JSONDecodeError as e:
                    error_msg = f"响应JSON解析失败: {str(e)}, 响应内容: {response.text}"
                    logger.error(error_msg)
                    if debug_mode:
                        print(f"[DEBUG] {error_msg}")
                    return False, f"响应解析失败: {response.text[:100]}"
            else:
                error_msg = f"HTTP请求失败 - 状态码: {response.status_code}, 响应: {response.text}"
                logger.error(error_msg)
                if debug_mode:
                    print(f"[DEBUG] {error_msg}")
                return False, f"HTTP错误: {response.status_code}"
                
        except requests.exceptions.Timeout:
            error_msg = "请求超时（10秒）"
            logger.error(f"企业微信通知发送超时: {error_msg}")
            if debug_mode:
                print(f"[DEBUG] {error_msg}")
            return False, error_msg
        except requests.exceptions.ConnectionError as e:
            error_msg = f"网络连接错误: {str(e)}"
            logger.error(f"企业微信通知网络错误: {error_msg}")
            if debug_mode:
                print(f"[DEBUG] {error_msg}")
            return False, f"网络连接失败: {str(e)[:100]}"
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            logger.error(f"企业微信通知请求异常: {error_msg}")
            if debug_mode:
                print(f"[DEBUG] {error_msg}")
            return False, f"请求异常: {str(e)[:100]}"
            
    except Exception as e:
        error_msg = f"发送企业微信通知时出现未知错误: {str(e)}"
        logger.error(error_msg)
        if debug_mode:
            print(f"[DEBUG] {error_msg}")
            import traceback
            print(f"[DEBUG] 完整错误堆栈: {traceback.format_exc()}")
        return False, f"未知错误: {str(e)[:100]}"

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
            'booker': res.booker,
            'department': res.department or '',
            'room_id': res.room_id,
            'room_name': res.room.name if res.room else '',
            'created_at': timezone.localtime(res.created_at).strftime('%Y-%m-%d %H:%M:%S') if res.created_at else '',
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
    from django.db import transaction
    
    try:
        data = json.loads(request.body)
        
        # 数据验证
        if not isinstance(data, list):
            return JsonResponse({'success': False, 'error': '数据格式错误：期望数组格式'}, status=400)
        
        # 验证每个会议室数据
        for i, room_data in enumerate(data):
            if not isinstance(room_data, dict):
                return JsonResponse({'success': False, 'error': f'第{i+1}个会议室数据格式错误'}, status=400)
            
            name = room_data.get('name', '').strip()
            capacity = room_data.get('capacity', 0)
            
            if not name:
                return JsonResponse({'success': False, 'error': f'第{i+1}个会议室名称不能为空'}, status=400)
            
            try:
                capacity = int(capacity)
                if capacity <= 0:
                    return JsonResponse({'success': False, 'error': f'会议室"{name}"的容量必须大于0'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': f'会议室"{name}"的容量格式错误'}, status=400)
        
        # 检查是否为批量删除操作（数据量显著减少）
        existing_count = Room.objects.count()
        new_count = len(data)
        
        if existing_count > 0 and new_count < existing_count * 0.5:
            # 如果新数据量少于现有数据的50%，认为可能是意外删除
            logger.warning(f"检测到可能的批量删除操作：现有{existing_count}个会议室，新数据只有{new_count}个")
            return JsonResponse({
                'success': False, 
                'error': f'安全检查失败：检测到可能的批量删除操作（现有{existing_count}个会议室，新数据只有{new_count}个）。如需批量删除，请使用管理后台。',
                'code': 'BULK_DELETE_DETECTED'
            }, status=400)
        
        # 备份功能已移除 - 不再自动备份
        
        # 使用事务确保数据一致性
        with transaction.atomic():
            # 获取所有现有的房间ID
            existing_rooms = {room.id: room for room in Room.objects.all()}
            received_ids = set()
            
            # 处理每个会议室数据
            for room_data in data:
                room_id = room_data.get('id')
                name = room_data.get('name', '').strip()
                capacity = int(room_data.get('capacity', 0))
                description = room_data.get('description', '').strip()
                equipment = room_data.get('equipment', '').strip()
                status = room_data.get('status', 'available')
                
                if room_id and str(room_id).isdigit():
                    # 更新现有房间
                    room_id = int(room_id)
                    received_ids.add(room_id)
                    
                    room, created = Room.objects.update_or_create(
                        id=room_id,
                        defaults={
                            'name': name,
                            'capacity': capacity,
                            'description': description,
                            'equipment': equipment,
                            'status': status
                        }
                    )
                    
                    if not created:
                        logger.info(f"更新会议室: {name} (ID: {room_id})")
                    else:
                        logger.info(f"创建会议室: {name} (ID: {room_id})")
                        
                elif room_id and str(room_id).startswith('room'):
                    # 处理临时ID，查找是否有同名房间
                    existing_room = Room.objects.filter(name=name).first()
                    if existing_room:
                        # 更新现有房间
                        received_ids.add(existing_room.id)
                        existing_room.capacity = capacity
                        existing_room.description = description
                        existing_room.equipment = equipment
                        existing_room.status = status
                        existing_room.save()
                        logger.info(f"更新现有会议室: {name} (ID: {existing_room.id})")
                    else:
                        # 创建新房间
                        new_room = Room.objects.create(
                            name=name,
                            capacity=capacity,
                            description=description,
                            equipment=equipment,
                            status=status
                        )
                        received_ids.add(new_room.id)
                        logger.info(f"创建新会议室: {name} (ID: {new_room.id})")
                else:
                    # 创建新房间
                    new_room = Room.objects.create(
                        name=name,
                        capacity=capacity,
                        description=description,
                        equipment=equipment,
                        status=status
                    )
                    received_ids.add(new_room.id)
                    logger.info(f"创建新会议室: {name} (ID: {new_room.id})")
            
            # 安全删除：只删除明确不在新数据中的房间，且需要额外确认
            existing_ids = set(existing_rooms.keys())
            ids_to_delete = existing_ids - received_ids
            
            if ids_to_delete:
                # 检查要删除的房间是否有预约
                rooms_with_reservations = []
                for room_id in ids_to_delete:
                    room = existing_rooms[room_id]
                    if Reservation.objects.filter(room=room).exists():
                        rooms_with_reservations.append(room.name)
                
                if rooms_with_reservations:
                    # 如果有预约，不允许删除
                    raise Exception(f"无法删除有预约记录的会议室: {', '.join(rooms_with_reservations)}")
                
                # 删除没有预约的房间
                deleted_rooms = [existing_rooms[room_id].name for room_id in ids_to_delete]
                Room.objects.filter(id__in=ids_to_delete).delete()
                logger.warning(f"删除会议室: {', '.join(deleted_rooms)}")
        
        logger.info("会议室数据保存成功")
        return JsonResponse({
            'success': True, 
            'message': '会议室数据保存成功'
        })
        
    except Exception as e:
        error_msg = f"保存会议室数据失败: {str(e)}"
        logger.error(error_msg)
        return JsonResponse({'success': False, 'error': error_msg}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_reservations(request):
    """保存预约数据"""
    from django.db import transaction
    
    try:
        data = json.loads(request.body)
        
        # 数据验证
        if isinstance(data, list):
            reservations_data = data
        elif isinstance(data, dict) and 'reservations' in data:
            reservations_data = data.get('reservations', [])
        else:
            return JsonResponse({'success': False, 'error': '数据格式错误：期望数组或包含reservations键的对象'}, status=400)
        
        if not isinstance(reservations_data, list):
            return JsonResponse({'success': False, 'error': '预约数据格式错误：期望数组格式'}, status=400)
        
        # 验证每个预约数据
        for i, res_data in enumerate(reservations_data):
            if not isinstance(res_data, dict):
                return JsonResponse({'success': False, 'error': f'第{i+1}个预约数据格式错误'}, status=400)
            
            # 验证必需字段
            title = res_data.get('title', '').strip()
            booker = res_data.get('booker', '').strip()
            date_str = res_data.get('date')
            start_str = res_data.get('start_time') or res_data.get('start')
            end_str = res_data.get('end_time') or res_data.get('end')
            room_id = res_data.get('room')
            
            if not title:
                return JsonResponse({'success': False, 'error': f'第{i+1}个预约的标题不能为空'}, status=400)
            
            if not booker:
                return JsonResponse({'success': False, 'error': f'第{i+1}个预约的预约人不能为空'}, status=400)
            
            if not date_str:
                return JsonResponse({'success': False, 'error': f'第{i+1}个预约的日期不能为空'}, status=400)
            
            if not start_str or not end_str:
                return JsonResponse({'success': False, 'error': f'第{i+1}个预约的时间不能为空'}, status=400)
            
            if not room_id:
                return JsonResponse({'success': False, 'error': f'第{i+1}个预约的会议室不能为空'}, status=400)
            
            # 验证日期格式
            try:
                date_obj = datetime.date.fromisoformat(date_str)
            except ValueError:
                return JsonResponse({'success': False, 'error': f'第{i+1}个预约的日期格式错误'}, status=400)
            
            # 验证时间格式
            try:
                start_time = datetime.datetime.strptime(start_str, '%H:%M').time()
                end_time = datetime.datetime.strptime(end_str, '%H:%M').time()
            except ValueError:
                return JsonResponse({'success': False, 'error': f'第{i+1}个预约的时间格式错误'}, status=400)
            
            # 验证时间逻辑
            if start_time >= end_time:
                return JsonResponse({'success': False, 'error': f'第{i+1}个预约的开始时间必须早于结束时间'}, status=400)
            
            # 验证会议室存在
            try:
                Room.objects.get(id=room_id)
            except Room.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'第{i+1}个预约的会议室不存在'}, status=400)
        
        # 获取现有数据统计
        existing_count = Reservation.objects.count()
        new_count = len(reservations_data)
        
        # 批量删除安全检查
        if existing_count > 0 and new_count < existing_count * 0.5:
            return JsonResponse({
                'success': False, 
                'error': f'安全检查失败：新数据量({new_count})显著少于现有数据量({existing_count})，可能存在数据丢失风险。如确需执行此操作，请先手动备份数据。'
            }, status=400)
        
        # 备份功能已移除 - 不再自动备份
        
        # 使用事务确保数据一致性
        with transaction.atomic():
            # 获取所有现有的预约ID
            existing_ids = set(Reservation.objects.values_list('id', flat=True))
            received_ids = set()
            
            for res_data in reservations_data:
                res_id = res_data.get('id')
                
                # 解析日期和时间
                date_str = res_data.get('date')
                date_obj = datetime.date.fromisoformat(date_str)
                
                start_str = res_data.get('start_time') or res_data.get('start')
                start_time = datetime.datetime.strptime(start_str, '%H:%M').time()
                
                end_str = res_data.get('end_time') or res_data.get('end')
                end_time = datetime.datetime.strptime(end_str, '%H:%M').time()
                
                # 获取房间
                room_id = res_data.get('room')
                room = Room.objects.get(id=room_id)
                    
                if res_id:
                    received_ids.add(int(res_id))
                    # 更新现有预约
                    try:
                        reservation = Reservation.objects.get(id=res_id)
                        
                        # 检查是否有变化
                        has_changed, change_reason = has_reservation_changed(reservation, res_data, room)
                        
                        # 更新数据
                        reservation.room = room
                        reservation.date = date_obj
                        reservation.start_time = start_time
                        reservation.end_time = end_time
                        reservation.title = res_data.get('title', '')
                        reservation.booker = res_data.get('booker', '')
                        reservation.department = res_data.get('department', '')
                        reservation.save()
                        
                        # 只有真正有变化时才发送编辑通知
                        if has_changed:
                            logger.info(f"预约ID {res_id} 有变化，发送编辑通知。变化原因: {change_reason}")
                            success, error_msg = send_wechat_notification(reservation, '编辑')
                            if not success:
                                logger.warning(f"编辑通知发送失败: {error_msg}")
                        else:
                            logger.debug(f"预约ID {res_id} 无变化，跳过通知发送")
                            
                    except Reservation.DoesNotExist:
                        # 如果ID不存在，创建新预约
                        new_reservation = Reservation.objects.create(
                            id=res_id,
                            room=room,
                            date=date_obj,
                            start_time=start_time,
                            end_time=end_time,
                            title=res_data.get('title', ''),
                            booker=res_data.get('booker', ''),
                            department=res_data.get('department', '')
                        )
                        # 发送新增通知（这是真正的新增）
                        logger.info(f"创建新预约ID {res_id}，发送新增通知")
                        success, error_msg = send_wechat_notification(new_reservation, '新增')
                        if not success:
                            logger.warning(f"新增通知发送失败: {error_msg}")
                else:
                    # 创建新预约（没有ID的情况）
                    new_res = Reservation.objects.create(
                        room=room,
                        date=date_obj,
                        start_time=start_time,
                        end_time=end_time,
                        title=res_data.get('title', ''),
                        booker=res_data.get('booker', ''),
                        department=res_data.get('department', '')
                    )
                    received_ids.add(new_res.id)
                    # 发送新增通知（这是真正的新增）
                    logger.info(f"创建新预约ID {new_res.id}，发送新增通知")
                    success, error_msg = send_wechat_notification(new_res, '新增')
                    if not success:
                        logger.warning(f"新增通知发送失败: {error_msg}")
            
            # 删除未接收到的预约
            ids_to_delete = existing_ids - received_ids
            if ids_to_delete:
                deleted_reservations = list(Reservation.objects.filter(id__in=ids_to_delete))
                # 发送删除通知
                for reservation in deleted_reservations:
                    logger.info(f"删除预约ID {reservation.id}，发送删除通知")
                    success, error_msg = send_wechat_notification(reservation, '删除')
                    if not success:
                        logger.warning(f"删除通知发送失败: {error_msg}")
                
                Reservation.objects.filter(id__in=ids_to_delete).delete()
                logger.warning(f"删除预约: {len(ids_to_delete)}条记录")
        
        logger.info("预约数据保存成功")
        return JsonResponse({
            'success': True, 
            'message': '预约数据保存成功'
        })
        
    except Exception as e:
        error_msg = f"保存预约数据失败: {str(e)}"
        logger.error(error_msg)
        return JsonResponse({'success': False, 'error': error_msg}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_settings(request):
    """保存设置数据"""
    try:
        data = json.loads(request.body)
        
        # 支持两种数据格式：直接键值对 或 settings数组
        if 'settings' in data:
            # 测试页面格式：{"settings": [{"key": "...", "value": "..."}]}
            for setting in data['settings']:
                Settings.objects.update_or_create(
                    key=setting['key'],
                    defaults={'value': setting['value']}
                )
        else:
            # 原有格式：{"key1": "value1", "key2": "value2"}
            for key, value in data.items():
                Settings.objects.update_or_create(
                    key=key,
                    defaults={'value': value}
                )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
