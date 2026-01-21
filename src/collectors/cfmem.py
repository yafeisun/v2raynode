#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CFMem 爬虫
"""

import re
import base64
from bs4 import BeautifulSoup
from src.core.base_collector import BaseCollector
from src.config.settings import MIN_NODE_LENGTH


class CfmemCollector(BaseCollector):
    """CFMem 专用爬虫"""

    def _get_latest_article_url(self):
        """获取最新文章URL - 实现抽象方法"""
        return self.get_latest_article_url()

    def get_latest_article_url(self, target_date=None):
        """重写获取最新文章URL的方法"""
        # 如果指定了日期，使用基类的日期匹配逻辑
        if target_date:
            return super().get_latest_article_url(target_date)

        try:
            response = self.session.get(
                self.base_url, timeout=self.timeout, verify=False
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # CFMem可能有特定的文章结构
            selectors = [
                ".post-list .title a",  # 文章列表标题
                ".article-list h2 a",  # 文章列表
                ".content-list h3 a",  # 内容列表
                ".node-list h2 a",  # 节点列表
                ".latest-post a",  # 最新文章
            ]

            # 先尝试特定选择器
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    href = links[0].get("href")
                    if href:
                        article_url = self._process_url(href)
                        self.logger.info(f"通过特定选择器找到文章: {article_url}")
                        return article_url

            # 调用父类方法
            return super().get_latest_article_url()

        except Exception as e:
            self.logger.error(f"获取文章链接失败: {str(e)}")
            return None

    def find_subscription_links(self, content):
        """重写订阅链接查找方法，专门查找V2Ray订阅链接"""
        links = []

        # CFMem专门查找V2Ray订阅链接
        v2ray_patterns = [
            # 标准V2Ray订阅链接（http开头，.txt结尾）
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            # 包含v2ray关键词的链接
            r'https?://[^\s\'"]*v2ray[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*vmess[^\s\'"]*\.txt[^\s\'"]*',
            # 订阅相关的.txt链接
            r'https?://[^\s\'"]*/sub[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*/subscribe[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*/link[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*/api[^\s\'"]*\.txt[^\s\'"]*',
        ]

        for pattern in v2ray_patterns:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                links.extend(matches)
            except Exception as e:
                self.logger.warning(f"V2Ray链接匹配失败: {pattern} - {str(e)}")

        # 在关键词附近查找
        v2ray_keywords = ["v2ray订阅", "vmess订阅", "节点订阅", "订阅链接", "v2ray sub"]
        for keyword in v2ray_keywords:
            try:
                pattern = rf"{keyword}[^:]*[:：]\s*(https?://[^\s\n\r]+\.txt)"
                matches = re.findall(pattern, content, re.IGNORECASE)
                links.extend(matches)
            except:
                pass

        # 查找可能在特定区域中的链接
        v2ray_area_patterns = [
            r'<div[^>]*class="[^"]*(?:v2ray|vmess|subscription)[^"]*"[^>]*>(.*?)</div>',
            r'<pre[^>]*class="[^"]*(?:v2ray|vmess|sub)[^"]*"[^>]*>(.*?)</pre>',
            r'<textarea[^>]*class="[^"]*(?:v2ray|vmess|sub)[^"]*"[^>]*>(.*?)</textarea>',
        ]

        for pattern in v2ray_area_patterns:
            try:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    # 在区域内查找.txt链接
                    txt_pattern = r'(https?://[^\s\'"]*\.txt)'
                    txt_matches = re.findall(txt_pattern, match, re.IGNORECASE)
                    links.extend(txt_matches)
            except Exception as e:
                self.logger.warning(f"V2Ray区域匹配失败: {pattern} - {str(e)}")

        # 清理和去重 - 使用改进的逻辑
        cleaned_links = []
        seen = set()

        for link in links:
            # 先从原始链接中提取所有独立的.txt URL（避免先清理导致URL合并）
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
                    self.logger.info(f"找到V2Ray订阅链接: {clean_link}")

        self.logger.info(f"CFMem找到 {len(cleaned_links)} 个V2Ray订阅链接")

        return cleaned_links

    def get_nodes_from_subscription(self, subscription_url):
        """使用统一订阅解析器处理订阅链接"""
        from src.core.subscription_parser import get_subscription_parser

        parser = get_subscription_parser()
        return parser.parse_subscription_url(subscription_url, self.session)

    def extract_direct_nodes(self, content):
        """重写直接节点提取方法，只提取V2Ray节点"""
        nodes = []

        # 只使用V2Ray节点模式
        # 使用所有节点模式
        from src.config.websites import NODE_PATTERNS

        for pattern in NODE_PATTERNS:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    node = match.strip()
                    if node and len(node) >= MIN_NODE_LENGTH:
                        nodes.append(node)
            except Exception as e:
                self.logger.warning(f"节点匹配失败: {pattern} - {str(e)}")

        return list(set(nodes))  # 去重
