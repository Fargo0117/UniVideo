"""
管理员路由模块
提供视频审核等管理功能API接口
"""
from flask import Blueprint, request, jsonify
from models import db, Video

# 创建管理员蓝图
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/audit/list', methods=['GET'])
def get_audit_list():
    """
    获取待审核视频列表接口
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
