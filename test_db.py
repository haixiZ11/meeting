import os
import sys
from pathlib import Path

# 获取项目根目录路径
BASE_DIR = Path(__file__).resolve().parent.parent

# 构建数据库路径
DB_PATH = os.path.join(BASE_DIR, "meeting", "data", "db.sqlite3")
print(f"数据库路径: {DB_PATH}")
print(f"数据库文件是否存在: {os.path.exists(DB_PATH)}")

# 尝试连接数据库
try:
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    print("成功连接到数据库!")
    conn.close()
except Exception as e:
    print(f"连接数据库时出错: {e}")

# 列出数据目录内容
data_dir = os.path.join(BASE_DIR, "meeting", "data")
print(f"\n数据目录 ({data_dir}) 内容:")
if os.path.exists(data_dir):
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isfile(item_path):
            print(f"  文件: {item} ({os.path.getsize(item_path)} 字节)")
        else:
            print(f"  目录: {item}")
else:
    print("  数据目录不存在!") 