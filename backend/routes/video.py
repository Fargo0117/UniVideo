"""
视频路由模块
提供视频上传、列表查询、详情获取等API接口
"""
from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from datetime import datetime
from models import db, Video, Category, User

# 创建视频蓝图
video_bp = Blueprint('video', __name__)


@video_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    获取所有视频分类
    用于前端上传页面的分类下拉框
    返回: [{"id": 1, "name": "校园生活"}, ...]
    """
    try:
        categories = Category.query.all()
        return jsonify({
            'code': 200,
            'msg': '获取分类成功',
            'data': [category.to_dict() for category in categories]
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@video_bp.route('/upload', methods=['POST'])
def upload_video():
    """
    视频上传接口（核心功能）
    接收 multipart/form-data 数据
    参数: user_id, title, description, category_id, video_file, cover_file
    返回: 上传成功信息
    """
    try:
        # 获取表单数据
        user_id = request.form.get('user_id')
        title = request.form.get('title')
        description = request.form.get('description', '')
        category_id = request.form.get('category_id')
        
        # 验证必填字段
        if not all([user_id, title, category_id]):
            return jsonify({
                'code': 400,
                'msg': '缺少必填字段：user_id、title、category_id'
            }), 400
        
        # 验证文件是否存在
        if 'video_file' not in request.files or 'cover_file' not in request.files:
            return jsonify({
                'code': 400,
                'msg': '缺少必传文件：video_file、cover_file'
            }), 400
        
        video_file = request.files['video_file']
        cover_file = request.files['cover_file']
        
        # 验证文件是否为空
        if video_file.filename == '' or cover_file.filename == '':
            return jsonify({
                'code': 400,
                'msg': '文件不能为空'
            }), 400
        
        # 验证用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'code': 404,
                'msg': '用户不存在'
            }), 404
        
        # 验证分类是否存在
        category = Category.query.get(category_id)
        if not category:
            return jsonify({
                'code': 404,
                'msg': '分类不存在'
            }), 404
        
        # 获取文件扩展名
        video_ext = os.path.splitext(video_file.filename)[1].lower()
        cover_ext = os.path.splitext(cover_file.filename)[1].lower()
        
        # 验证视频文件格式
        if video_ext[1:] not in current_app.config['ALLOWED_VIDEO_EXTENSIONS']:
            return jsonify({
                'code': 400,
                'msg': f'不支持的视频格式，允许的格式: {", ".join(current_app.config["ALLOWED_VIDEO_EXTENSIONS"])}'
            }), 400
        
        # 验证封面图片格式
        if cover_ext[1:] not in current_app.config['ALLOWED_IMAGE_EXTENSIONS']:
            return jsonify({
                'code': 400,
                'msg': f'不支持的图片格式，允许的格式: {", ".join(current_app.config["ALLOWED_IMAGE_EXTENSIONS"])}'
            }), 400
        
        # 生成唯一文件名：时间戳 + UUID（防止文件名冲突）
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        video_filename = f"{timestamp}_{unique_id}{video_ext}"
        cover_filename = f"{timestamp}_{unique_id}{cover_ext}"
        
        # 构建文件保存路径
        video_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'videos', video_filename)
        cover_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'covers', cover_filename)
        
        # 保存文件到服务器
        video_file.save(video_save_path)
        cover_file.save(cover_save_path)
        
        # 数据库存储的相对路径
        video_db_path = f"videos/{video_filename}"
        cover_db_path = f"covers/{cover_filename}"
        
        # 创建视频记录（status 默认为 0 = 待审核）
        new_video = Video(
            user_id=int(user_id),
            category_id=int(category_id),
            title=title,
            description=description,
            video_path=video_db_path,
            cover_path=cover_db_path,
            status=Video.STATUS_PENDING  # 0 = 待审核（实现先审后发机制）
        )
        
        # 写入数据库
        db.session.add(new_video)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '视频上传成功，等待管理员审核',
            'data': {
                'id': new_video.id,
                'title': new_video.title,
                'status': new_video.status
            }
        }), 201
    
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@video_bp.route('/list', methods=['GET'])
def get_video_list():
    """
    获取视频列表（仅已发布状态）
    参数: category_id (可选，用于分类筛选)
    返回: 视频列表（包含作者昵称、分类名、封面URL）
    """
    try:
        # 获取可选的分类筛选参数
        category_id = request.args.get('category_id', type=int)
        
        # 构建查询：只查询 status=1 (已发布) 的视频
        query = Video.query.filter_by(status=Video.STATUS_PUBLISHED)
        
        # 如果提供了分类ID，则按分类筛选
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        # 按上传时间倒序排列
        videos = query.order_by(Video.created_at.desc()).all()
        
        # 构建返回数据，包含完整的 URL
        video_list = []
        for video in videos:
            video_data = video.to_dict(include_author=True)
            # 添加完整的封面和视频URL
            video_data['cover_url'] = f"http://localhost:5001/static/{video.cover_path}"
            video_data['video_url'] = f"http://localhost:5001/static/{video.video_path}"
            video_list.append(video_data)
        
        return jsonify({
            'code': 200,
            'msg': '获取视频列表成功',
            'data': video_list
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@video_bp.route('/<int:id>', methods=['GET'])
def get_video_detail(id):
    """
    获取视频详情
    参数: id (视频ID)
    逻辑: 
    - 每次请求将 view_count +1
    - TODO: status=0 的视频仅允许上传者本人或管理员查看（权限判断）
    """
    try:
        # 查询视频
        video = Video.query.get(id)
        
        if not video:
            return jsonify({
                'code': 404,
                'msg': '视频不存在'
            }), 404
        
        # TODO: 权限判断
        # if video.status == Video.STATUS_PENDING:
        #     # 获取当前用户ID（从请求头或Token中）
        #     current_user_id = request.headers.get('X-User-Id')
        #     current_user = User.query.get(current_user_id) if current_user_id else None
        #     
        #     # 只有上传者本人或管理员可以查看待审核视频
        #     if not current_user or (current_user.id != video.user_id and not current_user.is_admin()):
        #         return jsonify({
        #             'code': 403,
        #             'msg': '该视频正在审核中，暂时无法查看'
        #         }), 403
        
        # 每次访问，播放量 +1
        video.view_count += 1
        db.session.commit()
        
        # 构建返回数据
        video_data = video.to_dict(include_author=True)
        video_data['cover_url'] = f"http://localhost:5001/static/{video.cover_path}"
        video_data['video_url'] = f"http://localhost:5001/static/{video.video_path}"
        
        return jsonify({
            'code': 200,
            'msg': '获取视频详情成功',
            'data': video_data
        }), 200
    
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500
