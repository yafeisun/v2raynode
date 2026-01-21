#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础配置
"""

import os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass


@dataclass
class BaseConfig:
    """基础配置"""

    # 项目路径
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent

    # Git配置
    GIT_EMAIL: str = "action@github.com"
    GIT_NAME: str = "GitHub Action"

    # 测试配置
    CONNECTION_TIMEOUT: int = 5  # 连接超时时间（秒）
    MAX_WORKERS: int = 10  # 最大并发测试线程数

    # 请求配置
    REQUEST_TIMEOUT: int = 60  # 请求超时时间（秒）
    REQUEST_DELAY: int = 2  # 请求间隔时间（秒）
    REQUEST_RETRY: int = 3  # 请求重试次数

    # 文件路径配置
    DATA_DIR: Path = None
    RAW_DATA_DIR: Path = None
    PROCESSED_DATA_DIR: Path = None
    LOGS_DIR: Path = None

    # 结果文件路径
    OUTPUT_DIR: Path = None
    RESULT_DIR: Path = None
    NODELIST_FILE: Path = None
    NODELIST_HK_FILE: Path = None
    WEBPAGE_LINKS_FILE: Path = None
    SUBSCRIPTION_FILE: Path = None

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Path = None

    # 网络配置
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # 节点配置
    SUPPORTED_PROTOCOLS: list = None
    MIN_NODE_LENGTH: int = 20  # 节点最小长度

    # 数据库配置（如果需要）
    DATABASE_URL: str = "sqlite:///nodes.db"

    # API配置（如果需要）
    API_ENABLED: bool = False
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8080

    # 调试配置
    DEBUG: bool = False

    # 性能配置
    BATCH_SIZE: int = 100  # 批处理大小
    CACHE_TTL: int = 3600  # 缓存时间（秒）

    def __post_init__(self):
        """初始化后处理"""
        # 设置路径
        if self.DATA_DIR is None:
            self.DATA_DIR = self.PROJECT_ROOT / "data"
        if self.RAW_DATA_DIR is None:
            self.RAW_DATA_DIR = self.DATA_DIR / "raw"
        if self.PROCESSED_DATA_DIR is None:
            self.PROCESSED_DATA_DIR = self.DATA_DIR / "processed"
        if self.LOGS_DIR is None:
            self.LOGS_DIR = self.DATA_DIR / "logs"

        if self.OUTPUT_DIR is None:
            self.OUTPUT_DIR = self.PROJECT_ROOT
        if self.RESULT_DIR is None:
            self.RESULT_DIR = self.PROJECT_ROOT / "result"
        if self.NODELIST_FILE is None:
            self.NODELIST_FILE = self.RESULT_DIR / "nodelist.txt"
        if self.NODELIST_HK_FILE is None:
            self.NODELIST_HK_FILE = self.RESULT_DIR / "nodelist_HK.txt"
        if self.WEBPAGE_LINKS_FILE is None:
            self.WEBPAGE_LINKS_FILE = self.RESULT_DIR / "webpage.txt"
        if self.SUBSCRIPTION_FILE is None:
            self.SUBSCRIPTION_FILE = self.RESULT_DIR / "subscription.txt"

        if self.LOG_FILE is None:
            self.LOG_FILE = self.LOGS_DIR / f"collector_{datetime.now().strftime('%Y%m%d')}.log"

        if self.SUPPORTED_PROTOCOLS is None:
            self.SUPPORTED_PROTOCOLS = [
                "vmess",
                "vless",
                "trojan",
                "hysteria",
                "hysteria2",
                "ss",
                "ssr",
            ]

        # 从环境变量读取
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///nodes.db")

        # 创建必要的目录
        self._create_directories()

    def _create_directories(self):
        """创建必要的目录"""
        for dir_path in [
            self.DATA_DIR,
            self.RAW_DATA_DIR,
            self.PROCESSED_DATA_DIR,
            self.LOGS_DIR,
            self.RESULT_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)


# 全局配置实例
_global_config = None


def get_config() -> BaseConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = BaseConfig()
    return _global_config