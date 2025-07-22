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
python manage.py makemigrations booking\n\
python manage.py migrate\n\
# 只在数据库为空时加载初始数据\n\
if [ ! -s /app/data/db.sqlite3 ] || [ ! -f /app/data/db.sqlite3 ]; then\n\
    echo "Loading initial data..."\n\
    python manage.py loaddata booking/fixtures/initial_data.json\n\
fi\n\
# 收集静态文件\n\
python manage.py collectstatic --noinput\n\
# 启动服务器\n\
python manage.py runserver 0.0.0.0:8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# 使用启动脚本运行应用
CMD ["/bin/bash", "/app/start.sh"]