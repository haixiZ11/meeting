"""
备份恢复管理命令
从备份文件恢复数据
"""
import os
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from booking.backup_manager import BackupManager

# 配置日志
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '从备份文件恢复数据'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='要恢复的备份文件名（不含路径）'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制恢复，覆盖现有数据'
        )
        parser.add_argument(
            '--backup-current',
            action='store_true',
            default=True,
            help='恢复前备份当前数据（默认启用）'
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            default=True,
            help='恢复后验证数据完整性（默认启用）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅验证备份文件，不实际恢复数据'
        )
    
    def handle(self, *args, **options):
        backup_file = options['backup_file']
        force = options['force']
        backup_current = options['backup_current']
        verify_data = options['verify']
        dry_run = options['dry_run']
        
        try:
            backup_manager = BackupManager()
            
            # 1. 验证备份文件
            self.stdout.write('正在验证备份文件...')
            if not backup_manager.validate_backup(backup_file):
                raise CommandError(f'备份文件验证失败: {backup_file}')
            
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'备份文件验证通过: {backup_file}')
                )
                return
            
            # 2. 检查现有数据
            from booking.models import Room, Reservation, Settings
            existing_rooms = Room.objects.count()
            existing_reservations = Reservation.objects.count()
            existing_settings = Settings.objects.count()
            
            if (existing_rooms > 0 or existing_reservations > 0 or existing_settings > 0) and not force:
                self.stdout.write(
                    self.style.WARNING(
                        '检测到现有数据：\n'
                        f'  会议室: {existing_rooms} 个\n'
                        f'  预约: {existing_reservations} 个\n'
                        f'  设置: {existing_settings} 个\n\n'
                        '使用 --force 参数强制恢复数据'
                    )
                )
                return
            
            # 3. 备份当前数据
            current_backup_file = None
            if backup_current and (existing_rooms > 0 or existing_reservations > 0 or existing_settings > 0):
                self.stdout.write('正在备份当前数据...')
                current_backup_file = backup_manager.create_backup(
                    backup_type='manual',
                    description=f'恢复前的自动备份 - {backup_file}'
                )
                self.stdout.write(
                    self.style.SUCCESS(f'当前数据备份已创建: {current_backup_file}')
                )
            
            # 4. 在事务中恢复数据
            self.stdout.write('正在恢复数据...')
            with transaction.atomic():
                try:
                    success = backup_manager.restore_backup(backup_file)
                    if not success:
                        raise CommandError('数据恢复失败')
                    
                    # 5. 验证数据完整性
                    if verify_data:
                        self.stdout.write('正在验证数据完整性...')
                        if not backup_manager.validate_data_integrity():
                            raise CommandError('数据完整性验证失败')
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'数据恢复成功: {backup_file}'
                        )
                    )
                    
                    # 显示恢复后的数据统计
                    rooms_count = Room.objects.count()
                    reservations_count = Reservation.objects.count()
                    settings_count = Settings.objects.count()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'恢复后数据统计：\n'
                            f'  会议室: {rooms_count} 个\n'
                            f'  预约: {reservations_count} 个\n'
                            f'  设置: {settings_count} 个'
                        )
                    )
                    
                except Exception as e:
                    # 如果有当前数据备份，提示可以恢复
                    if current_backup_file:
                        self.stdout.write(
                            self.style.ERROR(
                                f'数据恢复失败: {str(e)}\n'
                                f'可以使用以下命令恢复到恢复前状态:\n'
                                f'python manage.py restore_backup {current_backup_file}'
                            )
                        )
                    raise
                    
        except Exception as e:
            logger.error(f'备份恢复失败: {str(e)}')
            raise CommandError(f'备份恢复失败: {str(e)}')