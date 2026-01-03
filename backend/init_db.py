"""
================================================================================
示例数据初始化脚本 (init_db.py)
================================================================================

【用途说明】
本脚本用于向数据库插入测试/示例数据，方便开发和测试使用。
包含：默认分类、测试用户、管理员账号。

【前置条件】
在运行本脚本之前，必须先执行 univideo_db.sql 创建数据库和表结构：
    mysql -u root -p < univideo_db.sql

【使用方法】
    cd backend
    python init_db.py

【注意事项】
- 本脚本不负责创建数据库和表结构（由 univideo_db.sql 负责）
- 如果数据库中已有数据，会跳过创建
- 创建的测试账号仅用于开发测试，生产环境请删除
================================================================================
"""
from app import app, db
from models import User, Category


def create_sample_data():
    """
    创建示例数据
    包含：4个默认分类 + 1个测试用户 + 1个管理员
    """
    with app.app_context():
        # 检查是否已有用户数据，避免重复创建
        if User.query.first() is not None:
            print("⚠ 数据库中已有数据，跳过示例数据创建")
            return False
        
        # 检查是否已有分类数据
        if Category.query.first() is None:
            # 创建默认分类（与 univideo_db.sql 保持一致）
            categories = [
                Category(name='校园生活'),
                Category(name='课程学习'),
                Category(name='社团活动'),
                Category(name='娱乐搞笑'),
            ]
            for category in categories:
                db.session.add(category)
            print("✓ 默认分类创建成功（校园生活、课程学习、社团活动、娱乐搞笑）")
        else:
            print("⚠ 分类已存在，跳过分类创建")
        
        # 创建测试用户（普通用户）
        test_user = User(
            username='testuser',
            nickname='测试用户',
            role='user',
            avatar=''
        )
        test_user.set_password('password123')
        db.session.add(test_user)
        
        # 创建管理员用户
        admin_user = User(
            username='admin',
            nickname='管理员',
            role='admin',
            avatar=''
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        # 提交到数据库
        db.session.commit()
        
        print("✓ 测试账号创建成功：")
        print("  - 普通用户: testuser / password123")
        print("  - 管理员:   admin / admin123")
        return True


if __name__ == '__main__':
    print("=" * 50)
    print("UniVideo 示例数据初始化")
    print("=" * 50)
    print()
    
    try:
        create_sample_data()
        print()
        print("✓ 初始化完成！现在可以运行 'python app.py' 启动服务器")
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        print("\n请确保：")
        print("1. 已执行 univideo_db.sql 创建数据库和表")
        print("2. MySQL 服务正在运行")
        print("3. 数据库连接配置正确")
