import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'ai_testcase_generator')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Dify API配置
    DIFY_API_KEY = os.getenv('DIFY_API_KEY')
    DIFY_API_BASE_URL = os.getenv('DIFY_API_BASE_URL', 'https://api.dify.ai/v1')
    # 根据Dify API文档更新，知识库ID现在称为dataset_id
    DIFY_KNOWLEDGE_BASE_ID = os.getenv('DIFY_DATASET_ID') or os.getenv('DIFY_KNOWLEDGE_BASE_ID')
    
    # AI模型配置
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
    AI_BASE_URL = os.getenv('AI_BASE_URL', 'https://api.openai.com/v1')
    AI_API_KEY = os.getenv('AI_API_KEY')
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '4096'))

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 获取当前配置
def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default']) 