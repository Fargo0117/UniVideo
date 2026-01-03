"""
应用配置文件
包含开发环境、测试环境、生产环境的不同配置
"""
import os

# 基础目录路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """
    基础配置类：所有环境共享的配置
    """
    # 密钥配置：用于session加密和安全功能
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'univideo-secret-key-2026-dev-only-change-in-prod'
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.abspath(os.path.join(BASE_DIR, 'static'))  # 使用绝对路径
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB 最大上传大小
    
    # 允许的文件扩展名
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    
    # 数据库配置：使用 MySQL 数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭SQLAlchemy的事件系统，节省内存
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:lzh20050117@localhost/univideo_db'  # MySQL连接URI


class DevelopmentConfig(Config):
    """
    开发环境配置
    """
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """
    测试环境配置：使用内存数据库进行单元测试
    """
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # 使用内存数据库进行测试，不影响生产数据


class ProductionConfig(Config):
    """
    生产环境配置
    """
    DEBUG = False
    TESTING = False
    # 生产环境必须设置真实的SECRET_KEY
    SECRET_KEY = os.environ.get('SECRET_KEY')


# 配置字典：根据环境变量选择配置
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
