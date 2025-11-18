import os

class Config:
    # Agora配置（需要替换为实际的App ID和Certificate）
    AGORA_APP_ID = os.getenv('AGORA_APP_ID', '87e86c2155aa461fab6f68e7fa519498')
    AGORA_APP_CERTIFICATE = os.getenv('AGORA_APP_CERTIFICATE', '7726c35606cc41979e588e07de4f67ee')
    
    # 应用配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'abcdefg0123456')
    UPLOAD_FOLDER = 'recordings'
    DATABASE = 'meeting.db'
    
    # 支持的文件扩展名
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv'}