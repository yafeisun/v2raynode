#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主配置文件
"""

import os
from datetime import datetime

# 项目根目录（使用当前工作目录，适用于GitHub Actions）
PROJECT_ROOT = os.getcwd()

# Git配置
GIT_EMAIL = "action@github.com"
GIT_NAME = "GitHub Action"

# 测试配置
CONNECTION_TIMEOUT = 5  # 连接超时时间（秒）
MAX_WORKERS = 10  # 最大并发测试线程数

# 请求配置
REQUEST_TIMEOUT = 60  # 请求超时时间（秒）
REQUEST_DELAY = 2  # 请求间隔时间（秒）
REQUEST_RETRY = 3  # 请求重试次数

# 文件路径配置
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

# 结果文件路径
OUTPUT_DIR = PROJECT_ROOT
RESULT_DIR = os.path.join(PROJECT_ROOT, "result")
NODELIST_FILE = os.path.join(RESULT_DIR, "nodelist.txt")  # AI可用节点
NODELIST_HK_FILE = os.path.join(RESULT_DIR, "nodelist_HK.txt")  # 保留兼容性
WEBPAGE_LINKS_FILE = os.path.join(RESULT_DIR, "webpage.txt")
SUBSCRIPTION_FILE = os.path.join(RESULT_DIR, "subscription.txt")

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.path.join(LOGS_DIR, f"collector_{datetime.now().strftime('%Y%m%d')}.log")

# 网络配置
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 节点配置
SUPPORTED_PROTOCOLS = ["vmess", "vless", "trojan", "hysteria", "hysteria2", "ss", "ssr"]
MIN_NODE_LENGTH = 20  # 节点最小长度

# 数据库配置（如果需要）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///nodes.db")

# API配置（如果需要）
API_ENABLED = False
API_HOST = "127.0.0.1"
API_PORT = 8080

# 调试配置
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# 性能配置
BATCH_SIZE = 100  # 批处理大小
CACHE_TTL = 3600  # 缓存时间（秒）
