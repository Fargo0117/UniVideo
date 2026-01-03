"""
UniVideo 后端主应用入口
提供视频分享平台的核心API服务
"""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
import os

# 导入配置和数据库模型
from config import config
from models import db

# 创建Flask应用实例
def create_app(config_name='development'):
    """
    应用工厂函数：创建并配置Flask应用
    参数:
        config_name: 配置环境名称 ('development', 'testing', 'production')
    返回:
        配置好的Flask应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)  # 初始化SQLAlchemy
    migrate = Migrate(app, db)  # 初始化Flask-Migrate数据库迁移工具
    CORS(app)  # 初始化CORS，允许前端跨域访问
    
    # 确保上传目录存在
    with app.app_context():
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'covers'), exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
    
    # 注册蓝图 (Blueprints)
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # 注册视频路由蓝图
    from routes.video import video_bp
    app.register_blueprint(video_bp, url_prefix='/api/videos')
    
    return app

# 创建应用实例
app = create_app(os.environ.get('FLASK_ENV') or 'development')


@app.route('/')
def index():
    """
    根路由：测试API服务是否正常运行
    """
    return "UniVideo API is running..."


@app.route('/api/health')
def health_check():
    """
    健康检查接口：用于监控服务状态和数据库连接
    """
    from sqlalchemy import text
    try:
        # 测试数据库连接
        db.session.execute(text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'service': 'UniVideo Backend',
        'database': db_status,
        'version': '1.0.0'
    })


if __name__ == '__main__':
    # 开发模式运行，启用调试和自动重载
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=5001,       # 后端服务端口
        debug=True       # 开启调试模式
    )
