"""
互动路由模块
提供评论、点赞等用户互动功能API接口
"""
from flask import Blueprint, request, jsonify
from models import db, Comment, Like, Video, User

# 创建互动蓝图
interaction_bp = Blueprint('interaction', __name__)


@interaction_bp.route('/videos/<int:video_id>/comments', methods=['POST'])
def create_comment(video_id):
    """
    发表评论接口
    接收JSON: {user_id, content, parent_id(可选)}
    Root ID 计算逻辑：
    - 一级评论：root_id = None
    - 回复评论：root_id = 父评论的root_id 或 父评论的id（如果父评论是一级评论）
    返回: 创建的评论信息
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必填字段
        if not data or not data.get('user_id') or not data.get('content'):
            return jsonify({
                'code': 400,
                'msg': '缺少必填字段：user_id、content'
            }), 400
        
        user_id = data.get('user_id')
        content = data.get('content').strip()
        parent_id = data.get('parent_id')  # 可选，回复时传入
        
        # 验证评论内容不能为空
        if not content:
            return jsonify({
                'code': 400,
                'msg': '评论内容不能为空'
            }), 400
        
        # 验证视频是否存在
        video = Video.query.get(video_id)
        if not video:
            return jsonify({
                'code': 404,
                'msg': '视频不存在'
            }), 404
        
        # 验证用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'code': 404,
                'msg': '用户不存在'
            }), 404
        
        # 计算 root_id
        root_id = None
        if parent_id:
            # 查询父评论
            parent_comment = Comment.query.get(parent_id)
            if not parent_comment:
                return jsonify({
                    'code': 404,
                    'msg': '父评论不存在'
                }), 404
            
            # 验证父评论属于同一视频
            if parent_comment.video_id != video_id:
                return jsonify({
                    'code': 400,
                    'msg': '父评论不属于该视频'
                }), 400
            
            # Root ID 计算逻辑
            if parent_comment.root_id is None:
                # 父评论是一级评论，则 root_id = parent_id
                root_id = parent_id
            else:
                # 父评论也是回复，则 root_id = 父评论的 root_id
                root_id = parent_comment.root_id
        
        # 创建新评论
        new_comment = Comment(
            content=content,
            user_id=user_id,
            video_id=video_id,
            parent_id=parent_id,
            root_id=root_id
        )
        
        # 保存到数据库
        db.session.add(new_comment)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '评论成功',
            'data': new_comment.to_dict(include_author=True)
        }), 201
    
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@interaction_bp.route('/videos/<int:video_id>/like/status', methods=['GET'])
def get_like_status(video_id):
    """
    获取用户对视频的点赞状态
    参数: user_id (查询参数)
    返回: 当前用户是否已点赞该视频
    """
    try:
        # 获取查询参数
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                'code': 400,
                'msg': '缺少参数：user_id'
            }), 400
        
        # 验证视频是否存在
        video = Video.query.get(video_id)
        if not video:
            return jsonify({
                'code': 404,
                'msg': '视频不存在'
            }), 404
        
        # 检查是否已点赞
        existing_like = Like.query.filter_by(
            user_id=user_id,
            video_id=video_id
        ).first()
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'liked': existing_like is not None
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@interaction_bp.route('/videos/<int:video_id>/comments', methods=['GET'])
def get_comments(video_id):
    """
    获取视频评论列表接口
    查询该视频下的所有评论，按创建时间排序
    返回: 评论列表（包含用户信息：昵称、头像）
    """
    try:
        # 验证视频是否存在
        video = Video.query.get(video_id)
        if not video:
            return jsonify({
                'code': 404,
                'msg': '视频不存在'
            }), 404
        
        # 查询该视频的所有评论，按创建时间升序排列
        comments = Comment.query.filter_by(
            video_id=video_id
        ).order_by(
            Comment.created_at.asc()
        ).all()
        
        # 转换为字典列表，包含作者信息
        comment_list = [comment.to_dict(include_author=True) for comment in comments]
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'total': len(comment_list),
                'list': comment_list
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@interaction_bp.route('/videos/<int:video_id>/like', methods=['POST'])
def toggle_like(video_id):
    """
    点赞/取消点赞接口
    接收JSON: {user_id}
    逻辑：如果已点赞则取消，未点赞则添加
    返回: 当前点赞状态和视频最新点赞总数
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必填字段
        if not data or not data.get('user_id'):
            return jsonify({
                'code': 400,
                'msg': '缺少必填字段：user_id'
            }), 400
        
        user_id = data.get('user_id')
        
        # 验证视频是否存在
        video = Video.query.get(video_id)
        if not video:
            return jsonify({
                'code': 404,
                'msg': '视频不存在'
            }), 404
        
        # 验证用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'code': 404,
                'msg': '用户不存在'
            }), 404
        
        # 检查是否已存在点赞记录
        existing_like = Like.query.filter_by(
            user_id=user_id,
            video_id=video_id
        ).first()
        
        if existing_like:
            # 已存在点赞记录，取消点赞
            db.session.delete(existing_like)
            db.session.commit()
            liked = False
            msg = '取消点赞成功'
        else:
            # 不存在点赞记录，添加点赞
            new_like = Like(
                user_id=user_id,
                video_id=video_id
            )
            db.session.add(new_like)
            db.session.commit()
            liked = True
            msg = '点赞成功'
        
        # 获取视频最新点赞总数
        likes_count = video.get_likes_count()
        
        return jsonify({
            'code': 200,
            'msg': msg,
            'data': {
                'liked': liked,
                'likes_count': likes_count
            }
        }), 200
    
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500
