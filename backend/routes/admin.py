"""
管理员路由模块
提供视频审核、管理等功能API接口
"""
from flask import Blueprint, request, jsonify, current_app
from models import db, Video
import os

# 创建管理员蓝图
admin_bp = Blueprint('admin', __name__)


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
        else:  # action == 'reject'
            video.status = Video.STATUS_REJECTED   # 驳回
            result_msg = '视频已驳回'
        
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
