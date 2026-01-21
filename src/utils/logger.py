#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具
"""

import logging
import os
from datetime import datetime

from src.config.settings import LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOGS_DIR

def setup_logging():
    """设置日志配置"""
    # 确保日志目录存在
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=LOG_FORMAT,
        force=True,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8')
        ]
    )
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger().addHandler(console_handler)

def get_logger(name):
    """获取指定名称的日志器"""
    return logging.getLogger(name)

# 初始化日志
setup_logging()