

## 1. 配置说明

### 1.1 MinIO服务器配置

MinIO服务器的配置信息存储在`config/settings.json`文件中，包含以下字段：

```json
{
    "minio": {
        "endpoint": "服务器地址:端口",
        "access_key": "访问密钥",
        "secret_key": "秘密密钥",
        "bucket": "存储桶名称",
        "secure": false  // 是否使用HTTPS
    }
}
```

## 2. 核心功能

### 2.1 文件分享

主要通过`MinioService`类提供的`get_presigned_url`方法实现文件分享功能：

```python
def get_presigned_url(self, object_name: str, expires: timedelta = timedelta(hours=1)) -> Optional[str]:
    """
    获取文件的预签名URL
    
    参数:
    - object_name: 文件在MinIO中的对象名称
    - expires: 链接有效期，默认1小时
    
    返回:
    - 成功返回预签名URL字符串
    - 失败返回None
    """
```

### 2.2 文件管理功能

#### 列出文件
```python
def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
    """
    列出指定前缀的所有文件
    
    返回文件信息列表，每个文件包含:
    - name: 文件名
    - size: 文件大小
    - last_modified: 最后修改时间
    - content_type: 内容类型
    - metadata: 元数据
    """
```

#### 上传文件
```python
def upload_file(self, file_path: str, object_name: Optional[str] = None) -> bool:
    """
    上传文件到MinIO
    
    参数:
    - file_path: 本地文件路径
    - object_name: MinIO中的对象名称（可选，默认使用文件名）
    """
```

#### 下载文件
```python
def download_file(self, object_name: str, file_path: str) -> bool:
    """
    从MinIO下载文件
    
    参数:
    - object_name: MinIO中的对象名称
    - file_path: 保存到本地的文件路径
    """
```

#### 删除文件
```python
def delete_file(self, object_name: str) -> bool:
    """
    删除MinIO中的文件
    
    参数:
    - object_name: 要删除的文件对象名称
    """
```

### 2.3 文件夹操作

#### 创建文件夹
```python
def create_folder(self, folder_name: str) -> bool:
    """
    在MinIO中创建文件夹
    
    参数:
    - folder_name: 文件夹名称（会自动添加结尾的'/'）
    """
```

#### 重命名文件
```python
def rename_file(self, old_name: str, new_name: str) -> bool:
    """
    重命名MinIO中的文件
    
    参数:
    - old_name: 原文件名
    - new_name: 新文件名
    """
```

## 3. 错误处理

所有的操作都包含了错误处理机制：
- 操作失败时会打印错误信息
- 通过日志系统记录错误
- 返回布尔值表示操作是否成功

## 4. 使用示例

```python
# 初始化服务
config_manager = ConfigManager()
minio_service = MinioService(config_manager)

# 获取文件分享链接
share_url = minio_service.get_presigned_url("example.pdf", timedelta(hours=24))
if share_url:
    print(f"文件分享链接: {share_url}")
else:
    print("获取分享链接失败")

# 上传文件
success = minio_service.upload_file("local_file.txt", "remote_file.txt")
if success:
    print("文件上传成功")
```

## 5. 注意事项

1. 确保MinIO服务器配置正确，包括endpoint、access_key和secret_key
2. 分享链接有默认的过期时间（1小时），可以通过参数调整
3. 文件操作前会自动验证与MinIO服务器的连接
4. 所有操作都有日志记录，方便追踪问题
5. 文件夹操作实际上是创建空对象，因为MinIO是对象存储系统

## 6. 常见问题解答

### 6.1 连接问题
- 确保服务器地址和端口正确
- 检查access_key和secret_key是否有效
- 验证网络连接是否正常

### 6.2 文件操作问题
- 上传失败：检查文件权限和存储空间
- 下载失败：确认文件存在且有访问权限
- 分享链接失效：检查链接的有效期设置

## 7. 更新日志

### v1.0.0
- 初始版本发布
- 实现基本的文件管理功能
- 添加文件分享功能
- 支持文件夹操作 