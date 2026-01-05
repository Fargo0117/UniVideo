/* 创建数据库 */
CREATE DATABASE IF NOT EXISTS univideo_db DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE univideo_db;

/* 1. 用户表 */
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
  `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '学号/用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '加密后的密码',
  `nickname` VARCHAR(50) NOT NULL COMMENT '昵称',
  `role` VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色: user/admin',
  `avatar` VARCHAR(255) DEFAULT '' COMMENT '头像路径',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间'
) COMMENT='用户信息表';

/* 2. 视频分类表 */
CREATE TABLE IF NOT EXISTS `categories` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(50) NOT NULL UNIQUE COMMENT '分类名称'
) COMMENT='视频分类表';
INSERT IGNORE INTO `categories` (`name`) VALUES ('校园生活'), ('课程学习'), ('社团活动'), ('娱乐搞笑');

/* 3. 视频信息表 */
CREATE TABLE IF NOT EXISTS `videos` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL COMMENT '上传者ID',
  `category_id` INT NOT NULL COMMENT '分类ID',
  `title` VARCHAR(100) NOT NULL COMMENT '视频标题',
  `description` TEXT COMMENT '视频简介',
  `cover_path` VARCHAR(255) NOT NULL COMMENT '封面图片路径',
  `video_path` VARCHAR(255) NOT NULL COMMENT '视频文件路径',
  `status` TINYINT DEFAULT 0 COMMENT '状态: 0=待审核, 1=已发布, 2=驳回',
  `view_count` INT DEFAULT 0 COMMENT '播放量',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`),
  INDEX `idx_status` (`status`), /* 优化审核查询速度 */
  INDEX `idx_created_at` (`created_at`) /* 优化按时间排序 */
) COMMENT='视频信息表';

/* 4. 评论表 (已更新：增加 root_id 和索引) */
CREATE TABLE IF NOT EXISTS `comments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL COMMENT '评论者ID',
  `video_id` INT NOT NULL COMMENT '所属视频ID',
  `parent_id` INT DEFAULT NULL COMMENT '父评论ID: 直接回复的对象',
  `root_id` INT DEFAULT NULL COMMENT '根评论ID: 用于快速聚合整个对话串',
  `content` TEXT NOT NULL COMMENT '评论内容',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`video_id`) REFERENCES `videos`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`parent_id`) REFERENCES `comments`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`root_id`) REFERENCES `comments`(`id`) ON DELETE CASCADE,
  INDEX `idx_video_root` (`video_id`, `root_id`) /* 核心索引：查询某视频下某楼层的所有回复 */
) COMMENT='评论互动表';

/* 5. 点赞表 */
CREATE TABLE IF NOT EXISTS `likes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `video_id` INT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `unique_like` (`user_id`, `video_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`video_id`) REFERENCES `videos`(`id`) ON DELETE CASCADE
) COMMENT='点赞记录表';

/* 6. 收藏表 */
CREATE TABLE IF NOT EXISTS `collections` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL COMMENT '用户ID',
  `video_id` INT NOT NULL COMMENT '视频ID',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `unique_collection` (`user_id`, `video_id`), /* 防止重复收藏 */
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`video_id`) REFERENCES `videos`(`id`) ON DELETE CASCADE
) COMMENT='用户收藏表';

/* 7. 弹幕表 */
CREATE TABLE IF NOT EXISTS `danmaku` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '弹幕ID',
  `user_id` INT NOT NULL COMMENT '发送者ID',
  `video_id` INT NOT NULL COMMENT '所属视频ID',
  `text` VARCHAR(100) NOT NULL COMMENT '弹幕文本内容',
  `time` FLOAT NOT NULL COMMENT '弹幕出现时间（秒）',
  `color` VARCHAR(20) DEFAULT '#FFFFFF' COMMENT '弹幕颜色',
  `mode` TINYINT DEFAULT 0 COMMENT '弹幕模式: 0=滚动, 1=顶部, 2=底部',
  `border` BOOLEAN DEFAULT FALSE COMMENT '是否显示边框',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`video_id`) REFERENCES `videos`(`id`) ON DELETE CASCADE,
  INDEX `idx_video_time` (`video_id`, `time`) /* 优化按视频查询弹幕 */
) COMMENT='视频弹幕表';

/* 8. 关注关系表 */
CREATE TABLE IF NOT EXISTS `follows` (
  `follower_id` INT NOT NULL COMMENT '关注者ID',
  `followed_id` INT NOT NULL COMMENT '被关注者ID',
  `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '关注时间',
  PRIMARY KEY (`follower_id`, `followed_id`),
  FOREIGN KEY (`follower_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`followed_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  CONSTRAINT `check_no_self_follow` CHECK (`follower_id` != `followed_id`),
  INDEX `idx_follower` (`follower_id`), /* 优化查询某用户的关注列表 */
  INDEX `idx_followed` (`followed_id`)  /* 优化查询某用户的粉丝列表 */
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户关注关系表';