FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建静态文件目录
RUN mkdir -p staticfiles

# 收集静态文件
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# 创建启动脚本
RUN echo '#!/bin/bash\n\
touch /tmp/db.sqlite3\n\
python manage.py makemigrations booking\n\
python manage.py migrate\n\
python manage.py loaddata booking/fixtures/initial_data.json\n\
gunicorn --bind 0.0.0.0:8000 wsgi:application' > /app/start.sh && \
chmod +x /app/start.sh

# 使用启动脚本运行应用
CMD ["/app/start.sh"]
