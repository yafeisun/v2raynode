#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FreeV2rayNode 爬虫
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


class FreeV2rayNodeCollector(BaseCollector):
    """FreeV2rayNode 专用爬虫"""

    def __init__(self, site_config):
        super().__init__(site_config)
        # 添加额外的请求头以绕过反爬虫
        self.session.headers.update(
            {
                "Referer": "https://www.freev2raynode.com/",
                "Origin": "https://www.freev2raynode.com",
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

    def get_latest_article_url(self, target_date=None):
        """获取文章URL，支持指定日期"""
        try:
            response = self._make_request(self.base_url)

            soup = BeautifulSoup(response.text, "html.parser")

            if target_date is None:
                target_date = datetime.now()

            # FreeV2rayNode使用格式：2026-1-17-free-v2ray.htm
            date_str = target_date.strftime("%Y-%m-%d")
            date_str_alt = target_date.strftime("%Y/%m/%d")
            date_str_free_format = target_date.strftime("%Y-%m-%d")
            date_str_month_day_cn = f"{target_date.month}月{target_date.day}日"
            date_str_month_day_cn_alt = (
                f"{target_date.month:02d}月{target_date.day:02d}日"
            )
            date_str_month_day = target_date.strftime("%m-%d")
            date_str_year_month = target_date.strftime("%Y-%m")
            date_str_year_month_cn = (
                f"{target_date.year}年{target_date.month:02d}月{target_date.day:02d}日"
            )

            # 优先通过日期匹配查找文章
            all_links = soup.find_all("a", href=True)
            for link in all_links:
                href = link.get("href")
                text = link.get_text(strip=True)

                # 检查链接文本或URL中是否包含今天的日期
                if href and (
                    date_str in href
                    or date_str_alt in href
                    or date_str_month_day_cn in text
                    or date_str_month_day_cn_alt in text
                    or date_str_year_month_cn in text
                    or date_str in text
                    or date_str_month_day in text
                ):
                    # 排除导航链接（只选择文章链接）
                    if href and not any(
                        x in href
                        for x in ["category", "tag", "page", "search", "about", "feed"]
                    ):
                        article_url = self._process_url(href)
                        self.logger.info(f"通过日期匹配找到文章: {article_url}")
                        return article_url

            # 如果日期匹配失败，尝试特定选择器
            selectors = self.site_config.get("selectors", [])
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    href = links[0].get("href")
                    if href:
                        article_url = self._process_url(href)
                        self.logger.info(f"通过选择器找到文章: {article_url}")
                        return article_url

            self.logger.warning(f"未找到文章链接")
            return None

        except Exception as e:
            self.logger.error(f"获取文章链接失败: {str(e)}")
            return None

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
            except Exception as e:
                self.logger.debug(f"关键词匹配失败: {str(e)}")

        # 清理和去重
        cleaned_links = []
        seen = set()

        for link in links:
            # 先从原始链接中提取所有独立的.txt URL（避免先清理导致URL合并）
            # 使用正则表达式直接提取所有URL，不先移除HTML标签
            url_matches = re.findall(r'https?://[^\s<>"\']+\.(?:txt|TXT)', link)

            for url_match in url_matches:
                # 然后对每个提取的URL进行清理
                clean_link = self._clean_link(url_match)
                if (
                    clean_link
                    and clean_link not in seen
                    and self._is_valid_url(clean_link)
                    and self._is_valid_subscription_link(clean_link)
                ):
                    cleaned_links.append(clean_link)
                    seen.add(clean_link)

        return cleaned_links
