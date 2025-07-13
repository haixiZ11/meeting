# 构建并运行 Docker 容器
docker-compose up --build

# 构建镜像
docker build -t meeting-system .

# 运行容器
docker run -p 8000:8000 meeting-system