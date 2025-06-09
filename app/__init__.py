import os
from flask import Flask
from .models import db
from .controllers import testcase_bp, knowledge_bp
from flask_migrate import Migrate
from .utils.logger import init_logger

def create_app(config_class=None):
    """创建并配置Flask应用程序"""
    # 初始化日志系统
    init_logger()
    
    app = Flask(__name__)
    
    # 加载配置
    if config_class is None:
        from .config import get_config
        app.config.from_object(get_config())
    else:
        app.config.from_object(config_class)
        
    # 初始化扩展
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # 创建上传、导出和文档存储目录
    with app.app_context():
        os.makedirs(os.path.join(app.root_path, 'uploads'), exist_ok=True)
        os.makedirs(os.path.join(app.root_path, 'exports'), exist_ok=True)
        os.makedirs(os.path.join(app.root_path, 'documents'), exist_ok=True)
    
    # 注册蓝图
    app.register_blueprint(testcase_bp)
    app.register_blueprint(knowledge_bp)
    
    # 注册首页路由
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    return app 