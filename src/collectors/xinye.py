#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xinye 爬虫
"""

import re
import time
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from src.core.base_collector import BaseCollector
from src.core.exceptions import (
    ArticleLinkNotFoundError,
    NetworkError,
    RequestTimeoutError,
    ConnectionError as V2RayConnectionError,
)


class XinyeCollector(BaseCollector):
    """Xinye 专用爬虫"""

    def __init__(self, site_config):
        super().__init__(site_config)

    def get_latest_article_url(self, target_date=None):
        """
        重写获取文章URL的方法，直接构造GitHub订阅链接

        Xinye的订阅链接格式：https://raw.githubusercontent.com/xinyex/jds/main/wl{MMDD}u.txt
        其中MMDD是月份和日期（如0122表示1月22日）
        """
        try:
            # 默认使用今天作为目标日期
            if target_date is None:
                target_date = datetime.now()

            # 构造订阅链接
            month_day = f"{target_date.month:02d}{target_date.day:02d}"
            subscription_url = f"https://raw.githubusercontent.com/xinyex/jds/main/wl{month_day}u.txt"

            self.logger.info(f"构造Xinye订阅链接: {subscription_url}")

            # 返回特殊标记，表示直接从订阅链接获取节点
            return f"{subscription_url}#direct_subscription"

        except Exception as e:
            self.logger.error(f"构造Xinye订阅链接失败: {str(e)}")
            return None

    def find_subscription_links(self, content):
        """查找订阅链接 - 专门处理 xinye.eu.org 的格式"""
        links = []

        # 查找 GitHub raw 链接（主要来源）
        github_pattern = r'https://raw\.githubusercontent\.com/[^\s<>"]+\.txt'
        github_matches = re.findall(github_pattern, content)
        links.extend(github_matches)

        # 调用父类方法获取其他可能的链接
        parent_links = super().find_subscription_links(content)
        links.extend(parent_links)

        # 去重
        return list(set(links))

    def get_nodes_from_subscription(self, subscription_url):
        """使用统一订阅解析器处理订阅链接"""
        from src.core.subscription_parser import get_subscription_parser

        parser = get_subscription_parser()
        return parser.parse_subscription_url(subscription_url, self.session)