"""
数据库模型定义
包含 User, Category, Video, Comment, Like, Collection 等核心模型
严格对应 univideo_db.sql 表结构
"""
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 初始化 SQLAlchemy 实例
db = SQLAlchemy()


class User(db.Model):
    """
    用户模型：存储用户基本信息和认证数据
    对应 SQL: users 表
    """
    __tablename__ = 'users'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户ID')
    # 基本信息
    username = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='学号/用户名')
    password = db.Column(db.String(255), nullable=False, comment='加密后的密码')
    nickname = db.Column(db.String(50), nullable=False, comment='用户昵称')
    role = db.Column(db.String(20), nullable=False, default='user', comment='角色: user/admin')
    avatar = db.Column(db.String(255), default='', comment='头像路径')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='注册时间')
    
    # 关系定义：一个用户可以上传多个视频
    videos = db.relationship('Video', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    # 关系定义：一个用户可以发表多条评论
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    # 关系定义：一个用户可以点赞多个视频
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    # 关系定义：一个用户可以收藏多个视频
    collections = db.relationship('Collection', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    # 便捷关系：通过 secondary 关联表直接访问收藏的视频
    favorites = db.relationship('Video', secondary='collections', backref=db.backref('collected_by', lazy='dynamic'), lazy='dynamic')
    
    def set_password(self, password):
        """
        设置用户密码：将明文密码转换为哈希值存储
        参数:
            password: 明文密码字符串
        """
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """
        验证用户密码：检查输入的密码是否与存储的哈希值匹配
        参数:
            password: 待验证的明文密码
        返回:
            bool: 密码正确返回 True，否则返回 False
        """
        return check_password_hash(self.password, password)
    
    def is_admin(self):
        """
        检查用户是否为管理员
        返回:
            bool: 是管理员返回 True，否则返回 False
        """
        return self.role == 'admin'
    
    def to_dict(self):
        """
        将用户对象转换为字典格式，用于API响应
        """
        return {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'role': self.role,
            'avatar': self.avatar,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    """
    视频分类模型：用于视频内容分类管理
    对应 SQL: categories 表
    """
    __tablename__ = 'categories'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='分类ID')
    # 分类名称
    name = db.Column(db.String(50), unique=True, nullable=False, comment='分类名称')
    
    # 关系定义：一个分类下可以有多个视频
    videos = db.relationship('Video', backref='category', lazy='dynamic')
    
    def to_dict(self):
        """
        将分类对象转换为字典格式
        """
        return {
            'id': self.id,
            'name': self.name
        }
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Video(db.Model):
    """
    视频模型：存储视频基本信息和元数据
    对应 SQL: videos 表
    重要：status 字段用于实现"先审后发"功能
    """
    __tablename__ = 'videos'
    
    # 视频状态常量定义
    STATUS_PENDING = 0   # 待审核
    STATUS_PUBLISHED = 1 # 已发布
    STATUS_REJECTED = 2  # 已驳回
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='视频ID')
    # 视频信息
    title = db.Column(db.String(100), nullable=False, comment='视频标题')
    description = db.Column(db.Text, comment='视频简介')
    cover_path = db.Column(db.String(255), nullable=False, comment='封面图片路径')
    video_path = db.Column(db.String(255), nullable=False, comment='视频文件路径')
    # 审核状态：0=待审核, 1=已发布, 2=驳回（核心字段，实现先审后发）
    status = db.Column(db.SmallInteger, default=0, index=True, comment='状态: 0=待审核, 1=已发布, 2=驳回')
    view_count = db.Column(db.Integer, default=0, comment='播放量')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True, comment='上传时间')
    
    # 外键：关联用户表
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='上传者ID')
    # 外键：关联分类表
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, comment='分类ID')
    
    # 关系定义：一个视频可以有多条评论
    comments = db.relationship('Comment', backref='video', lazy='dynamic', cascade='all, delete-orphan')
    # 关系定义：一个视频可以被多个用户点赞
    likes = db.relationship('Like', backref='video', lazy='dynamic', cascade='all, delete-orphan')
    # 关系定义：一个视频可以被多个用户收藏
    collections = db.relationship('Collection', backref='video', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_collections_count(self):
        """
        获取视频收藏数（通过关联表计算）
        返回:
            int: 收藏数量
        """
        return self.collections.count()
    
    def get_likes_count(self):
        """
        获取视频点赞数（通过关联表计算）
        返回:
            int: 点赞数量
        """
        return self.likes.count()
    
    def to_dict(self, include_author=True):
        """
        将视频对象转换为字典格式
        参数:
            include_author: 是否包含作者信息
        """
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'cover_path': self.cover_path,
            'video_path': self.video_path,
            'status': self.status,
            'view_count': self.view_count,
            'likes_count': self.get_likes_count(),
            'collections_count': self.get_collections_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'category_id': self.category_id,
        }
        if include_author and self.author:
            data['author'] = {
                'id': self.author.id,
                'username': self.author.username,
                'nickname': self.author.nickname,
                'avatar': self.author.avatar
            }
        if self.category:
            data['category'] = self.category.to_dict()
        return data
    
    def __repr__(self):
        return f'<Video {self.title}>'


class Comment(db.Model):
    """
    评论模型：支持多级评论（自关联结构）
    对应 SQL: comments 表
    设计说明：
    - parent_id: 直接回复的对象
    - root_id: 用于快速聚合整个对话串（所有属于同一楼层的回复均关联至同一个根评论ID）
    """
    __tablename__ = 'comments'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='评论ID')
    # 评论内容
    content = db.Column(db.Text, nullable=False, comment='评论内容')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='评论时间')
    
    # 外键：关联用户表
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='评论者ID')
    # 外键：关联视频表
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False, comment='所属视频ID')
    
    # 自关联字段：支持多级评论
    # parent_id: 直接父评论ID（直接回复的对象）
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'), comment='父评论ID')
    # root_id: 根评论ID（用于快速聚合整个对话串）
    root_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'), comment='根评论ID')
    
    # 联合索引：优化查询某视频下某楼层的所有回复
    __table_args__ = (
        db.Index('idx_video_root', 'video_id', 'root_id'),
    )
    
    # 关系定义：父评论关系（一对多）
    # parent: 访问当前评论的父评论
    # children: 访问当前评论的所有直接子评论
    parent = db.relationship('Comment', remote_side=[id], backref='children', foreign_keys=[parent_id])
    
    # 关系定义：根评论关系
    # root: 访问当前评论的根评论
    # all_replies: 访问根评论下的所有回复
    root = db.relationship('Comment', remote_side=[id], backref='all_replies', foreign_keys=[root_id])
    
    def to_dict(self, include_author=True, include_children=False):
        """
        将评论对象转换为字典格式
        参数:
            include_author: 是否包含作者信息
            include_children: 是否包含子评论
        """
        data = {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id,
            'video_id': self.video_id,
            'parent_id': self.parent_id,
            'root_id': self.root_id,
        }
        if include_author and self.author:
            data['author'] = {
                'id': self.author.id,
                'username': self.author.username,
                'nickname': self.author.nickname,
                'avatar': self.author.avatar
            }
        if include_children:
            data['children'] = [child.to_dict(include_author=True) for child in self.children]
        return data
    
    def __repr__(self):
        return f'<Comment {self.id}>'


class Like(db.Model):
    """
    点赞模型：记录用户对视频的点赞关系
    对应 SQL: likes 表
    """
    __tablename__ = 'likes'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='点赞ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='点赞时间')
    
    # 外键：关联用户表
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    # 外键：关联视频表
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False, comment='视频ID')
    
    # 联合唯一约束：确保同一用户不能重复点赞同一视频
    __table_args__ = (
        db.UniqueConstraint('user_id', 'video_id', name='unique_like'),
    )
    
    def to_dict(self):
        """
        将点赞记录转换为字典格式
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'video_id': self.video_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Like user_id={self.user_id} video_id={self.video_id}>'


class Collection(db.Model):
    """
    收藏模型：记录用户对视频的收藏关系
    对应 SQL: collections 表
    """
    __tablename__ = 'collections'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='收藏ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='收藏时间')
    
    # 外键：关联用户表
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    # 外键：关联视频表
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False, comment='视频ID')
    
    # 联合唯一约束：确保同一用户不能重复收藏同一视频
    __table_args__ = (
        db.UniqueConstraint('user_id', 'video_id', name='unique_collection'),
    )
    
    def to_dict(self):
        """
        将收藏记录转换为字典格式
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'video_id': self.video_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Collection user_id={self.user_id} video_id={self.video_id}>'


class Danmaku(db.Model):
    """
    弹幕模型：存储视频弹幕数据
    对应 ArtPlayer 弹幕插件的数据格式要求
    """
    __tablename__ = 'danmaku'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='弹幕ID')
    # 弹幕内容
    text = db.Column(db.String(100), nullable=False, comment='弹幕文本内容')
    # 弹幕出现时间（视频播放时间，单位：秒）
    time = db.Column(db.Float, nullable=False, comment='弹幕出现时间（秒）')
    # 弹幕颜色（十六进制颜色值）
    color = db.Column(db.String(20), default='#FFFFFF', comment='弹幕颜色')
    # 弹幕模式（0=滚动，1=顶部，2=底部）
    mode = db.Column(db.SmallInteger, default=0, comment='弹幕模式: 0=滚动, 1=顶部, 2=底部')
    # 是否显示边框
    border = db.Column(db.Boolean, default=False, comment='是否显示边框')
    # 发送时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='发送时间')
    
    # 外键：关联用户表
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='发送者ID')
    # 外键：关联视频表
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False, comment='所属视频ID')
    
    # 索引：优化按视频查询弹幕
    __table_args__ = (
        db.Index('idx_video_time', 'video_id', 'time'),
    )
    
    # 关系定义
    author = db.relationship('User', backref='danmakus')
    video = db.relationship('Video', backref='danmakus')
    
    def to_dict(self, include_author=False):
        """
        将弹幕对象转换为字典格式
        兼容 ArtPlayer 弹幕插件的数据格式
        """
        data = {
            'id': self.id,
            'text': self.text,
            'time': self.time,
            'color': self.color,
            'mode': self.mode,
            'border': self.border,
        }
        if include_author and self.author:
            data['author'] = {
                'id': self.author.id,
                'nickname': self.author.nickname,
            }
        return data
    
    def __repr__(self):
        return f'<Danmaku id={self.id} video_id={self.video_id}>'
