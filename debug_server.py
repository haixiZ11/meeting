import os
import sys
import traceback

# 将当前目录添加到sys.path
sys.path.insert(0, '.')

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

try:
    print("尝试导入Django...")
    import django
    print(f"Django版本: {django.get_version()}")
    
    print("\n尝试获取数据库配置...")
    from django.conf import settings
    print(f"数据库引擎: {settings.DATABASES['default']['ENGINE']}")
    print(f"数据库路径: {settings.DATABASES['default']['NAME']}")
    print(f"数据库文件存在: {os.path.exists(settings.DATABASES['default']['NAME'])}")
    
    print("\n尝试从django.core.management导入execute_from_command_line...")
    from django.core.management import execute_from_command_line
    print("导入execute_from_command_line成功!")
    
    print("\n尝试启动服务器...")
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
except Exception as e:
    print(f"错误: {e}")
    print("\n详细错误信息:")
    traceback.print_exc() 