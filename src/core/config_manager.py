#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置加载器
整合所有配置项的加载和管理
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class BaseConfig:
    """基础配置类，统一管理所有配置项"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BaseConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._load_base_config()
            self._initialized = True

    def _load_base_config(self):
        """加载基础配置"""
        # 项目路径
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent

        # Git配置
        self.GIT_EMAIL = os.getenv("GIT_EMAIL", "action@github.com")
        self.GIT_NAME = os.getenv("GIT_NAME", "GitHub Action")

        # 网络配置
        self.REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.REQUEST_DELAY = int(os.getenv("REQUEST_DELAY", "2"))
        self.REQUEST_RETRY = int(os.getenv("REQUEST_RETRY", "3"))
        self.USER_AGENT = os.getenv(
            "USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        # 测试配置
        self.CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "5"))
        self.MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))

        # 文件路径配置
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.RAW_DATA_DIR = self.DATA_DIR / "raw"
        self.PROCESSED_DATA_DIR = self.DATA_DIR / "processed"
        self.LOGS_DIR = self.DATA_DIR / "logs"
        self.RESULT_DIR = self.PROJECT_ROOT / "result"

        # 结果文件路径
        self.NODELIST_FILE = self.RESULT_DIR / "nodelist.txt"
        self.NODELIST_HK_FILE = self.RESULT_DIR / "nodelist_HK.txt"
        self.WEBPAGE_LINKS_FILE = self.RESULT_DIR / "webpage.txt"
        self.SUBSCRIPTION_FILE = self.RESULT_DIR / "subscription.txt"

        # 日志配置
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.LOG_FILE = (
            self.LOGS_DIR / f"collector_{datetime.now().strftime('%Y%m%d')}.log"
        )

        # 节点配置
        self.SUPPORTED_PROTOCOLS = [
            "vmess",
            "vless",
            "trojan",
            "hysteria",
            "hysteria2",
            "ss",
            "ssr",
        ]
        self.MIN_NODE_LENGTH = 20

        # 性能配置
        self.BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
        self.CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))

        # 调试配置
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"

        # API配置
        self.API_ENABLED = os.getenv("API_ENABLED", "False").lower() == "true"
        self.API_HOST = os.getenv("API_HOST", "127.0.0.1")
        self.API_PORT = int(os.getenv("API_PORT", "8080"))

        # 数据库配置
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///nodes.db")


class WebsiteConfig:
    """网站配置管理器"""

    def __init__(self):
        self._websites = {}
        self._load_websites()

    def _load_websites(self):
        """从配置文件加载网站配置"""
        try:
            from src.config.websites import WEBSITES

            self._websites = WEBSITES
        except ImportError:
            print("❌ 无法导入网站配置文件")
            self._websites = {}

    def get_websites(self) -> Dict[str, Any]:
        """获取所有网站配置"""
        return self._websites

    def get_website(self, site_key: str) -> Optional[Dict[str, Any]]:
        """获取指定网站配置"""
        return self._websites.get(site_key)

    def get_enabled_websites(self) -> Dict[str, Any]:
        """获取启用的网站配置"""
        return {
            key: config
            for key, config in self._websites.items()
            if config.get("enabled", True)
        }

    def get_website_keys(self) -> list:
        """获取所有网站键名"""
        return list(self._websites.keys())

    def get_enabled_website_keys(self) -> list:
        """获取启用的网站键名"""
        return [
            key for key, config in self._websites.items() if config.get("enabled", True)
        ]


class ConfigManager:
    """统一配置管理器"""

    def __init__(self):
        self.base = BaseConfig()
        self.websites = WebsiteConfig()

    def get_config(self, section: str = None) -> Any:
        """获取配置"""
        if section is None:
            return self
        elif section == "websites":
            return self.websites
        else:
            return getattr(self.base, str(section).upper() if section else "", None)

    def reload(self):
        """重新加载配置"""
        self.base._load_base_config()
        self.websites._load_websites()

    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.base.DATA_DIR,
            self.base.RAW_DATA_DIR,
            self.base.PROCESSED_DATA_DIR,
            self.base.LOGS_DIR,
            self.base.RESULT_DIR,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典格式"""
        return {
            "base": {
                "project_root": str(self.base.PROJECT_ROOT),
                "git_email": self.base.GIT_EMAIL,
                "git_name": self.base.GIT_NAME,
                "request_timeout": self.base.REQUEST_TIMEOUT,
                "request_delay": self.base.REQUEST_DELAY,
                "request_retry": self.base.REQUEST_RETRY,
                "user_agent": self.base.USER_AGENT,
                "connection_timeout": self.base.CONNECTION_TIMEOUT,
                "max_workers": self.base.MAX_WORKERS,
                "log_level": self.base.LOG_LEVEL,
                "debug": self.base.DEBUG,
                "api_enabled": self.base.API_ENABLED,
                "api_host": self.base.API_HOST,
                "api_port": self.base.API_PORT,
            },
            "websites": {
                "total_count": len(self.websites.get_websites()),
                "enabled_count": len(self.websites.get_enabled_websites()),
                "websites": list(self.websites.get_website_keys()),
            },
        }


# 全局配置实例
config = ConfigManager()


def get_config(section: Optional[str] = None) -> Any:
    """获取配置"""
    return config.get_config(section)


def ensure_directories():
    """确保目录存在的便捷函数"""
    config.ensure_directories()


if __name__ == "__main__":
    # 测试配置加载
    cfg = get_config()
    print("配置加载测试:")
    print(f"项目根目录: {cfg.PROJECT_ROOT}")
    print(f"网站数量: {len(config.websites.get_websites())}")
    print(f"启用网站数量: {len(config.websites.get_enabled_websites())}")

    # 确保目录存在
    ensure_directories()
    print("目录检查完成")
