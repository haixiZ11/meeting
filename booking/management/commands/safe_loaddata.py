"""
安全的数据加载管理命令
在加载数据前进行备份和验证，确保数据安全
"""
import os
import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction
from django.conf import settings
from booking.models import Room, Reservation, Settings
from booking.backup_manager import BackupManager

# 配置日志
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '安全地加载初始数据，包含备份和验证机制'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'fixture_file',
            type=str,
            help='要加载的fixture文件路径'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制加载数据，即使已存在数据'
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            default=True,
            help='在加载前创建备份（默认启用）'
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            default=True,
            help='加载后验证数据完整性（默认启用）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅验证fixture文件，不实际加载数据'
        )
    
    def handle(self, *args, **options):
        fixture_file = options['fixture_file']
        force = options['force']
        create_backup = options['backup']
        verify_data = options['verify']
        dry_run = options['dry_run']
        
        try:
            # 1. 验证fixture文件
            self.stdout.write('正在验证fixture文件...')
            if not self.validate_fixture_file(fixture_file):
                raise CommandError(f'Fixture文件验证失败: {fixture_file}')
            
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'Fixture文件验证通过: {fixture_file}')
                )
                return
            
            # 2. 检查现有数据
            existing_data = self.check_existing_data()
            if existing_data and not force:
                self.stdout.write(
                    self.style.WARNING(
                        '检测到现有数据：\n'
                        f'  会议室: {existing_data["rooms"]} 个\n'
                        f'  预约: {existing_data["reservations"]} 个\n'
                        f'  设置: {existing_data["settings"]} 个\n\n'
                        '使用 --force 参数强制加载数据'
                    )
                )
                return
            
            # 3. 创建备份
            backup_file = None
            if create_backup and existing_data:
                self.stdout.write('正在创建数据备份...')
                backup_manager = BackupManager()
                backup_file = backup_manager.create_backup(
                    backup_type='manual',
                    description=f'数据加载前的自动备份 - {fixture_file}'
                )
                self.stdout.write(
                    self.style.SUCCESS(f'备份已创建: {backup_file}')
                )
            
            # 4. 在事务中加载数据
            self.stdout.write('正在加载数据...')
            with transaction.atomic():
                try:
                    # 使用Django的loaddata命令
                    call_command('loaddata', fixture_file, verbosity=0)
                    
                    # 5. 验证数据完整性
                    if verify_data:
                        self.stdout.write('正在验证数据完整性...')
                        if not self.verify_loaded_data():
                            raise CommandError('数据完整性验证失败')
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'数据加载成功: {fixture_file}'
                        )
                    )
                    
                except Exception as e:
                    # 如果有备份，提示可以恢复
                    if backup_file:
                        self.stdout.write(
                            self.style.ERROR(
                                f'数据加载失败: {str(e)}\n'
                                f'可以使用以下命令恢复备份:\n'
                                f'python manage.py restore_backup {backup_file}'
                            )
                        )
                    raise
                    
        except Exception as e:
            logger.error(f'安全数据加载失败: {str(e)}')
            raise CommandError(f'数据加载失败: {str(e)}')
    
    def validate_fixture_file(self, fixture_file):
        """验证fixture文件格式和内容"""
        try:
            # 检查文件是否存在
            if not os.path.exists(fixture_file):
                self.stdout.write(
                    self.style.ERROR(f'Fixture文件不存在: {fixture_file}')
                )
                return False
            
            # 验证JSON格式
            with open(fixture_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                self.stdout.write(
                    self.style.ERROR('Fixture文件格式错误：应为JSON数组')
                )
                return False
            
            # 验证数据结构
            valid_models = ['booking.room', 'booking.reservation', 'booking.settings']
            for item in data:
                if not isinstance(item, dict):
                    self.stdout.write(
                        self.style.ERROR('Fixture项格式错误：应为对象')
                    )
                    return False
                
                if 'model' not in item or 'fields' not in item:
                    self.stdout.write(
                        self.style.ERROR('Fixture项缺少必需字段：model或fields')
                    )
                    return False
                
                if item['model'] not in valid_models:
                    self.stdout.write(
                        self.style.WARNING(f'未知模型: {item["model"]}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Fixture文件验证通过，包含 {len(data)} 个数据项')
            )
            return True
            
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Fixture文件JSON格式错误: {str(e)}')
            )
            return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'验证fixture文件时出错: {str(e)}')
            )
            return False
    
    def check_existing_data(self):
        """检查现有数据"""
        try:
            rooms_count = Room.objects.count()
            reservations_count = Reservation.objects.count()
            settings_count = Settings.objects.count()
            
            if rooms_count > 0 or reservations_count > 0 or settings_count > 0:
                return {
                    'rooms': rooms_count,
                    'reservations': reservations_count,
                    'settings': settings_count
                }
            return None
            
        except Exception as e:
            logger.error(f'检查现有数据时出错: {str(e)}')
            return None
    
    def verify_loaded_data(self):
        """验证加载的数据完整性"""
        try:
            # 验证会议室数据
            rooms = Room.objects.all()
            for room in rooms:
                if not room.name or not room.name.strip():
                    self.stdout.write(
                        self.style.ERROR(f'会议室名称为空: ID {room.id}')
                    )
                    return False
                
                if room.capacity <= 0:
                    self.stdout.write(
                        self.style.ERROR(f'会议室容量无效: {room.name}')
                    )
                    return False
            
            # 验证预约数据
            reservations = Reservation.objects.all()
            for reservation in reservations:
                if not reservation.room:
                    self.stdout.write(
                        self.style.ERROR(f'预约缺少会议室: ID {reservation.id}')
                    )
                    return False
                
                if reservation.start_time >= reservation.end_time:
                    self.stdout.write(
                        self.style.ERROR(f'预约时间无效: ID {reservation.id}')
                    )
                    return False
            
            self.stdout.write(
                self.style.SUCCESS('数据完整性验证通过')
            )
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'数据完整性验证失败: {str(e)}')
            )
            return False