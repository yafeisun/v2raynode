#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OneClash 爬虫
"""

import re
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from src.core.base_collector import BaseCollector
from src.config.websites import (
    SUBSCRIPTION_PATTERNS,
    SUBSCRIPTION_KEYWORDS,
    UNIVERSAL_SELECTORS,
)


class OneClashCollector(BaseCollector):
    """OneClash 专用爬虫"""

    def __init__(self, site_config):
        super().__init__(site_config)
        # 添加额外的请求头以绕过反爬虫
        self.session.headers.update(
            {
                "Referer": "https://oneclash.cc/",
                "Origin": "https://oneclash.cc",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
            }
        )

    def _make_request(self, url, method="GET", **kwargs):
        """重写请求方法，添加随机延迟"""
        # 添加随机延迟以模拟人类行为
        time.sleep(random.uniform(1, 2))

        # 调用父类方法
        return super()._make_request(url, method, **kwargs)

    def _get_latest_article_url(self):
        """获取最新文章URL - 实现抽象方法"""
        return self.get_latest_article_url()

    def find_subscription_links(self, content):
        """查找订阅链接"""
        links = []

        # 使用特定网站的模式
        patterns = self.site_config.get("patterns", [])
        for pattern in patterns:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                links.extend(matches)
            except Exception as e:
                self.logger.warning(f"模式匹配失败: {pattern} - {str(e)}")

        # 使用通用订阅模式
        for pattern in SUBSCRIPTION_PATTERNS:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        links.extend(match)
                    else:
                        links.append(match)
            except Exception as e:
                self.logger.warning(f"通用模式匹配失败: {pattern} - {str(e)}")

        # 在关键词附近查找
        for keyword in SUBSCRIPTION_KEYWORDS:
            try:
                pattern = rf"{keyword}[^:]*[:：]\s*(https?://[^\s\n\r]+)"
                matches = re.findall(pattern, content, re.IGNORECASE)
                links.extend(matches)
            except:
                pass

        # 清理和去重
        cleaned_links = []
        seen = set()

        for link in links:
            clean_link = self._clean_link(link)
            if (
                clean_link
                and clean_link not in seen
                and self._is_valid_url(clean_link)
                and self._is_valid_subscription_link(clean_link)
            ):
                cleaned_links.append(clean_link)
                seen.add(clean_link)

        return cleaned_links
