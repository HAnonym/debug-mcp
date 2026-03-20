"""
日志系统 - 统一的日志配置
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str = "debug-mcp",
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    配置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，None 则不输出到文件
        format_string: 自定义格式字符串

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 默认格式
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "debug-mcp") -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)


# 默认日志配置
_default_logger: Optional[logging.Logger] = None


def init_default_logger(level: str = "INFO") -> logging.Logger:
    """初始化默认日志记录器"""
    global _default_logger
    if _default_logger is None:
        # 默认日志路径
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        log_file = os.path.join(log_dir, f"debug-mcp-{datetime.now().strftime('%Y%m%d')}.log")

        _default_logger = setup_logger(
            name="debug-mcp",
            level=level,
            log_file=log_file
        )

    return _default_logger


def get_default_logger() -> logging.Logger:
    """获取默认日志记录器"""
    global _default_logger
    if _default_logger is None:
        _default_logger = init_default_logger()
    return _default_logger
