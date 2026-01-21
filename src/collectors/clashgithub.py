#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClashGithub 爬虫
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


class ClashGithubCollector(BaseCollector):
    """ClashGithub 专用爬虫"""

    def __init__(self, site_config):
        super().__init__(site_config)
        # 添加额外的请求头以绕过反爬虫
        self.session.headers.update(
            {
                "Referer": "https://clashgithub.com/",
                "Origin": "https://clashgithub.com",
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
        """获取文章URL - ClashGithub 使用固定格式的文章链接"""
        try:
            if target_date is None:
                target_date = datetime.now()

            # 生成日期格式的文章链接
            date_str = target_date.strftime("%Y%m%d")
            article_url = f"https://clashgithub.com/clashnode-{date_str}.html"

            self.logger.info(f"使用固定文章链接: {article_url}")
            return article_url

        except Exception as e:
            self.logger.error(f"获取文章链接失败: {str(e)}")
            return None

    def find_subscription_links(self, content):
        """查找订阅链接 - 重写以处理 ClashGithub 的特殊格式"""
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

    def get_v2ray_subscription_links(self, article_url):
        """获取V2Ray订阅链接（重写方法以处理特殊格式）"""
        try:
            self.logger.info(f"正在解析文章获取V2Ray订阅链接: {article_url}")
            response = self.session.get(article_url, timeout=self.timeout, verify=False)
            response.raise_for_status()

            content = response.text

            # 查找所有订阅链接
            links = self.find_subscription_links(content)

            # 过滤V2Ray订阅链接
            v2ray_links = []
            for link in links:
                if self.is_v2ray_subscription(link):
                    v2ray_links.append(link)

            # ClashGithub 特殊处理：如果没有订阅链接，返回一个特殊标记
            # 表示节点直接在文章中，需要通过 extract_nodes_from_article 提取
            if not v2ray_links:
                # 返回一个特殊的URL，表示需要从文章直接提取节点
                special_link = f"{article_url}#direct_nodes"
                self.logger.info(f"网站直接提供节点，使用特殊标记: {special_link}")
                return [special_link]

            self.logger.info(f"从文章中找到 {len(v2ray_links)} 个V2Ray订阅链接")
            return v2ray_links

        except Exception as e:
            self.logger.error(f"获取V2Ray订阅链接失败: {str(e)}")
            return []

    def extract_nodes_from_article(self, article_url):
        """从文章中提取节点 - ClashGithub 从文章HTML直接提取节点或订阅链接"""
        try:
            self.logger.info(f"解析文章: {article_url}")
            response = self._make_request(article_url)

            content = response.text
            self.raw_data = content

            nodes = []

            # 方法1: 直接从文章HTML中提取节点
            self.logger.info("尝试直接从文章HTML中提取节点")
            node_patterns = [
                r'(vmess://[^\s\n\r<>"]+)',
                r'(vless://[^\s\n\r<>"]+)',
                r'(trojan://[^\s\n\r<>"]+)',
                r'(hysteria2://[^\s\n\r<>"]+)',
                r'(hysteria://[^\s\n\r<>"]+)',
                r'(ss://[^\s\n\r<>"]+)',
                r'(ssr://[^\s\n\r<>"]+)',
            ]

            for pattern in node_patterns:
                matches = re.findall(pattern, content)
                nodes.extend(matches)

            if nodes:
                self.logger.info(f"从文章HTML直接提取到 {len(nodes)} 个节点")

            # 方法2: 从代码块中提取
            self.logger.info("尝试从代码块中提取节点")
            soup = BeautifulSoup(content, "html.parser")
            code_blocks = soup.find_all(["code", "pre", "textarea"])

            for block in code_blocks:
                block_content = block.get_text(strip=True)
                if len(block_content) > 50:
                    for pattern in node_patterns:
                        matches = re.findall(pattern, block_content)
                        nodes.extend(matches)

            if nodes:
                self.logger.info(
                    f"从代码块额外提取到 {len(list(set(nodes))) - len(set(nodes))} 个新节点"
                )

            # 方法3: 从订阅链接获取节点
            self.logger.info("尝试从订阅链接获取节点")
            subscription_links = self.find_subscription_links(content)

            for link in subscription_links:
                self.logger.info(f"找到订阅链接: {link}")
                try:
                    sub_nodes = self.get_nodes_from_subscription(link)
                    nodes.extend(sub_nodes)
                    time.sleep(self.delay)
                except Exception as e:
                    self.logger.warning(f"从订阅链接获取节点失败: {link} - {str(e)}")

            # 去重
            nodes = list(set(nodes))

            self.logger.info(f"从文章提取到 {len(nodes)} 个节点")
            return nodes

        except Exception as e:
            self.logger.error(f"解析文章失败: {str(e)}")
            return []

    def get_nodes_from_subscription(self, subscription_url):
        """从订阅链接获取节点 - 重写以处理特殊标记"""
        # 检查是否为特殊标记（直接从文章提取节点）
        if subscription_url.endswith("#direct_nodes"):
            article_url = subscription_url.replace("#direct_nodes", "")
            self.logger.info(f"检测到特殊标记，直接从文章提取节点: {article_url}")
            return self.extract_nodes_from_article(article_url)

        # 否则使用父类方法
        return super().get_nodes_from_subscription(subscription_url)
