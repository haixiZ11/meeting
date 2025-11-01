"""
数据备份管理器
提供自动备份、恢复和数据完整性检查功能
"""
import os
import json
import shutil
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core import serializers
from django.db import transaction
from .models import Room, Reservation, Settings

logger = logging.getLogger(__name__)

class BackupManager:
    """数据备份管理器"""
    
    def __init__(self):
        self.backup_dir = os.path.join(settings.BASE_DIR, 'data', 'backups')
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """确保备份目录存在"""
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def create_backup(self, backup_type='manual', description=''):
        """
        创建数据备份
        
        Args:
            backup_type: 备份类型 ('manual', 'auto', 'pre_operation')
            description: 备份描述
            
        Returns:
            tuple: (success, backup_file_path, message)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{backup_type}_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # 收集所有数据
            backup_data = {
                'metadata': {
                    'backup_time': datetime.now().isoformat(),
                    'backup_type': backup_type,
                    'description': description,
                    'version': '1.0'
                },
                'rooms': self._serialize_rooms(),
                'reservations': self._serialize_reservations(),
                'settings': self._serialize_settings()
            }
            
            # 写入备份文件
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            # 记录备份信息
            logger.info(f"数据备份成功: {backup_filename}")
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            return True, backup_path, f"备份创建成功: {backup_filename}"
            
        except Exception as e:
            error_msg = f"创建备份失败: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _serialize_rooms(self):
        """序列化会议室数据"""
        rooms = []
        for room in Room.objects.all():
            rooms.append({
                'id': room.id,
                'name': room.name,
                'capacity': room.capacity,
                'description': room.description,
                'equipment': room.equipment,
                'status': room.status
            })
        return rooms
    
    def _serialize_reservations(self):
        """序列化预约数据"""
        reservations = []
        for reservation in Reservation.objects.all():
            reservations.append({
                'id': reservation.id,
                'room_id': reservation.room.id,
                'date': reservation.date.isoformat(),
                'start_time': reservation.start_time.strftime('%H:%M'),
                'end_time': reservation.end_time.strftime('%H:%M'),
                'title': reservation.title,
                'booker': reservation.booker,
                'department': reservation.department,
                'created_at': reservation.created_at.isoformat() if reservation.created_at else None
            })
        return reservations
    
    def _serialize_settings(self):
        """序列化设置数据"""
        settings_data = []
        for setting in Settings.objects.all():
            settings_data.append({
                'key': setting.key,
                'value': setting.value,
                'description': setting.description
            })
        return settings_data
    
    def restore_backup(self, backup_file_path, restore_options=None):
        """
        从备份文件恢复数据
        
        Args:
            backup_file_path: 备份文件路径
            restore_options: 恢复选项 {'rooms': True, 'reservations': True, 'settings': True}
            
        Returns:
            tuple: (success, message)
        """
        if restore_options is None:
            restore_options = {'rooms': True, 'reservations': True, 'settings': True}
        
        try:
            # 在恢复前创建当前数据的备份
            self.create_backup('pre_restore', f'恢复前自动备份 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            
            # 读取备份文件
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            with transaction.atomic():
                # 恢复会议室数据
                if restore_options.get('rooms', True):
                    self._restore_rooms(backup_data.get('rooms', []))
                
                # 恢复预约数据
                if restore_options.get('reservations', True):
                    self._restore_reservations(backup_data.get('reservations', []))
                
                # 恢复设置数据
                if restore_options.get('settings', True):
                    self._restore_settings(backup_data.get('settings', []))
            
            logger.info(f"数据恢复成功: {backup_file_path}")
            return True, "数据恢复成功"
            
        except Exception as e:
            error_msg = f"数据恢复失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _restore_rooms(self, rooms_data):
        """恢复会议室数据"""
        # 清空现有数据
        Room.objects.all().delete()
        
        # 恢复数据
        for room_data in rooms_data:
            Room.objects.create(
                id=room_data['id'],
                name=room_data['name'],
                capacity=room_data['capacity'],
                description=room_data.get('description', ''),
                equipment=room_data.get('equipment', ''),
                status=room_data.get('status', 'available')
            )
    
    def _restore_reservations(self, reservations_data):
        """恢复预约数据"""
        # 清空现有数据
        Reservation.objects.all().delete()
        
        # 恢复数据
        for reservation_data in reservations_data:
            try:
                room = Room.objects.get(id=reservation_data['room_id'])
                Reservation.objects.create(
                    id=reservation_data['id'],
                    room=room,
                    date=datetime.fromisoformat(reservation_data['date']).date(),
                    start_time=datetime.strptime(reservation_data['start_time'], '%H:%M').time(),
                    end_time=datetime.strptime(reservation_data['end_time'], '%H:%M').time(),
                    title=reservation_data['title'],
                    booker=reservation_data['booker'],
                    department=reservation_data.get('department', '')
                )
            except Room.DoesNotExist:
                logger.warning(f"恢复预约时找不到会议室 ID: {reservation_data['room_id']}")
                continue
    
    def _restore_settings(self, settings_data):
        """恢复设置数据"""
        # 清空现有数据
        Settings.objects.all().delete()
        
        # 恢复数据
        for setting_data in settings_data:
            Settings.objects.create(
                key=setting_data['key'],
                value=setting_data['value'],
                description=setting_data.get('description', '')
            )
    
    def _cleanup_old_backups(self, keep_days=30):
        """清理旧备份文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('backup_') and filename.endswith('.json'):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        logger.info(f"清理旧备份文件: {filename}")
                        
        except Exception as e:
            logger.warning(f"清理旧备份文件时出错: {str(e)}")
    
    def list_backups(self):
        """列出所有备份文件"""
        backups = []
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('backup_') and filename.endswith('.json'):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_stat = os.stat(file_path)
                    
                    # 尝试读取备份元数据
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            backup_data = json.load(f)
                            metadata = backup_data.get('metadata', {})
                    except:
                        metadata = {}
                    
                    backups.append({
                        'filename': filename,
                        'file_path': file_path,
                        'size': file_stat.st_size,
                        'created_time': datetime.fromtimestamp(file_stat.st_ctime),
                        'backup_type': metadata.get('backup_type', 'unknown'),
                        'description': metadata.get('description', ''),
                        'rooms_count': len(backup_data.get('rooms', [])) if 'rooms' in locals() else 0,
                        'reservations_count': len(backup_data.get('reservations', [])) if 'reservations' in locals() else 0
                    })
            
            # 按创建时间排序
            backups.sort(key=lambda x: x['created_time'], reverse=True)
            
        except Exception as e:
            logger.error(f"列出备份文件时出错: {str(e)}")
        
        return backups
    
    def validate_data_integrity(self):
        """验证数据完整性"""
        issues = []
        
        try:
            # 检查会议室数据
            rooms = Room.objects.all()
            if not rooms.exists():
                issues.append("警告: 没有会议室数据")
            
            for room in rooms:
                if not room.name or not room.name.strip():
                    issues.append(f"错误: 会议室 ID {room.id} 名称为空")
                if room.capacity <= 0:
                    issues.append(f"错误: 会议室 '{room.name}' 容量无效: {room.capacity}")
            
            # 检查预约数据
            reservations = Reservation.objects.all()
            for reservation in reservations:
                if not reservation.room:
                    issues.append(f"错误: 预约 ID {reservation.id} 关联的会议室不存在")
                if reservation.start_time >= reservation.end_time:
                    issues.append(f"错误: 预约 '{reservation.title}' 时间设置无效")
                if not reservation.title or not reservation.title.strip():
                    issues.append(f"警告: 预约 ID {reservation.id} 标题为空")
                if not reservation.booker or not reservation.booker.strip():
                    issues.append(f"警告: 预约 '{reservation.title}' 预约人为空")
            
            # 检查重复预约
            for reservation in reservations:
                conflicts = Reservation.objects.filter(
                    room=reservation.room,
                    date=reservation.date,
                    start_time__lt=reservation.end_time,
                    end_time__gt=reservation.start_time
                ).exclude(id=reservation.id)
                
                if conflicts.exists():
                    issues.append(f"错误: 预约 '{reservation.title}' 存在时间冲突")
            
        except Exception as e:
            issues.append(f"数据完整性检查时出错: {str(e)}")
        
        return issues

# 全局备份管理器实例
backup_manager = BackupManager()