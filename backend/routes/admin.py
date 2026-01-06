"""
管理员路由模块
提供视频审核、管理等功能API接口
"""
from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from models import db, Video, User, Notification
from datetime import datetime, timedelta
import os
import json

# 创建管理员蓝图
admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """
    管理员权限验证装饰器
    从请求头 X-User-ID 获取用户ID，验证是否为管理员
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 从请求头获取用户ID
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                return jsonify({
                    'code': 401,
                    'msg': '未授权：缺少用户ID'
                }), 401
            
            # 查询用户
            user = User.query.get(int(user_id))
            if not user:
                return jsonify({
                    'code': 401,
                    'msg': '未授权：用户不存在'
                }), 401
            
            # 验证是否为管理员
            if not user.is_admin():
                return jsonify({
                    'code': 403,
                    'msg': '权限不足：仅管理员可访问'
                }), 403
            
            # 将用户对象传递给被装饰的函数
            return f(*args, **kwargs)
        except (ValueError, TypeError):
            return jsonify({
                'code': 400,
                'msg': '无效的用户ID'
            }), 400
        except Exception as e:
            return jsonify({
                'code': 500,
                'msg': f'服务器错误: {str(e)}'
            }), 500
    
    return decorated_function


@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    获取管理员统计数据接口
    返回: 待审核视频数、总用户数、今日新增视频数
    """
    try:
        # 待审核视频数
        pending_videos_count = Video.query.filter_by(status=Video.STATUS_PENDING).count()
        
        # 总用户数
        total_users_count = User.query.count()
        
        # 今日新增视频数（今天0点到现在）
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_new_count = Video.query.filter(Video.created_at >= today_start).count()
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'pending_videos': pending_videos_count,
                'total_users': total_users_count,
                'today_new': today_new_count
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@admin_bp.route('/manage/list', methods=['GET'])
def get_video_list():
    """
    获取视频管理列表接口（升级版）
    参数:
        - keyword (可选): 按标题模糊搜索
        - status (可选): 按状态筛选 (0=待审核, 1=已发布, 2=已驳回)，不传则查询所有
    返回: 视频列表
    """
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        status = request.args.get('status', type=int)  # None 表示不筛选
        
        # 构建查询
        query = Video.query
        
        # 关键词模糊搜索
        if keyword:
            query = query.filter(Video.title.like(f'%{keyword}%'))
        
        # 状态筛选
        if status is not None:
            query = query.filter(Video.status == status)
        
        # 按上传时间倒序排列
        videos = query.order_by(Video.created_at.desc()).all()
        
        # 将视频对象列表转换为字典列表
        video_list = [video.to_dict(include_author=True) for video in videos]
        
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


@admin_bp.route('/audit/list', methods=['GET'])
def get_audit_list():
    """
    获取待审核视频列表接口（保留兼容）
    查询所有 status=0 (待审核) 的视频
    按上传时间正序排列（先传的先审）
    返回: 待审核视频列表
    """
    try:
        # 查询所有待审核视频，按上传时间正序排列（先传的先审）
        pending_videos = Video.query.filter_by(
            status=Video.STATUS_PENDING  # status=0
        ).order_by(
            Video.created_at.asc()  # 按上传时间升序排列
        ).all()
        
        # 将视频对象列表转换为字典列表
        video_list = [video.to_dict(include_author=True) for video in pending_videos]
        
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


@admin_bp.route('/audit/<int:video_id>', methods=['POST'])
def audit_video(video_id):
    """
    视频审核接口
    接收JSON: {action: "approve" | "reject"}
    - approve: 通过审核，设置 status=1
    - reject: 驳回，设置 status=2
    返回: 审核操作结果
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必填字段
        if not data or not data.get('action'):
            return jsonify({
                'code': 400,
                'msg': '缺少必填字段：action'
            }), 400
        
        action = data.get('action')
        
        # 验证 action 值是否合法
        if action not in ['approve', 'reject']:
            return jsonify({
                'code': 400,
                'msg': 'action 参数无效，仅支持 "approve" 或 "reject"'
            }), 400
        
        # 查找视频
        video = Video.query.get(video_id)
        
        if not video:
            return jsonify({
                'code': 404,
                'msg': '视频不存在'
            }), 404
        
        # 检查视频是否处于待审核状态
        if video.status != Video.STATUS_PENDING:
            status_map = {
                Video.STATUS_PUBLISHED: '已发布',
                Video.STATUS_REJECTED: '已驳回'
            }
            current_status = status_map.get(video.status, '未知状态')
            return jsonify({
                'code': 400,
                'msg': f'该视频当前状态为"{current_status}"，无法重复审核'
            }), 400
        
        # 根据 action 设置视频状态
        if action == 'approve':
            video.status = Video.STATUS_PUBLISHED  # 通过审核
            result_msg = '审核通过，视频已发布'
            # 创建通知：视频审核通过
            notification = Notification(
                title='视频审核结果',
                content=f'您的视频《{video.title}》已通过审核并发布',
                msg_type=Notification.MSG_TYPE_AUDIT,
                related_link=f'/video/{video.id}',
                user_id=video.user_id,
                video_id=video.id
            )
            db.session.add(notification)
        else:  # action == 'reject'
            video.status = Video.STATUS_REJECTED   # 驳回
            result_msg = '视频已驳回'
            # 获取驳回理由
            reason = data.get('reason', '')
            reject_content = f'您的视频《{video.title}》未通过审核'
            if reason:
                reject_content += f'，驳回理由：{reason}'
            # 创建通知：视频审核驳回
            notification = Notification(
                title='视频审核结果',
                content=reject_content,
                msg_type=Notification.MSG_TYPE_AUDIT,
                related_link='/upload',  # 驳回后引导用户重新上传
                user_id=video.user_id,
                video_id=video.id,
                extra_data=json.dumps({'reason': reason}) if reason else None
            )
            db.session.add(notification)
        
        # 保存更改到数据库
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': result_msg,
            'data': {
                'video_id': video.id,
                'title': video.title,
                'new_status': video.status
            }
        }), 200
    
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@admin_bp.route('/manage/video/<int:video_id>', methods=['DELETE'])
def delete_video(video_id):
    """
    删除视频接口
    逻辑:
        1. 检查视频是否存在
        2. 尝试删除物理文件（视频和封面）
        3. 从数据库删除记录
    返回: 删除结果
    """
    try:
        # 查找视频
        video = Video.query.get(video_id)
        
        if not video:
            return jsonify({
                'code': 404,
                'msg': '视频不存在'
            }), 404
        
        # 保存视频信息用于返回
        video_title = video.title
        
        # 尝试删除物理文件
        deleted_files = []
        try:
            # 删除视频文件
            if video.video_path:
                video_file_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'], 
                    video.video_path
                )
                if os.path.exists(video_file_path):
                    os.remove(video_file_path)
                    deleted_files.append(video.video_path)
            
            # 删除封面文件
            if video.cover_path:
                cover_file_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'], 
                    video.cover_path
                )
                if os.path.exists(cover_file_path):
                    os.remove(cover_file_path)
                    deleted_files.append(video.cover_path)
        except Exception as file_err:
            # 文件删除失败不影响数据库记录删除，记录日志即可
            print(f'删除物理文件失败: {str(file_err)}')
        
        # 从数据库删除视频记录
        db.session.delete(video)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '视频删除成功',
            'data': {
                'video_id': video_id,
                'title': video_title,
                'deleted_files': deleted_files
            }
        }), 200
    
    except Exception as e:
        # 发生异常时回滚事务
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@admin_bp.route('/notifications/send', methods=['POST'])
def send_notification():
    """
    发送通知接口（仅管理员可用）
    参数:
        - target_username (可选): 接收用户名，如果为空则视为群发/广播（系统通知，所有用户可见）
        - title: 消息标题
        - content: 消息正文
        - msg_type (可选): 消息类型，默认为 'system'，可选值: 'system', 'audit', 'interaction'
        - related_link (可选): 关联链接
    返回: 发送结果
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必填字段
        if not data:
            return jsonify({
                'code': 400,
                'msg': '缺少请求数据'
            }), 400
        
        # 安全地获取并处理字符串字段（处理 None 值）
        title = (data.get('title') or '').strip()
        content = (data.get('content') or '').strip()
        target_username = (data.get('target_username') or '').strip()
        msg_type = data.get('msg_type', Notification.MSG_TYPE_SYSTEM)
        related_link = (data.get('related_link') or '').strip() or None
        
        # 验证必填字段
        if not title:
            return jsonify({
                'code': 400,
                'msg': '缺少必填字段：title'
            }), 400
        
        if not content:
            return jsonify({
                'code': 400,
                'msg': '缺少必填字段：content'
            }), 400
        
        # 验证消息类型
        valid_types = [Notification.MSG_TYPE_SYSTEM, Notification.MSG_TYPE_AUDIT, Notification.MSG_TYPE_INTERACTION]
        if msg_type not in valid_types:
            return jsonify({
                'code': 400,
                'msg': f'msg_type 参数无效，仅支持: {", ".join(valid_types)}'
            }), 400
        
        # 处理用户查找逻辑
        user_id = None
        if target_username:
            # 单发：通过用户名查找用户
            user = User.query.filter_by(username=target_username).first()
            if not user:
                return jsonify({
                    'code': 404,
                    'msg': f'找不到用户: {target_username}'
                }), 404
            user_id = user.id
        # 如果 target_username 为空，user_id 保持为 None，表示系统通知（群发）
        
        # 创建通知
        notification = Notification(
            title=title,
            content=content,
            msg_type=msg_type,
            related_link=related_link,
            user_id=user_id  # 如果为None，表示系统通知（群发，所有用户可见）
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '消息已送达',
            'data': {
                'notification_id': notification.id,
                'title': notification.title,
                'msg_type': notification.msg_type,
                'user_id': notification.user_id,
                'target_username': target_username if target_username else '全体用户'
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@admin_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """
    获取通知列表接口
    参数:
        - user_id (可选): 用户ID，如果传入则返回该用户的个人通知 + 所有系统通知（全员广播）
        - is_read (可选): 是否已读筛选 (true/false)
        - limit (可选): 返回数量限制，默认20
        - offset (可选): 偏移量，默认0
    返回: 通知列表（包含个人通知和系统通知）
    """
    try:
        # 获取查询参数
        user_id = request.args.get('user_id', type=int)
        is_read = request.args.get('is_read')
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 构建查询：如果传了 user_id，同时获取个人通知和系统通知
        if user_id:
            # 获取个人通知（user_id 匹配）或系统通知（user_id 为 NULL）
            query = Notification.query.filter(
                db.or_(
                    Notification.user_id == user_id,
                    Notification.user_id.is_(None)  # 系统通知（全员广播）
                )
            )
        else:
            # 如果没有指定用户ID，只返回系统通知（user_id为NULL）
            query = Notification.query.filter(Notification.user_id.is_(None))
        
        # 已读状态筛选
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            query = query.filter(Notification.is_read == is_read_bool)
        
        # 按创建时间倒序排列
        query = query.order_by(Notification.created_at.desc())
        
        # 总数
        total = query.count()
        
        # 分页
        notifications = query.offset(offset).limit(limit).all()
        
        # 转换为字典列表
        notification_list = [notif.to_dict(include_video=True) for notif in notifications]
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'total': total,
                'list': notification_list
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@admin_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    """
    标记通知为已读接口
    返回: 操作结果
    """
    try:
        # 查找通知
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return jsonify({
                'code': 404,
                'msg': '通知不存在'
            }), 404
        
        # 标记为已读
        notification.is_read = True
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '标记成功',
            'data': {
                'notification_id': notification_id,
                'is_read': True
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@admin_bp.route('/notifications/read-all', methods=['PUT'])
def mark_all_notifications_read():
    """
    标记所有通知为已读接口
    参数:
        - user_id (可选): 用户ID，如果传入则标记该用户的个人通知和系统通知
    返回: 操作结果
    """
    try:
        # 获取查询参数
        user_id = request.args.get('user_id', type=int)
        
        # 构建查询：如果传了 user_id，同时标记个人通知和系统通知
        query = Notification.query.filter_by(is_read=False)
        
        if user_id:
            # 标记个人未读通知（user_id 匹配）或系统未读通知（user_id 为 NULL）
            query = query.filter(
                db.or_(
                    Notification.user_id == user_id,
                    Notification.user_id.is_(None)  # 系统通知（全员广播）
                )
            )
        else:
            # 如果没有指定用户ID，只标记系统通知
            query = query.filter(Notification.user_id.is_(None))
        
        # 批量更新
        updated_count = query.update({'is_read': True})
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '标记成功',
            'data': {
                'updated_count': updated_count
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@admin_bp.route('/notifications/unread-count', methods=['GET'])
def get_unread_count():
    """
    获取未读通知数量接口
    参数:
        - user_id (可选): 用户ID，如果传入则返回该用户的个人未读通知 + 所有系统未读通知
    返回: 未读通知数量
    """
    try:
        # 获取查询参数
        user_id = request.args.get('user_id', type=int)
        
        # 构建查询：如果传了 user_id，同时统计个人通知和系统通知
        if user_id:
            # 统计个人未读通知（user_id 匹配）或系统未读通知（user_id 为 NULL）
            query = Notification.query.filter_by(is_read=False).filter(
                db.or_(
                    Notification.user_id == user_id,
                    Notification.user_id.is_(None)  # 系统通知（全员广播）
                )
            )
        else:
            # 如果没有指定用户ID，只统计系统通知未读数
            query = Notification.query.filter_by(is_read=False).filter(
                Notification.user_id.is_(None)
            )
        
        count = query.count()
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'unread_count': count
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """
    获取用户列表接口
    参数:
        - page (可选): 页码，默认1
        - per_page (可选): 每页数量，默认10
        - keyword (可选): 搜索关键词（用户名模糊搜索）
    返回: 用户列表和分页信息
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        keyword = request.args.get('keyword', '').strip()
        
        # 限制每页数量范围
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        # 构建查询
        query = User.query
        
        # 关键词搜索（用户名模糊匹配）
        if keyword:
            query = query.filter(User.username.like(f'%{keyword}%'))
        
        # 按创建时间倒序排列
        query = query.order_by(User.created_at.desc())
        
        # 分页查询
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 转换为字典列表
        user_list = [user.to_dict() for user in pagination.items]
        
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': {
                'list': user_list,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@admin_bp.route('/users/<int:user_id>/status', methods=['POST'])
@admin_required
def update_user_status(user_id):
    """
    更新用户状态接口
    参数:
        - user_id: 用户ID（路径参数）
        - status: 用户状态（JSON body），1=正常, 0=封禁/停用
    返回: 操作结果
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必填字段
        if not data or 'status' not in data:
            return jsonify({
                'code': 400,
                'msg': '缺少必填字段：status'
            }), 400
        
        status = data.get('status')
        
        # 验证状态值
        if status not in [0, 1]:
            return jsonify({
                'code': 400,
                'msg': 'status 参数无效，仅支持 0（封禁）或 1（正常）'
            }), 400
        
        # 查询用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'code': 404,
                'msg': '用户不存在'
            }), 404
        
        # 不能封禁管理员
        if user.is_admin() and status == 0:
            return jsonify({
                'code': 403,
                'msg': '不能封禁管理员账号'
            }), 403
        
        # 更新状态
        user.status = status
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '操作成功',
            'data': {
                'user_id': user.id,
                'username': user.username,
                'status': user.status
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500
