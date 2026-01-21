#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datiya 爬虫
"""

import re
import base64
from datetime import datetime
from bs4 import BeautifulSoup
from src.core.base_collector import BaseCollector
from src.config.websites import UNIVERSAL_SELECTORS


class DatiyaCollector(BaseCollector):
    """Datiya 专用爬虫"""

    def __init__(self, site_config):
        super().__init__(site_config)
        self.session.headers.update(
            {
                "Referer": "https://free.datiya.com/",
                "Origin": "https://free.datiya.com/",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
            }
        )

    def _get_latest_article_url(self):
        """获取最新文章URL - 实现抽象方法"""
        return self.get_latest_article_url()

    def get_latest_article_url(self, target_date=None):
        """获取文章URL，支持指定日期"""
        try:
            response = self._make_request(self.base_url)
            response_text = response.text
            if not response_text:
                self.logger.error("无法获取页面内容")
                return None

            soup = BeautifulSoup(response_text, "html.parser")

            if not target_date:
                target_date = datetime.now()

            date_str = target_date.strftime("%Y%m%d")

            today_links = soup.find_all(
                "a", href=re.compile(f"/post/{date_str}", re.IGNORECASE)
            )

            for link in today_links:
                href = link.get("href")
                text = link.get_text(strip=True)

                if href and text and date_str in text:
                    article_url = self._process_url(href)
                    self.logger.info(f"通过日期匹配找到文章: {article_url}")
                    return article_url

            if not today_links:
                selectors = [
                    ".post-title a",
                    ".entry-title a",
                    "h1 a",
                    "h2 a",
                    "article h2 a",
                    "content h2 a",
                ]

                for selector in selectors:
                    links = soup.select(selector)
                    if links:
                        href = links[0].get("href")
                        if href:
                            article_url = self._process_url(href)
                            self.logger.info(f"通过选择器找到文章: {article_url}")
                            return article_url

            for selector in UNIVERSAL_SELECTORS:
                links = soup.select(selector)
                if links:
                    href = links[0].get("href")
                    if href:
                        article_url = self._process_url(href)
                        self.logger.info(f"通过通用选择器找到文章: {article_url}")
                        return article_url

            self.logger.warning(f"未找到文章链接")
            return None

        except Exception as e:
            self.logger.error(f"获取文章链接失败: {str(e)}")
            return None

    def find_subscription_links(self, content):
        """查找订阅链接"""
        links = []

        parent_links = super().find_subscription_links(content)
        links.extend(parent_links)

        datiya_patterns = [
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            r"https?://free\.datiya\.com/uploads/\d{8}[^\s<]*\.yaml",
        ]

        for pattern in datiya_patterns:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    clean_link = self._clean_link(match)
                    if clean_link and self._is_valid_url(clean_link):
                        links.append(clean_link)
                        self.logger.info(f"找到订阅链接: {clean_link}")
            except Exception as e:
                self.logger.warning(f"订阅链接匹配失败: {pattern} - {str(e)}")

        return list(set(links))

    def get_nodes_from_subscription(self, subscription_url):
        """使用统一订阅解析器处理订阅链接"""
        from src.core.subscription_parser import get_subscription_parser

        parser = get_subscription_parser()
        return parser.parse_subscription_url(subscription_url, self.session)

    def _extract_datiya_yaml_nodes(self, content):
        """从Datiya的YAML格式提取节点"""
        nodes = []
        try:
            import yaml

            yaml_data = yaml.safe_load(content)

            if "proxies" in yaml_data:
                proxies = yaml_data["proxies"]
                for proxy in proxies:
                    try:
                        node = self._convert_clash_proxy_to_node(proxy)
                        if node and len(node) >= 50:
                            nodes.append(node)
                    except Exception as e:
                        self.logger.debug(f"代理转换失败: {str(e)}")

            self.logger.info(f"从Datiya YAML解析获取到 {len(nodes)} 个节点")

        except Exception as e:
            self.logger.error(f"YAML解析失败: {str(e)}")
            try:
                import re

                proxy_pattern = r"  - \{([^}]+)\}"
                matches = re.findall(proxy_pattern, content)

                for match in matches:
                    try:
                        kv_pattern = r"([a-zA-Z-]+):\s*([^,}]+)"
                        kv_pairs = re.findall(kv_pattern, match)
                        proxy = dict(kv_pairs)

                        if "port" in proxy:
                            proxy["port"] = int(proxy["port"])
                        if "skip-cert-verify" in proxy:
                            proxy["skip-cert-verify"] = (
                                proxy["skip-cert-verify"].lower() == "true"
                            )
                        if "tls" in proxy:
                            proxy["tls"] = proxy["tls"].lower() == "true"

                        node = self._convert_clash_proxy_to_node(proxy)
                        if node and len(node) >= 50:
                            nodes.append(node)
                    except Exception as e:
                        self.logger.debug(f"YAML fallback解析失败: {str(e)}")

                self.logger.info(f"从YAML fallback解析获取到 {len(nodes)} 个节点")

            except Exception as fallback_e:
                self.logger.error(f"YAML fallback解析也失败: {str(fallback_e)}")

        return nodes

    def extract_direct_nodes(self, content):
        """从文章内容提取直接节点"""
        nodes = []

        from src.config.websites import NODE_PATTERNS

        for pattern in NODE_PATTERNS:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    node = match.strip()
                    if len(node) >= 50:
                        nodes.append(node)
            except Exception as e:
                self.logger.warning(f"节点匹配失败: {pattern} - {str(e)}")

        return list(set(nodes))

    def _clean_link(self, link):
        """重写链接清理方法，处理Datiya的特殊格式"""
        if not link:
            return ""

        clean_link = super()._clean_link(link)

        clean_link = (
            clean_link.replace("%3C", "").replace("%3E", "").replace("%20", " ")
        )

        contaminants = [
            "</strong>",
            "</span>",
            "</div>",
            "<p>",
            "</h1>",
            "</h2>",
            "</h3>",
            "Clash订阅链接",
            "Sing-Box免费节点:",
        ]

        for contaminant in contaminants:
            clean_link = clean_link.replace(contaminant, "")

        return clean_link.strip()

    def _is_valid_url(self, url):
        """重写URL验证方法，支持Datiya的格式"""
        try:
            import urllib.parse

            parsed = urllib.parse.urlparse(url)
            return bool(parsed.scheme and parsed.netloc and len(url) > 10)
        except:
            return False
