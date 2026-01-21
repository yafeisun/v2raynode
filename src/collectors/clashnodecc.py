#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClashNodeCC 爬虫
"""

import re
import base64
from bs4 import BeautifulSoup
from src.core.base_collector import BaseCollector


class ClashNodeCCCollector(BaseCollector):
    """ClashNodeCC 专用爬虫"""

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

            # ClashNodeCC可能的文章链接选择器
            selectors = [
                "article:first-child a",  # 第一篇文章的链接
                ".post:first-child a",  # 第一个文章的链接
                ".entry-title:first-child a",  # 第一个条目标题
                "h1 a",  # h1标题链接
                "h2 a",  # h2标题链接
                ".post-title a",  # 文章标题链接
                ".entry-title a",  # 条目标题链接
                "article h2 a",  # 文章中的h2链接
                ".content h2 a",  # 内容区域的h2链接
                ".latest-post a",  # 最新文章链接
                'a[href*="/archives/"]',  # 归档链接
                'a[href*="/post/"]',  # 文章链接
                'a[href*="/node/"]',  # 节点相关链接
            ]

            # 先尝试特定选择器
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    href = links[0].get("href")
                    if href:
                        article_url = self._process_url(href)
                        self.logger.info(f"通过选择器找到文章: {article_url}")
                        return article_url

            # 调用父类方法作为后备
            return super().get_latest_article_url()

        except Exception as e:
            self.logger.error(f"获取文章链接失败: {str(e)}")
            return None

    def find_subscription_links(self, content):
        """重写订阅链接查找方法，专门查找ClashNodeCC的订阅链接"""
        links = []

        # ClashNodeCC特定的订阅链接模式
        clashnodecc_patterns = [
            # 标准订阅链接（http开头，.txt结尾）
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            # 包含常见关键词的链接
            r'https?://[^\s\'"]*(?:sub|subscribe|link|api|node)[^\s\'"]*\.txt[^\s\'"]*',
            # 可能的域名模式
            r'https?://[^\s\'"]*(?:github\.com|gitlab\.com|raw\.githubusercontent\.com)[^\s\'"]*\.txt[^\s\'"]*',
            # 其他可能的订阅链接格式
            r'https?://[^\s\'"]*/[^\s\'"]*(?:sub|subscribe|link)[^\s\'"]*',
            # 直接的txt文件链接
            r'https?://[^\s\'"]*\.txt',
        ]

        for pattern in clashnodecc_patterns:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    clean_link = self._clean_link(match)
                    if clean_link and self._is_valid_url(clean_link):
                        # 过滤掉HTML页面，只保留真正的订阅文件
                        if not clean_link.endswith(
                            (".htm", ".html", ".htm/", ".html/")
                        ):
                            links.append(clean_link)
                            self.logger.info(f"找到订阅链接: {clean_link}")
            except Exception as e:
                self.logger.warning(f"订阅链接匹配失败: {pattern} - {str(e)}")

        # 处理合并的链接问题 - 查找可能被合并的多个链接
        merged_pattern = r'(https?://[^\s\'"]*\.txt[^\s\'"]*)'
        try:
            matches = re.findall(merged_pattern, content, re.IGNORECASE)
            for match in matches:
                # 检查是否包含多个http（合并的链接）
                if match.count("http") > 1:
                    # 分割合并的链接
                    parts = match.split("http")
                    for i, part in enumerate(parts):
                        if i == 0:
                            continue
                        reconstructed = "http" + part
                        clean_link = self._clean_link(reconstructed)
                        if clean_link and self._is_valid_url(clean_link):
                            links.append(clean_link)
                            self.logger.info(f"从合并链接中提取: {clean_link}")
                else:
                    clean_link = self._clean_link(match)
                    if clean_link and self._is_valid_url(clean_link):
                        # 过滤掉HTML页面，只保留真正的订阅文件
                        if not clean_link.endswith(
                            (".htm", ".html", ".htm/", ".html/")
                        ):
                            links.append(clean_link)
        except Exception as e:
            self.logger.warning(f"合并链接处理失败: {str(e)}")

        # 在关键词附近查找
        subscription_keywords = [
            "clash订阅",
            "v2ray订阅",
            "节点订阅",
            "订阅链接",
            "免费节点",
            "clash sub",
            "v2ray sub",
            "node sub",
            "subscription link",
            "clash配置",
            "v2ray配置",
            "节点配置",
        ]

        for keyword in subscription_keywords:
            try:
                pattern = rf"{keyword}[^:]*[:：]\s*(https?://[^\s\n\r]+)"
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    clean_link = self._clean_link(match)
                    if clean_link and self._is_valid_url(clean_link):
                        # 过滤掉HTML页面，只保留真正的订阅文件
                        if not clean_link.endswith(
                            (".htm", ".html", ".htm/", ".html/")
                        ):
                            links.append(clean_link)
                            self.logger.info(f"通过关键词找到订阅链接: {clean_link}")
            except Exception as e:
                self.logger.debug(f"关键词订阅链接匹配失败: {str(e)}")

        # 查找可能在特定区域中的链接
        area_patterns = [
            r'<div[^>]*class="[^"]*(?:subscription|node|clash|v2ray)[^"]*"[^>]*>(.*?)</div>',
            r'<pre[^>]*class="[^"]*(?:subscription|node|clash|v2ray)[^"]*"[^>]*>(.*?)</pre>',
            r'<textarea[^>]*class="[^"]*(?:subscription|node|clash|v2ray)[^"]*"[^>]*>(.*?)</textarea>',
            r'<code[^>]*class="[^"]*(?:subscription|node|clash|v2ray)[^"]*"[^>]*>(.*?)</code>',
        ]

        for pattern in area_patterns:
            try:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    # 在区域内查找订阅链接
                    sub_pattern = r'(https?://[^\s\'"]*)'
                    sub_matches = re.findall(sub_pattern, match, re.IGNORECASE)
                    for sub_match in sub_matches:
                        clean_link = self._clean_link(sub_match)
                        if clean_link and self._is_valid_url(clean_link):
                            # 过滤掉HTML页面，只保留真正的订阅文件
                            if not clean_link.endswith(
                                (".htm", ".html", ".htm/", ".html/")
                            ):
                                links.append(clean_link)
            except Exception as e:
                self.logger.warning(f"区域订阅链接匹配失败: {pattern} - {str(e)}")

        # 查找可能被HTML标签污染的链接
        polluted_patterns = [
            r"https?://[^\s<]*\.txt[^<]*",
            r'(https?://[^\s\'"]*\.txt)',
        ]

        for pattern in polluted_patterns:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    clean_link = self._clean_link(match)
                    if clean_link and self._is_valid_url(clean_link):
                        # 过滤掉HTML页面，只保留真正的订阅文件
                        if not clean_link.endswith(
                            (".htm", ".html", ".htm/", ".html/")
                        ):
                            links.append(clean_link)
            except Exception as e:
                self.logger.warning(f"污染链接匹配失败: {pattern} - {str(e)}")

        # 去重
        unique_links = list(set(links))
        self.logger.info(f"ClashNodeCC找到 {len(unique_links)} 个订阅链接")

        return unique_links

    def get_nodes_from_subscription(self, subscription_url):
        """使用统一订阅解析器处理订阅链接"""
        from src.core.subscription_parser import get_subscription_parser

        parser = get_subscription_parser()
        return parser.parse_subscription_url(subscription_url, self.session)

    def extract_direct_nodes(self, content):
        """重写直接节点提取方法"""
        nodes = []

        # 使用标准节点模式
        from src.config.websites import NODE_PATTERNS

        for pattern in NODE_PATTERNS:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    node = match.strip()
                    if node and len(node) >= 50:  # 节点长度通常大于50
                        nodes.append(node)
            except Exception as e:
                self.logger.warning(f"节点匹配失败: {pattern} - {str(e)}")

        # 从代码块中提取
        code_patterns = [
            r"<code[^>]*>(.*?)</code>",
            r"<pre[^>]*>(.*?)</pre>",
            r"<textarea[^>]*>(.*?)</textarea>",
        ]

        for pattern in code_patterns:
            try:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    block_nodes = self.parse_node_text(match)
                    nodes.extend(block_nodes)
            except Exception as e:
                self.logger.warning(f"代码块匹配失败: {pattern} - {str(e)}")

        # 从Base64内容中提取
        base64_pattern = r"([A-Za-z0-9+/]{50,}={0,2})"
        try:
            matches = re.findall(base64_pattern, content)
            for match in matches:
                try:
                    decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
                    if any(
                        proto in decoded.lower()
                        for proto in ["vmess://", "vless://", "trojan://", "ss://"]
                    ):
                        decoded_nodes = self.parse_node_text(decoded)
                        nodes.extend(decoded_nodes)
                except Exception as e:
                    self.logger.debug(f"Base64解码失败: {str(e)}")
        except Exception as e:
            self.logger.debug(f"Base64模式匹配失败: {str(e)}")

        return list(set(nodes))  # 去重

    def _clean_link(self, link):
        """重写链接清理方法，处理ClashNodeCC的特殊格式"""
        if not link:
            return ""

        # 调用父类的清理方法
        clean_link = super()._clean_link(link)

        # ClashNodeCC特定的清理规则
        # 移除常见的HTML标签和污染
        contaminants = [
            "</strong>",
            "</span>",
            "</div>",
            "</p>",
            "</h1>",
            "</h2>",
            "</h3>",
            "<strong>",
            "<span>",
            "<div>",
            "<p>",
            "<h1>",
            "<h2>",
            "<h3>",
            "&nbsp;",
            "&lt;",
            "&gt;",
            "&amp;",
            "&quot;",
            "clash订阅链接",
            "sing-box订阅链接",  # 移除这些文本标识
        ]

        for contaminant in contaminants:
            clean_link = clean_link.replace(contaminant, "")

        # 处理合并的链接问题
        # 如果链接中包含多个http，说明有链接被合并了
        if clean_link.count("http") > 1:
            # 分割合并的链接
            parts = clean_link.split("http")
            links = []
            for i, part in enumerate(parts):
                if i == 0:
                    continue  # 第一个部分是空的
                reconstructed = "http" + part
                # 找到合适的结束位置
                for end_marker in [" ", "\n", "\r", "\t", "<", '"', "'", ")", "]", "}"]:
                    if end_marker in reconstructed:
                        end_pos = reconstructed.find(end_marker)
                        candidate = reconstructed[:end_pos]
                        if (
                            candidate.endswith((".txt", ".yaml", ".json"))
                            or "sub" in candidate
                            or "subscribe" in candidate
                        ):
                            links.append(candidate)
                            break
                else:
                    # 如果没有找到结束标记，检查整个链接
                    if (
                        reconstructed.endswith((".txt", ".yaml", ".json"))
                        or "sub" in reconstructed
                        or "subscribe" in reconstructed
                    ):
                        links.append(reconstructed)

            # 返回第一个有效的链接（因为这是在单个链接处理中）
            if links:
                clean_link = links[0]

        # 处理单个链接的截断问题
        if "http" in clean_link:
            # 找到第一个http开始
            http_start = clean_link.find("http")
            clean_link = clean_link[http_start:]

            # 找到合适的结束位置
            for end_marker in [" ", "\n", "\r", "\t", "<", '"', "'", ")", "]", "}"]:
                if end_marker in clean_link:
                    end_pos = clean_link.find(end_marker)
                    candidate = clean_link[:end_pos]
                    if (
                        candidate.endswith((".txt", ".yaml", ".json"))
                        or "sub" in candidate
                        or "subscribe" in candidate
                    ):
                        clean_link = candidate
                        break

        return clean_link.strip()
