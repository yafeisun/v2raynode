#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
米贝节点爬虫
"""

import re
import base64
from bs4 import BeautifulSoup
from src.core.base_collector import BaseCollector


class Mibei77Collector(BaseCollector):
    """米贝节点专用爬虫"""

    def __init__(self, site_config):
        super().__init__(site_config)
        # 添加额外的请求头以适配米贝77
        self.session.headers.update(
            {
                "Referer": "https://www.mibei77.com/",
                "Origin": "https://www.mibei77.com",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )

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

            # 米贝节点通常有特定的文章结构
            selectors = [
                ".post-list .post-title a",  # 文章列表
                ".article-list .title a",
                ".content-list h2 a",
                ".blog-list .entry-title a",
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

    def get_nodes_from_subscription(self, subscription_url):
        """使用统一订阅解析器处理订阅链接"""
        from src.core.subscription_parser import get_subscription_parser

        parser = get_subscription_parser()
        return parser.parse_subscription_url(subscription_url, self.session)

    def find_subscription_links(self, content):
        """重写订阅链接查找方法，专门查找米贝77的订阅链接"""
        links = []

        # 米贝77特定的订阅链接模式
        mibei77_patterns = [
            # 标准的V2Ray订阅链接
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            # 米贝77域名下的链接
            r'https?://[^\s\'"]*mibei77[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*mm\.[^\s\'"]*\.txt[^\s\'"]*',
            # 包含日期的链接
            r'https?://[^\s\'"]*/\d{4}\.\d{2}[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*/\d{8}[^\s\'"]*\.txt[^\s\'"]*',
        ]

        for pattern in mibei77_patterns:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                links.extend(matches)
            except Exception as e:
                self.logger.warning(f"米贝77链接匹配失败: {pattern} - {str(e)}")

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
                    self.logger.info(f"找到米贝77订阅链接: {clean_link}")

        self.logger.info(f"米贝77找到 {len(cleaned_links)} 个订阅链接")

        return cleaned_links

    def _is_valid_subscription_link(self, url):
        """验证是否为有效的V2Ray订阅链接"""
        # 排除明显的非V2Ray链接
        excluded_patterns = [
            r".*clash.*",
            r".*sing.*box.*",
            r".*yaml.*",
            r".*json.*",
        ]

        for pattern in excluded_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False

        return True

    def extract_direct_nodes(self, content):
        """重写直接节点提取方法"""
        nodes = []

        # 调用父类方法
        parent_nodes = super().extract_direct_nodes(content)
        nodes.extend(parent_nodes)

        # 米贝节点可能有特殊的节点展示格式
        # 查找包含节点信息的特定区域
        node_areas = [
            r'<div[^>]*class="[^"]*(?:node|config|subscription)[^"]*"[^>]*>(.*?)</div>',
            r'<pre[^>]*class="[^"]*(?:node|config)[^"]*"[^>]*>(.*?)</pre>',
            r'<textarea[^>]*class="[^"]*(?:node|config)[^"]*"[^>]*>(.*?)</textarea>',
        ]

        for pattern in node_areas:
            try:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    area_nodes = self.parse_node_text(match)
                    nodes.extend(area_nodes)
            except Exception as e:
                self.logger.warning(f"节点区域匹配失败: {pattern} - {str(e)}")

        # 查找可能在表格中的节点
        table_pattern = r"<table[^>]*>(.*?)</table>"
        try:
            tables = re.findall(table_pattern, content, re.DOTALL | re.IGNORECASE)
            for table in tables:
                table_nodes = self.parse_node_text(table)
                nodes.extend(table_nodes)
        except Exception as e:
            self.logger.debug(f"表格解析失败: {str(e)}")

        return list(set(nodes))  # 去重
