"""
统一的日志配置模块，用于配置应用的所有日志
支持按日期轮转、彩色输出、自定义格式和目录结构
"""
import logging
import os
import sys
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import traceback

# 全局日志配置是否已初始化
_is_initialized = False

# 日志级别映射
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# ANSI颜色代码
COLORS = {
    'DEBUG': '\033[36m',     # 青色
    'INFO': '\033[32m',      # 绿色
    'WARNING': '\033[33m',   # 黄色
    'ERROR': '\033[31m',     # 红色
    'CRITICAL': '\033[35m',  # 紫色
    'RESET': '\033[0m'       # 重置
}

class ColoredFormatter(logging.Formatter):
    """
    自定义彩色日志格式化器
    """
    def format(self, record):
        # 保存原始的levelname
        levelname = record.levelname
        # 添加颜色
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
        result = super().format(record)
        # 恢复原始的levelname
        record.levelname = levelname
        return result

def ensure_log_dir(log_dir):
    """
    确保日志目录存在
    
    Args:
        log_dir: 日志目录路径
    """
    try:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def get_log_path(app_name=None, log_dir=None):
    """
    获取日志文件路径
    
    Args:
        app_name: 应用名称，用于日志文件命名
        log_dir: 日志目录
        
    Returns:
        日志文件路径
    """
    # 默认日志目录
    if not log_dir:
        # 尝试从环境变量获取
        log_dir = os.environ.get('LOG_DIR')
        if not log_dir:
            # 默认在项目根目录下的logs目录
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            log_dir = os.path.join(base_dir, 'logs')
    
    # 确保日志目录存在
    ensure_log_dir(log_dir)
    
    # 日志文件名
    if not app_name:
        app_name = os.environ.get('APP_NAME', 'app')
    
    # 返回日志文件路径
    return os.path.join(log_dir, f"{app_name}.log")

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
    
    # 获取配置
    # 1. 从Flask应用获取配置
    if app:
        log_level_name = app.config.get('LOG_LEVEL', 'INFO')
        log_file = app.config.get('LOG_FILE')
        log_dir = app.config.get('LOG_DIR')
        app_name = app.config.get('APP_NAME', app.name)
    # 2. 从环境变量获取配置
    else:
        log_level_name = os.environ.get('LOG_LEVEL', 'INFO')
        log_file = os.environ.get('LOG_FILE')
        log_dir = os.environ.get('LOG_DIR')
        app_name = os.environ.get('APP_NAME', 'app')
    
    # 获取日志级别
    log_level = LOG_LEVELS.get(log_level_name.upper(), logging.INFO)
    
    # 创建处理器列表
    handlers = []
    
    # 控制台处理器（彩色）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # 控制台使用简化的彩色格式
    console_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    console_formatter = ColoredFormatter(console_format, datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    # 文件处理器（详细信息）
    if not log_file:
        log_file = get_log_path(app_name, log_dir)
    
    if log_file:
        try:
            # 使用TimedRotatingFileHandler按天轮转日志
            file_handler = TimedRotatingFileHandler(
                log_file,
                when='midnight',          # 每天午夜轮转
                interval=1,               # 轮转间隔为1天
                backupCount=30,           # 保留30天的日志
                encoding='utf-8',         # 使用UTF-8编码
                delay=False,              # 立即打开文件
                atTime=None               # 在午夜轮转
            )
            file_handler.setLevel(log_level)
            
            # 文件使用详细格式，包含更多信息
            file_format = (
                '%(asctime)s [%(process)d:%(thread)d] [%(levelname)s] '
                '%(name)s [%(filename)s:%(lineno)d] [%(funcName)s]: %(message)s'
            )
            file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(file_formatter)
            handlers.append(file_handler)
        except Exception as e:
            traceback.print_exc()
    
    # 配置根日志器
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True  # 强制重新配置
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
    root_logger = logging.getLogger()
    if log_file:
        root_logger.info("日志系统初始化完成，日志级别: %s，日志文件: %s", log_level_name, log_file)
    else:
        root_logger.info("日志系统初始化完成，日志级别: %s，仅控制台输出", log_level_name)

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

# 默认初始化
if not _is_initialized:
    init_logger() 