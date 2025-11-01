FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=settings

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p /app/data
# 创建静态文件目录
RUN mkdir -p /app/static
# 创建日志目录
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 8000

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "Starting Django application..."\n\
\n\
# 数据库迁移\n\
echo "Running database migrations..."\n\
python manage.py makemigrations booking\n\
python manage.py migrate\n\
\n\
# 安全的数据加载\n\
echo "Checking for initial data..."\n\
# 检查是否需要加载初始数据（仅在数据库完全为空时）\n\
ROOM_COUNT=$(python manage.py shell -c "from booking.models import Room; print(Room.objects.count())")\n\
if [ "$ROOM_COUNT" = "0" ]; then\n\
    echo "Database is empty, checking for initial data fixture..."\n\
    if [ -f "/app/booking/fixtures/initial_data.json" ]; then\n\
        echo "Loading initial data safely..."\n\
        python manage.py safe_loaddata booking/fixtures/initial_data.json --verify\n\
        if [ $? -eq 0 ]; then\n\
            echo "Initial data loaded successfully"\n\
        else\n\
            echo "Warning: Initial data loading failed, continuing without initial data"\n\
        fi\n\
    else\n\
        echo "No initial data fixture found, starting with empty database"\n\
        echo "Please create meeting rooms through Django admin interface"\n\
    fi\n\
else\n\
    echo "Database contains $ROOM_COUNT rooms, skipping initial data loading"\n\
fi\n\
\n\
# 收集静态文件\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput\n\
\n\
# 启动服务器\n\
echo "Starting Django development server..."\n\
python manage.py runserver 0.0.0.0:8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# 使用启动脚本运行应用
CMD ["/bin/bash", "/app/start.sh"]