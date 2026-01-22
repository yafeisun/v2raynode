#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clash Meta 爬虫
"""

import re
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


class ClashMetaCollector(BaseCollector):
    """Clash Meta 专用爬虫"""

    def __init__(self, site_config):
        super().__init__(site_config)
        self.session.headers.update(
            {
                "Referer": "https://clash-meta.github.io/",
                "Origin": "https://clash-meta.github.io",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
            }
        )

    def _get_latest_article_url(self):
        """获取最新文章URL列表"""
        try:
            self.logger.info("正在查找最新文章...")

            # 访问主页
            response = self._make_request(self.base_url)
            if not response:
                self.logger.error("无法获取主页内容")
                return []

            main_page = response.text
            soup = BeautifulSoup(main_page, "html.parser")

            # 查找文章链接
            article_pattern = r"/free-nodes/\d{4}-\d{1,2}-\d{1,2}-free-subscribe-node\.htm"
            article_urls = []
            seen = set()

            links = soup.find_all("a", href=True)
            for link in links:
                href = link.get("href", "")
                if re.search(article_pattern, href):
                    article_url = urljoin(self.base_url, href)
                    if article_url not in seen:
                        seen.add(article_url)
                        article_urls.append(article_url)

            # 最多返回前3个文章链接
            if article_urls:
                self.logger.info(f"找到 {len(article_urls)} 篇文章")
                return article_urls[:3]

            self.logger.warning("未找到任何文章链接")
            return []

        except Exception as e:
            self.logger.error(f"获取文章链接失败: {str(e)}")
            return []

    def _extract_subscription_links(self, article_url):
        """从文章内容中提取订阅链接"""
        links = []
        try:
            response = self._make_request(article_url)
            if not response:
                self.logger.error("无法获取文章内容")
                return links

            article_content = response.text
            soup = BeautifulSoup(article_content, "html.parser")

            # 查找所有链接
            all_links = soup.find_all("a", href=True)

            for link in all_links:
                href = link.get("href", "")

                # 匹配订阅链接模式
                if re.search(r"clash-meta\.github\.io/uploads/\d{4}/\d{2}/", href):
                    clean_link = urljoin(self.base_url, href)
                    if clean_link and clean_link not in links:
                        links.append(clean_link)
                        self.logger.info(f"找到订阅链接: {clean_link}")

            # 如果没有找到，尝试从文本中提取
            if not links:
                text = soup.get_text()
                # 匹配 yaml, txt, json 文件
                url_pattern = r"https?://clash-meta\.github\.io/uploads/\d{4}/\d{2}/[^\s]+?\.(?:yaml|txt|json)"
                matches = re.findall(url_pattern, text)
                for match in matches:
                    full_url = urljoin(self.base_url, match)
                    if full_url not in links:
                        links.append(full_url)
                        self.logger.info(f"从文本中提取订阅链接: {full_url}")

            return links

        except Exception as e:
            self.logger.error(f"提取订阅链接失败: {str(e)}")
            return links

    def collect(self):
        """收集节点"""
        try:
            self.logger.info(f"开始收集 {self.site_name}...")

            # 获取最新文章URL列表
            article_urls = self._get_latest_article_url()
            if not article_urls:
                raise ArticleLinkNotFoundError("未找到文章链接")

            # 从所有文章中提取订阅链接
            all_subscription_links = []
            for article_url in article_urls:
                try:
                    subscription_links = self._extract_subscription_links(article_url)
                    all_subscription_links.extend(subscription_links)
                except Exception as e:
                    self.logger.error(f"提取订阅链接失败 {article_url}: {str(e)}")
                    continue

            # 去重订阅链接
            all_subscription_links = list(set(all_subscription_links))

            if not all_subscription_links:
                self.logger.warning("未找到订阅链接")
                return []

            # 解析订阅链接获取节点
            from src.core.subscription_parser import get_subscription_parser
            parser = get_subscription_parser()

            all_nodes = []
            for sub_url in all_subscription_links:
                try:
                    self.logger.info(f"正在解析订阅链接: {sub_url}")
                    nodes = parser.parse_subscription_url(sub_url, self.session)
                    if nodes:
                        all_nodes.extend(nodes)
                        self.logger.info(f"从 {sub_url} 获取到 {len(nodes)} 个节点")
                except Exception as e:
                    self.logger.error(f"解析订阅链接失败 {sub_url}: {str(e)}")
                    continue

            # 去重和过滤
            unique_nodes = self._deduplicate_and_filter_nodes(all_nodes)

            self.logger.info(f"{self.site_name} 收集完成，共 {len(unique_nodes)} 个节点")
            return unique_nodes

        except Exception as e:
            self.logger.error(f"{self.site_name} 收集失败: {str(e)}")
            return []