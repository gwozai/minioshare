from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from minio import Minio
from datetime import timedelta
import json
import os
from dotenv import load_dotenv
import logging
from io import BytesIO
from math import ceil
from functools import wraps

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

# 每页显示的文件数量
FILES_PER_PAGE = 10

# MinIO configuration from environment variables
MINIO_CONFIG = {
    'endpoint': os.getenv('MINIO_ENDPOINT', '106.12.107.176:19000'),
    'access_key': os.getenv('MINIO_ACCESS_KEY', 'minio'),
    'secret_key': os.getenv('MINIO_SECRET_KEY', 'ei2BEHZYLaR8eGtT'),
    'bucket': os.getenv('MINIO_BUCKET', 'album'),
    'secure': os.getenv('MINIO_SECURE', 'False').lower() == 'true'
}

# Access password
ACCESS_PASSWORD = os.getenv('ACCESS_PASSWORD', 'minioshare123')

def get_minio_client():
    """Get MinIO client from configuration"""
    try:
        client = Minio(
            endpoint=MINIO_CONFIG['endpoint'],
            access_key=MINIO_CONFIG['access_key'],
            secret_key=MINIO_CONFIG['secret_key'],
            secure=MINIO_CONFIG['secure']
        )
        return client
    except Exception as e:
        logger.error("Error creating MinIO client: %s", str(e))
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ACCESS_PASSWORD:
            session['logged_in'] = True
            flash('Login successful', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Home page - show file list with pagination and sorting"""
    client = get_minio_client()
    if not client:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'error': 'Error connecting to MinIO server',
                'objects': [],
                'pagination': {
                    'page': 1,
                    'totalPages': 0,
                    'totalFiles': 0,
                    'hasPrev': False,
                    'hasNext': False,
                    'sortBy': 'date',
                    'order': 'desc'
                },
                'is_admin': True
            })
        else:
            flash("Error connecting to MinIO server", "error")
            return render_template('index.html', is_admin=True)
    
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        sort_by = request.args.get('sort', 'date')  # 'date', 'name', 'size'
        order = request.args.get('order', 'desc')   # 'asc', 'desc'
        
        # List objects in the configured bucket
        bucket = MINIO_CONFIG['bucket']
        objects = []
        logger.debug("Checking bucket existence: %s", bucket)
        
        if client.bucket_exists(bucket):
            logger.debug("Bucket exists, listing objects")
            # 获取所有对象
            for obj in client.list_objects(bucket):
                try:
                    # 检查对象是否以斜杠结尾（目录）
                    if obj.object_name.endswith('/'):
                        objects.append({
                            'name': obj.object_name,
                            'size': 0,
                            'last_modified': obj.last_modified.isoformat() if obj.last_modified else None,
                            'is_directory': True
                        })
                    else:
                        stat = client.stat_object(bucket, obj.object_name)
                        objects.append({
                            'name': obj.object_name,
                            'size': stat.size,
                            'last_modified': stat.last_modified.isoformat() if stat.last_modified else None,
                            'is_directory': False
                        })
                except Exception as stat_error:
                    logger.error("Error getting object stats: %s", str(stat_error))
                    # 如果获取状态失败，仍然添加基本信息
                    objects.append({
                        'name': obj.object_name,
                        'size': 0,
                        'last_modified': obj.last_modified.isoformat() if obj.last_modified else None,
                        'is_directory': obj.object_name.endswith('/')
                    })
            
            # 排序
            if sort_by == 'date':
                objects.sort(key=lambda x: x['last_modified'] or '', reverse=(order == 'desc'))
            elif sort_by == 'name':
                objects.sort(key=lambda x: x['name'].lower(), reverse=(order == 'desc'))
            elif sort_by == 'size':
                # 目录始终排在文件前面
                objects.sort(key=lambda x: (not x['is_directory'], x['size']), reverse=(order == 'desc'))
            
            # 分页
            total_files = len(objects)
            total_pages = ceil(total_files / FILES_PER_PAGE)
            page = min(max(1, page), total_pages) if total_pages > 0 else 1
            
            start_idx = (page - 1) * FILES_PER_PAGE
            end_idx = start_idx + FILES_PER_PAGE
            paginated_objects = objects[start_idx:end_idx]
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'objects': paginated_objects,
                    'pagination': {
                        'page': page,
                        'totalPages': total_pages,
                        'totalFiles': total_files,
                        'hasPrev': page > 1,
                        'hasNext': page < total_pages,
                        'sortBy': sort_by,
                        'order': order
                    },
                    'is_admin': True
                })
            else:
                return render_template('index.html', is_admin=True)
        else:
            logger.warning("Bucket does not exist: %s", bucket)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'error': f"Bucket '{bucket}' does not exist",
                    'objects': [],
                    'pagination': {
                        'page': 1,
                        'totalPages': 0,
                        'totalFiles': 0,
                        'hasPrev': False,
                        'hasNext': False,
                        'sortBy': sort_by,
                        'order': order
                    },
                    'is_admin': True
                })
            else:
                flash(f"Bucket '{bucket}' does not exist", "error")
                return render_template('index.html', is_admin=True)
    except Exception as e:
        logger.error("Error listing files: %s", str(e), exc_info=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'error': str(e),
                'objects': [],
                'pagination': {
                    'page': 1,
                    'totalPages': 0,
                    'totalFiles': 0,
                    'hasPrev': False,
                    'hasNext': False,
                    'sortBy': 'date',
                    'order': 'desc'
                },
                'is_admin': True
            })
        else:
            flash(f"Error listing files: {str(e)}", "error")
            return render_template('index.html', is_admin=True)

@app.route('/share/<path:object_name>')
@login_required
def share_file(object_name):
    """Generate a presigned URL for file sharing"""
    logger.debug("Generating share URL for object: %s", object_name)
    client = get_minio_client()
    if not client:
        return jsonify({'error': 'Error connecting to MinIO server'}), 400
    
    try:
        url = client.presigned_get_object(
            bucket_name=MINIO_CONFIG['bucket'],
            object_name=object_name,
            expires=timedelta(hours=1)
        )
        logger.debug("Generated share URL: %s", url)
        return jsonify({'url': url})
    except Exception as e:
        logger.error("Error generating share URL: %s", str(e), exc_info=True)
        return jsonify({'error': str(e)}), 400

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        logger.warning("No file provided in request")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.warning("Empty filename provided")
        return jsonify({'error': 'No file selected'}), 400
    
    logger.debug("Processing upload for file: %s", file.filename)
    client = get_minio_client()
    if not client:
        return jsonify({'error': 'Error connecting to MinIO server'}), 400
    
    try:
        # 读取文件内容到内存
        file_data = file.read()
        file_size = len(file_data)
        logger.debug("File size: %d bytes", file_size)
        logger.debug("Content type: %s", file.content_type)
        
        # 创建一个BytesIO对象，这样可以重新读取文件内容
        file_stream = BytesIO(file_data)
        
        # 上传文件
        client.put_object(
            bucket_name=MINIO_CONFIG['bucket'],
            object_name=file.filename,
            data=file_stream,
            length=file_size,
            content_type=file.content_type or 'application/octet-stream'
        )
        logger.info("Successfully uploaded file: %s", file.filename)
        return jsonify({'message': 'File uploaded successfully'})
    except Exception as e:
        logger.error("Error uploading file: %s", str(e), exc_info=True)
        return jsonify({'error': str(e)}), 400

@app.route('/test-config', methods=['POST'])
def test_config():
    """Test MinIO configuration"""
    try:
        config = request.json
        client = get_minio_client()
        if not client:
            return jsonify({'success': False, 'error': 'Failed to create MinIO client'})
        
        # 测试bucket是否存在
        if not client.bucket_exists(config['bucket']):
            return jsonify({'success': False, 'error': f"Bucket '{config['bucket']}' does not exist"})
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Ensure the bucket exists
    client = get_minio_client()
    if client:
        bucket = MINIO_CONFIG['bucket']
        logger.info("Checking if bucket exists: %s", bucket)
        if not client.bucket_exists(bucket):
            logger.info("Creating bucket: %s", bucket)
            client.make_bucket(bucket)
    
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true') 