from flask import Flask
from app.models import db
from app.config import get_config

def init_db():
    """初始化数据库，创建所有表"""
    app = Flask(__name__)
    app.config.from_object(get_config())
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("数据库表已创建")

if __name__ == "__main__":
    init_db() 