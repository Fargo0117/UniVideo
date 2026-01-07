"""
用户认证路由模块
提供用户注册、登录等认证相关API接口
"""
from flask import Blueprint, request, jsonify
from models import db, User

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口
    接收JSON: {username, password, nickname}
    返回: 注册成功信息或错误信息
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必填字段
        if not data or not data.get('username') or not data.get('password') or not data.get('nickname'):
            return jsonify({
                'code': 400,
                'msg': '缺少必填字段：username、password、nickname'
            }), 400
        
        username = data.get('username').strip()
        password = data.get('password')
        nickname = data.get('nickname').strip()
        
        # 验证用户名长度
        if len(username) < 3 or len(username) > 50:
            return jsonify({
                'code': 400,
                'msg': '用户名长度必须在3-50个字符之间'
            }), 400
        
        # 验证密码强度
        if len(password) < 6:
            return jsonify({
                'code': 400,
                'msg': '密码长度至少6位'
            }), 400
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({
                'code': 409,
                'msg': '用户名已存在，请更换'
            }), 409
        
        # 创建新用户
        new_user = User(
            username=username,
            nickname=nickname,
            role='user'  # 默认角色为普通用户
        )
        # 使用模型方法加密密码
        new_user.set_password(password)
        
        # 保存到数据库
        db.session.add(new_user)
        db.session.commit()
        
        # 返回成功信息
        return jsonify({
            'code': 200,
            'msg': '注册成功',
            'data': {
                'id': new_user.id,
                'username': new_user.username,
                'nickname': new_user.nickname
            }
        }), 201
    
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    接收JSON: {username, password}
    返回: 用户信息（简化版，不使用JWT Token）
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必填字段
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'code': 400,
                'msg': '缺少必填字段：username、password'
            }), 400
        
        username = data.get('username').strip()
        password = data.get('password')
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        # 验证用户是否存在
        if not user:
            return jsonify({
                'code': 401,
                'msg': '用户名或密码错误'
            }), 401
        
        # 验证密码
        if not user.check_password(password):
            return jsonify({
                'code': 401,
                'msg': '用户名或密码错误'
            }), 401
        
        # 检查用户状态：如果被封禁，不允许登录
        if user.status == 0:
            return jsonify({
                'code': 403,
                'msg': '该账号因违反社区规定已被封禁，无法登录。如有申诉请联系管理员。'
            }), 403
        
        # 登录成功，返回用户信息（仅当 status == 1 时）
        return jsonify({
            'code': 200,
            'msg': '登录成功',
            'data': {
                'id': user.id,
                'username': user.username,
                'nickname': user.nickname,
                'role': user.role,
                'avatar': user.avatar
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    获取当前登录用户信息接口
    （简化版：通过请求头中的 user_id 获取）
    """
    try:
        # 从请求头获取 user_id（前端 localStorage 存储）
        user_id = request.headers.get('X-User-Id')
        
        if not user_id:
            return jsonify({
                'code': 401,
                'msg': '未登录或登录已过期'
            }), 401
        
        # 查找用户
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'code': 404,
                'msg': '用户不存在'
            }), 404
        
        # 返回用户信息
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': user.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500
