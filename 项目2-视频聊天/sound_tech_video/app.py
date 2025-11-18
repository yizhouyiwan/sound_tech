from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import json
import os
import uuid
from datetime import datetime
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# 配置
CONFIG = {
    'AGORA_APP_ID': '87e86c2155aa461fab6f68e7fa519498',
    'AGORA_APP_CERTIFICATE': '7726c35606cc41979e588e07de4f67ee',
    'UPLOAD_FOLDER': 'recordings',
    'DATABASE': 'meeting.db'
}

# 初始化数据库
def init_db():
    conn = sqlite3.connect(CONFIG['DATABASE'])
    c = conn.cursor()
    
    # 创建房间表
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id TEXT PRIMARY KEY,
            room_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # 创建录制表
    c.execute('''
        CREATE TABLE IF NOT EXISTS recordings (
            id TEXT PRIMARY KEY,
            room_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT DEFAULT 'stopped',
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Agora token 生成
def generate_agora_token(channel_name, uid):
    from agora_token_builder import RtcTokenBuilder
    import time
    
    app_id = CONFIG['AGORA_APP_ID']
    app_certificate = CONFIG['AGORA_APP_CERTIFICATE']
    channel_name = str(channel_name)
    uid = uid or 0
    role = 1  # 1: host, 2: audience
    privilege_expired_ts = int(time.time()) + 3600  # 1小时过期
    
    token = RtcTokenBuilder.buildTokenWithUid(
        app_id, app_certificate, channel_name, uid, role, privilege_expired_ts
    )
    return token

# API路由
@app.route('/')
def index():
    return send_file('index.html')  # 返回前端页面
@app.route('/api/v1/rooms', methods=['POST'])
def create_room():
    """创建音视频房间"""
    try:
        data = request.get_json()
        room_name = data.get('room_name', f'room_{uuid.uuid4().hex[:8]}')
        user_id = data.get('user_id', 0)
        
        room_id = str(uuid.uuid4())
        
        # 生成Agora token
        token = generate_agora_token(room_id, user_id)
        
        # 保存到数据库
        conn = sqlite3.connect(CONFIG['DATABASE'])
        c = conn.cursor()
        c.execute(
            'INSERT INTO rooms (id, room_name) VALUES (?, ?)',
            (room_id, room_name)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'room_id': room_id,
            'room_name': room_name,
            'token': token,
            'app_id': CONFIG['AGORA_APP_ID']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/rooms/<room_id>/join', methods=['POST'])
def join_room(room_id):
    """加入音视频房间"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 0)
        
        # 检查房间是否存在
        conn = sqlite3.connect(CONFIG['DATABASE'])
        c = conn.cursor()
        c.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
        room = c.fetchone()
        conn.close()
        
        if not room:
            return jsonify({
                'success': False,
                'error': 'Room not found'
            }), 404
        
        # 生成token
        token = generate_agora_token(room_id, user_id)
        
        return jsonify({
            'success': True,
            'room_id': room_id,
            'token': token,
            'app_id': CONFIG['AGORA_APP_ID']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/rooms/<room_id>/record/start', methods=['POST'])
def start_recording(room_id):
    """开始录制"""
    try:
        # 在实际应用中，这里应该调用Agora云录制API
        # 这里简化实现，只记录元数据
        
        recording_id = str(uuid.uuid4())
        file_path = os.path.join(CONFIG['UPLOAD_FOLDER'], f'{recording_id}.mp4')
        
        # 确保目录存在
        os.makedirs(CONFIG['UPLOAD_FOLDER'], exist_ok=True)
        
        conn = sqlite3.connect(CONFIG['DATABASE'])
        c = conn.cursor()
        c.execute(
            'INSERT INTO recordings (id, room_id, file_path, start_time, status) VALUES (?, ?, ?, ?, ?)',
            (recording_id, room_id, file_path, datetime.now(), 'recording')
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'recording_id': recording_id,
            'message': 'Recording started'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/rooms/<room_id>/record/stop', methods=['POST'])
def stop_recording(room_id):
    """停止录制"""
    try:
        data = request.get_json()
        recording_id = data.get('recording_id')
        
        if not recording_id:
            return jsonify({
                'success': False,
                'error': 'Recording ID is required'
            }), 400
        
        conn = sqlite3.connect(CONFIG['DATABASE'])
        c = conn.cursor()
        c.execute(
            'UPDATE recordings SET end_time = ?, status = ? WHERE id = ?',
            (datetime.now(), 'stopped', recording_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Recording stopped'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/recordings/<recording_id>', methods=['GET'])
def get_recording(recording_id):
    """获取录制文件信息"""
    try:
        conn = sqlite3.connect(CONFIG['DATABASE'])
        c = conn.cursor()
        c.execute('SELECT * FROM recordings WHERE id = ?', (recording_id,))
        recording = c.fetchone()
        conn.close()
        
        if not recording:
            return jsonify({
                'success': False,
                'error': 'Recording not found'
            }), 404
        
        # 返回录制信息
        return jsonify({
            'success': True,
            'recording': {
                'id': recording[0],
                'room_id': recording[1],
                'file_path': recording[2],
                'start_time': recording[3],
                'end_time': recording[4],
                'status': recording[5]
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/recordings/<recording_id>/download', methods=['GET'])
def download_recording(recording_id):
    """下载录制文件"""
    try:
        conn = sqlite3.connect(CONFIG['DATABASE'])
        c = conn.cursor()
        c.execute('SELECT file_path FROM recordings WHERE id = ?', (recording_id,))
        recording = c.fetchone()
        conn.close()
        
        if not recording or not os.path.exists(recording[0]):
            return jsonify({
                'success': False,
                'error': 'Recording file not found'
            }), 404
        
        return send_file(recording[0], as_attachment=True)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'webm', 'mp4', 'avi'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/v1/recordings/upload', methods=['POST'])
def upload_recording():
    """上传录制文件"""
    try:
        if 'recording' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['recording']
        room_id = request.form.get('room_id', 'unknown')
        user_id = request.form.get('user_id', '0')
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if file and allowed_file(file.filename):
            # 生成唯一文件名
            filename = secure_filename(file.filename)
            file_extension = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            # 确保录制目录存在
            os.makedirs(CONFIG['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(CONFIG['UPLOAD_FOLDER'], unique_filename)
            
            # 保存文件
            file.save(file_path)
            
            # 记录到数据库
            recording_id = str(uuid.uuid4())
            conn = sqlite3.connect(CONFIG['DATABASE'])
            c = conn.cursor()
            c.execute(
                '''INSERT INTO recordings 
                   (id, room_id, file_path, start_time, end_time, status) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (recording_id, room_id, file_path, 
                 datetime.now(), datetime.now(), 'completed')
            )
            conn.commit()
            conn.close()
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            return jsonify({
                'success': True,
                'recording_id': recording_id,
                'file_path': file_path,
                'file_size': file_size,
                'message': 'Recording uploaded successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid file type'
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/recordings/list', methods=['GET'])
def list_recordings():
    """获取录制文件列表"""
    try:
        conn = sqlite3.connect(CONFIG['DATABASE'])
        c = conn.cursor()
        c.execute('''
            SELECT r.id, r.room_id, r.file_path, r.start_time, r.end_time, 
                   rm.room_name, r.status 
            FROM recordings r 
            LEFT JOIN rooms rm ON r.room_id = rm.id 
            ORDER BY r.start_time DESC
        ''')
        recordings = c.fetchall()
        conn.close()
        
        recording_list = []
        for rec in recordings:
            file_exists = os.path.exists(rec[2]) if rec[2] else False
            file_size = os.path.getsize(rec[2]) if file_exists else 0
            
            recording_list.append({
                'id': rec[0],
                'room_id': rec[1],
                'file_path': rec[2],
                'start_time': rec[3],
                'end_time': rec[4],
                'room_name': rec[5],
                'status': rec[6],
                'file_exists': file_exists,
                'file_size': file_size
            })
        
        return jsonify({
            'success': True,
            'recordings': recording_list
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    
@app.route('/api/v1/recordings/<recording_id>', methods=['DELETE'])
def delete_recording(recording_id):
    """删除录制文件"""
    try:
        conn = sqlite3.connect(CONFIG['DATABASE'])
        c = conn.cursor()
        
        # 获取文件路径
        c.execute('SELECT file_path FROM recordings WHERE id = ?', (recording_id,))
        recording = c.fetchone()
        
        if not recording:
            return jsonify({
                'success': False,
                'error': 'Recording not found'
            }), 404
        
        # 删除数据库记录
        c.execute('DELETE FROM recordings WHERE id = ?', (recording_id,))
        conn.commit()
        conn.close()
        
        # 删除物理文件
        file_path = recording[0]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': 'Recording deleted successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)