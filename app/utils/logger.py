"""
统一的日志配置模块，用于配置应用的所有日志
"""
import logging
import os
from logging.handlers import RotatingFileHandler

# 全局日志配置是否已初始化
_is_initialized = False

def init_logger(app=None):
    """
    初始化日志配置
    
    Args:
        app: Flask应用实例，如果提供则从app.config中读取配置
    """
    global _is_initialized
    
    # 避免重复初始化
    if _is_initialized:
        return
    
    # 获取日志级别
    log_level_name = os.environ.get('LOG_LEVEL', 'INFO')
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)
    
    # 创建根日志器的处理器
    handlers = [logging.StreamHandler()]
    
    # 如果指定了日志文件，添加文件处理器
    log_file = os.environ.get('LOG_FILE')
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        handlers.append(file_handler)
    
    # 配置根日志器
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # 配置第三方库的日志级别
    # 降低httpx的日志级别，避免过多的HTTP请求日志
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    # 降低其他常见库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # 降低一些AI相关库的日志级别
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)
    
    # 标记为已初始化
    _is_initialized = True
    
    # 记录日志初始化完成
    logging.info("日志系统初始化完成，日志级别: %s", log_level_name)

def get_logger(name):
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        指定名称的日志器
    """
    # 确保日志系统已初始化
    if not _is_initialized:
        init_logger()
    
    return logging.getLogger(name) 