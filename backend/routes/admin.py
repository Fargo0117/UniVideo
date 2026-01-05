"""
管理员路由模块
提供视频审核、管理等功能API接口
"""
from flask import Blueprint, request, jsonify, current_app
from models import db, Video, User, Notification
from datetime import datetime, timedelta
import os
import json

# 创建管理员蓝图
admin_bp = Blueprint('admin', __name__)


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
        - user_id (可选): 接收用户ID，如果为空则视为群发/广播（暂只实现指定ID发送）
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
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        user_id = data.get('user_id')
        msg_type = data.get('msg_type', Notification.MSG_TYPE_SYSTEM)
        related_link = data.get('related_link')
        
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
        
        # 验证用户ID（如果提供）
        if user_id:
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'code': 404,
                    'msg': '用户不存在'
                }), 404
        
        # 创建通知
        notification = Notification(
            title=title,
            content=content,
            msg_type=msg_type,
            related_link=related_link,
            user_id=user_id  # 如果为None，表示系统通知（群发）
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '通知发送成功',
            'data': {
                'notification_id': notification.id,
                'title': notification.title,
                'msg_type': notification.msg_type,
                'user_id': notification.user_id
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
        - user_id (可选): 用户ID，不传则返回系统通知
        - is_read (可选): 是否已读筛选 (true/false)
        - limit (可选): 返回数量限制，默认20
        - offset (可选): 偏移量，默认0
    返回: 通知列表
    """
    try:
        # 获取查询参数
        user_id = request.args.get('user_id', type=int)
        is_read = request.args.get('is_read')
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 构建查询
        query = Notification.query
        
        # 用户ID筛选
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        else:
            # 如果没有指定用户ID，返回系统通知（user_id为NULL）
            query = query.filter(Notification.user_id.is_(None))
        
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
        - user_id (可选): 用户ID，不传则标记系统通知
    返回: 操作结果
    """
    try:
        # 获取查询参数
        user_id = request.args.get('user_id', type=int)
        
        # 构建查询
        query = Notification.query.filter_by(is_read=False)
        
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        else:
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
        - user_id (可选): 用户ID，不传则返回系统通知未读数
    返回: 未读通知数量
    """
    try:
        # 获取查询参数
        user_id = request.args.get('user_id', type=int)
        
        # 构建查询
        query = Notification.query.filter_by(is_read=False)
        
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        else:
            query = query.filter(Notification.user_id.is_(None))
        
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
