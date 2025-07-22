# Etek会议室预约系统

一个基于Django的会议室预约管理系统，支持会议室预约、管理和状态查看功能。
##
![image](https://github.com/haixiZ11/meeting/blob/main/data/%E9%A6%96%E9%A1%B5.png)
## 项目特点

- 会议室预约与管理
- 实时显示会议室状态
- 响应式设计，支持移动端和桌面端
- 管理员后台，方便管理会议室和预约
- 日历视图，直观查看会议室使用情况

## 技术栈

- 后端：Django 4.2.7
- 前端：HTML, CSS, JavaScript
- 容器化：Docker

## 安装与运行

### 方式一：使用Docker（推荐）

1. 确保已安装Docker和Docker Compose
2. 克隆项目到本地
3. 在项目根目录下运行：

```bash
# 构建并启动容器
docker-compose up -d

# 查看容器运行状态
docker-compose ps
```

4. 访问 http://localhost:8000 即可使用系统

### 方式二：本地运行

1. 确保已安装Python 3.8+
2. 创建并激活虚拟环境：

```bash
# 创建虚拟环境
python -m venv venv

# Windows激活
venv\Scripts\activate

# Linux/Mac激活
source venv/bin/activate
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 创建静态文件目录：

```bash
mkdir -p static
mkdir -p staticfiles
```

5. 运行数据库迁移：

```bash
python manage.py makemigrations booking
python manage.py migrate
```

6. 收集静态文件：

```bash
python manage.py collectstatic --noinput
```

7. 加载初始数据：

```bash
python manage.py loaddata booking/fixtures/initial_data.json
```

8. 创建超级用户（用于管理后台登录）：

```bash
python manage.py createsuperuser
```

9. 启动开发服务器：

```bash
python manage.py runserver
```

10. 访问 http://127.0.0.1:8000 使用系统
    - 管理后台：http://127.0.0.1:8000/admin/

## 系统使用

### 普通用户

1. 预约会议：选择会议室、日期、时间段，填写会议主题和预约人信息
2. 查看会议室状态：实时显示当前和即将进行的会议
3. 查看日历视图：了解各会议室的使用情况

### 管理员

1. 访问 http://localhost:8000/admin/ 进入Django管理后台
2. 使用超级用户账号登录（需先创建超级用户：`python manage.py createsuperuser`）
3. 管理会议室：添加、编辑、删除会议室
4. 管理预约：查看、删除预约记录
   
5.user：admin   password：meetingadmin

## 项目结构

```
### Django 主项目文件
- `__init__.py` - Python包初始化文件
- `settings.py` - 项目配置设置
- `urls.py` - URL路由配置
- `wsgi.py` - WSGI应用入口
- `asgi.py` - ASGI应用入口
- `manage.py` - Django命令行工具
### 会议室预约模块 (booking)
- `models.py` - 数据模型定义（会议室、预约记录等）
- `views.py` - 视图函数和类
- `urls.py` - URL路由映射
- `admin.py` - 后台管理界面配置
- `forms.py` - 表单定义
- `api.py` - API接口定义
### 模板文件
- `templates/booking/` - 预约系统模板
  - `admin.html` - 管理页面模板
  - `index.html` - 首页模板
  - `room_status.html` - 会议室状态页模板
- `templates/admin/` - 管理后台模板定制
### 静态资源
- `static/css/` - CSS样式文件
- `staticfiles/` - 收集的静态文件
### 数据相关
- `data/` - 数据存储目录
  - `db.sqlite3` - SQLite数据库文件
  - `date.png`, `home.png` - 图片资源
### 部署与配置
- `Dockerfile` - Docker镜像构建配置
- `docker-compose.yml` - Docker Compose配置
- `requirements.txt` - Python依赖包列表
### 初始化数据
- `booking/fixtures/initial_data.json` - 初始数据
```

## 账户信息

首次使用需创建Django超级用户：

```bash
python manage.py createsuperuser
```


