#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置模块
"""

# 导入基础配置
from .base_config import BaseConfig, get_config

# 导入 User-Agent 配置
from .user_agents import (
    REAL_USER_AGENTS,
    DEFAULT_USER_AGENT,
    get_random_user_agent,
    get_user_agent,
    get_headers,
)

# 导入网站配置（保持向后兼容）
from src.config.settings import *
from src.config.websites import *

__all__ = [
    # 基础配置
    "BaseConfig",
    "get_config",
    # User-Agent
    "REAL_USER_AGENTS",
    "DEFAULT_USER_AGENT",
    "get_random_user_agent",
    "get_user_agent",
    "get_headers",
    # 向后兼容的导出
    "PROJECT_ROOT",
    "GIT_EMAIL",
    "GIT_NAME",
    "CONNECTION_TIMEOUT",
    "MAX_WORKERS",
    "REQUEST_TIMEOUT",
    "REQUEST_DELAY",
    "REQUEST_RETRY",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "LOGS_DIR",
    "OUTPUT_DIR",
    "RESULT_DIR",
    "NODELIST_FILE",
    "NODELIST_HK_FILE",
    "WEBPAGE_LINKS_FILE",
    "SUBSCRIPTION_FILE",
    "LOG_LEVEL",
    "LOG_FORMAT",
    "LOG_FILE",
    "USER_AGENT",
    "SUPPORTED_PROTOCOLS",
    "MIN_NODE_LENGTH",
    "DATABASE_URL",
    "API_ENABLED",
    "API_HOST",
    "API_PORT",
    "DEBUG",
    "BATCH_SIZE",
    "CACHE_TTL",
    "WEBSITES",
    "SUBSCRIPTION_PATTERNS",
    "NODE_PATTERNS",
    "BROWSER_ONLY_SITES",
    "EXCLUDED_SUBSCRIPTION_PATTERNS",
    "SUBSCRIPTION_KEYWORDS",
    "CODE_BLOCK_SELECTORS",
    "BASE64_PATTERNS",
    "TIME_SELECTORS",
    "UNIVERSAL_SELECTORS",
]