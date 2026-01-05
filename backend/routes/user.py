"""
用户个人中心路由模块
提供用户信息管理、收藏列表、发布视频列表等API接口
"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, User, Video
import os
import uuid

# 创建用户蓝图
user_bp = Blueprint('user', __name__)

# 允许的头像文件扩展名
ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_avatar_file(filename):
    """
    检查上传的头像文件是否为允许的类型
    参数:
        filename: 文件名
    返回:
        bool: 是否允许
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS


@user_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    获取当前登录用户的详细信息
    参数: user_id (查询参数 - 前端需传入已登录用户ID)
    返回: 用户详细信息（含头像URL、昵称等）
    """
    try:
        # 获取查询参数中的user_id
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                'code': 400,
                'msg': '缺少参数：user_id'
            }), 400
        
        # 查询用户
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


@user_bp.route('/me', methods=['PUT'])
def update_current_user():
    """
    修改当前用户资料
    接收表单数据:
        - user_id: 用户ID (必填)
        - nickname: 新昵称 (可选)
        - password: 新密码 (可选)
        - avatar: 头像文件 (可选)
    返回: 更新后的用户信息
    """
    try:
        # 获取用户ID（支持表单和JSON两种方式）
        user_id = request.form.get('user_id') or (request.get_json() or {}).get('user_id')
        
        if not user_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必填字段：user_id'
            }), 400
        
        # 查询用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'code': 404,
                'msg': '用户不存在'
            }), 404
        
        # 更新昵称
        nickname = request.form.get('nickname')
        if nickname:
            nickname = nickname.strip()
            if len(nickname) < 2 or len(nickname) > 50:
                return jsonify({
                    'code': 400,
                    'msg': '昵称长度需要在2-50个字符之间'
                }), 400
            user.nickname = nickname
        
        # 更新密码
        password = request.form.get('password')
        if password:
            if len(password) < 6:
                return jsonify({
                    'code': 400,
                    'msg': '密码长度至少6位'
                }), 400
            user.set_password(password)
        
        # 处理头像上传
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file and avatar_file.filename:
                # 验证文件类型
                if not allowed_avatar_file(avatar_file.filename):
                    return jsonify({
                        'code': 400,
                        'msg': '头像格式不支持，仅支持 png, jpg, jpeg, gif, webp'
                    }), 400
                
                # 生成安全的文件名
                ext = avatar_file.filename.rsplit('.', 1)[1].lower()
                new_filename = f"{uuid.uuid4().hex}.{ext}"
                
                # 保存路径
                avatar_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
                os.makedirs(avatar_folder, exist_ok=True)
                avatar_path = os.path.join(avatar_folder, new_filename)
                
                # 保存文件
                avatar_file.save(avatar_path)
                
                # 更新数据库中的头像路径（存储相对路径，不包含/static/前缀）
                user.avatar = f"avatars/{new_filename}"
        
        # 提交更改
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '资料更新成功',
            'data': user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@user_bp.route('/me/videos', methods=['GET'])
def get_my_videos():
    """
    获取当前用户发布的视频列表
    参数: user_id (查询参数)
    返回: 用户上传的所有视频（含各种状态）
    """
    try:
        # 获取用户ID
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                'code': 400,
                'msg': '缺少参数：user_id'
            }), 400
        
        # 验证用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'code': 404,
                'msg': '用户不存在'
            }), 404
        
        # 查询用户发布的视频，按时间倒序
        videos = Video.query.filter_by(user_id=user_id).order_by(
            Video.created_at.desc()
        ).all()
        
        # 转换为字典列表，并添加完整的URL
        video_list = []
        for video in videos:
            video_data = video.to_dict(include_author=False)
            # 添加完整的封面和视频URL
            video_data['cover_url'] = f"http://localhost:5001/static/{video.cover_path}"
            video_data['video_url'] = f"http://localhost:5001/static/{video.video_path}"
            video_list.append(video_data)
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'total': len(video_list),
                'list': video_list
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@user_bp.route('/me/collections', methods=['GET'])
def get_my_collections():
    """
    获取当前用户收藏的视频列表
    参数: user_id (查询参数)
    返回: 用户收藏的所有已发布视频
    """
    try:
        # 获取用户ID
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                'code': 400,
                'msg': '缺少参数：user_id'
            }), 400
        
        # 验证用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'code': 404,
                'msg': '用户不存在'
            }), 404
        
        # 通过 favorites 关系获取收藏的视频
        # 只返回已发布的视频
        collected_videos = user.favorites.filter(
            Video.status == Video.STATUS_PUBLISHED
        ).order_by(Video.created_at.desc()).all()
        
        # 转换为字典列表，并添加完整的URL
        video_list = []
        for video in collected_videos:
            video_data = video.to_dict(include_author=True)
            # 添加完整的封面和视频URL
            video_data['cover_url'] = f"http://localhost:5001/static/{video.cover_path}"
            video_data['video_url'] = f"http://localhost:5001/static/{video.video_path}"
            video_list.append(video_data)
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'total': len(video_list),
                'list': video_list
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user_info(user_id):
    """
    获取指定用户的信息和视频列表（作者主页）
    参数: user_id (路径参数)
    返回: 用户信息和已发布的视频列表
    """
    try:
        # 查询用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'code': 404,
                'msg': '用户不存在'
            }), 404
        
        # 查询用户发布的已发布状态的视频，按时间倒序
        videos = Video.query.filter_by(
            user_id=user_id, 
            status=Video.STATUS_PUBLISHED
        ).order_by(Video.created_at.desc()).all()
        
        # 转换为字典列表，并添加完整的URL
        video_list = []
        for video in videos:
            video_data = video.to_dict(include_author=False)
            # 添加完整的封面和视频URL
            video_data['cover_url'] = f"http://localhost:5001/static/{video.cover_path}"
            video_data['video_url'] = f"http://localhost:5001/static/{video.video_path}"
            video_list.append(video_data)
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'user': user.to_dict(),
                'videos': {
                    'total': len(video_list),
                    'list': video_list
                }
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500
