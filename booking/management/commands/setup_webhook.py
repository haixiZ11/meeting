from django.core.management.base import BaseCommand
from booking.models import Settings


class Command(BaseCommand):
    help = '配置企业微信Webhook URL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='企业微信Webhook URL',
            default='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=91e68cb7-a244-43d4-a2e0-0d20a9a72712'
        )

    def handle(self, *args, **options):
        webhook_url = options['url']
        
        # 创建或更新webhook_url设置
        webhook_setting, created = Settings.objects.get_or_create(
            key='webhook_url',
            defaults={'value': webhook_url}
        )
        
        if not created:
            webhook_setting.value = webhook_url
            webhook_setting.save()
            self.stdout.write(
                self.style.SUCCESS(f'已更新企业微信Webhook URL: {webhook_url}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'已创建企业微信Webhook URL配置: {webhook_url}')
            )
        
        # 同时创建debug_mode设置（如果不存在）
        debug_setting, debug_created = Settings.objects.get_or_create(
            key='debug_mode',
            defaults={'value': 'false'}
        )
        
        if debug_created:
            self.stdout.write(
                self.style.SUCCESS('已创建debug_mode配置，默认值为false')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Webhook配置完成！现在可以接收企业微信通知了。')
        )