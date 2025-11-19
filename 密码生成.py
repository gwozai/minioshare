import random
import string
import logging

# 设置日志配置
logging.basicConfig(filename='minio_user_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def generate_random_string(length=10, include_special=False):
    """生成随机字符串"""
    chars = string.ascii_letters + string.digits
    if include_special:
        chars += string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

# 生成随机用户名（10 位，字母+数字）
username = generate_random_string(10)

# 生成随机密码（12 位，只用字母+数字，不包含特殊字符）
password = generate_random_string(12, include_special=False)

# 输出 MinIO 创建用户命令
create_command = f"mc admin user add myminio {username} {password}"
print("生成的 MinIO 创建用户命令：")
print(create_command)

# 输出分配策略命令
attach_command = f"mc admin policy attach myminio consoleAdmin --user={username}"
print("生成的 MinIO 分配策略命令：")
print(attach_command)

# 记录到日志
logging.info(f"用户名: {username}")
logging.info(f"密码: {password}")
logging.info(f"创建命令: {create_command}")
logging.info(f"分配命令: {attach_command}")