#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FreeClashNode 爬虫
"""

import re
import base64
import time
import random
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


class FreeClashNodeCollector(BaseCollector):
    """FreeClashNode 专用爬虫"""

    def __init__(self, site_config):
        super().__init__(site_config)
        # 添加额外的请求头以绕过反爬虫
        self.session.headers.update(
            {
                "Referer": "https://www.freeclashnode.com/",
                "Origin": "https://www.freeclashnode.com",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
            }
        )
        # 移除硬编码的代理禁用，让父类统一管理代理

    def _get_latest_article_url(self):
        """获取最新文章URL"""
        try:
            self.logger.info("正在查找最新文章...")

            # 访问主页
            main_page = self._get_page(self.base_url)
            if not main_page:
                self.logger.error("无法获取主页内容")
                return None

            soup = BeautifulSoup(main_page, "html.parser")

            # 查找今天日期的文章链接
            today = datetime.now().strftime("%Y-%m-%d")
            article_pattern = f"/free-node/{today}-"

            # 在所有链接中查找
            links = soup.find_all("a", href=True)
            for link in links:
                href = link.get("href", "")
                if article_pattern in href:
                    article_url = urljoin(self.base_url, href)
                    self.logger.info(f"找到今日文章: {article_url}")
                    return article_url

            # 如果没找到今天的，尝试最新的文章
            self.logger.info(f"未找到今日文章，尝试获取最新文章...")
            # 查找最新文章的模式
            latest_pattern = r"/free-node/\d{4}-\d{1,2}-\d{1,2}-"

            for link in links:
                href = link.get("href", "")
                if re.search(latest_pattern, href) and ".htm" in href:
                    article_url = urljoin(self.base_url, href)
                    self.logger.info(f"找到最新文章: {article_url}")
                    return article_url

            self.logger.warning("未找到任何文章链接")
            return None

        except requests.exceptions.Timeout as e:
            self.logger.error(f"获取最新文章URL超时: {str(e)}")
            return None
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"获取最新文章URL连接错误: {str(e)}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取最新文章URL网络请求错误: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"获取最新文章URL失败: {str(e)}")
            return None

    def _make_request(self, url, method="GET", **kwargs):
        """重写请求方法，添加随机延迟"""
        # 添加随机延迟以模拟人类行为
        time.sleep(random.uniform(1, 3))

        # 调用父类方法
        return super()._make_request(url, method, **kwargs)

    def find_subscription_links(self, content):
        """重写订阅链接查找方法，处理特殊的污染格式"""
        links = []

        # 处理freeclashnode.com的特殊格式
        links.extend(self._extract_polluted_links(content))

        # 调用父类方法
        parent_links = super().find_subscription_links(content)
        links.extend(parent_links)

        # 去重
        return list(set(links))

    def _extract_polluted_links(self, content):
        """提取被HTML标签污染的链接"""
        links = []

        # 查找所有node.freeclashnode.com的URL片段
        pattern = r"node\.freeclashnode\.com/uploads/\d{4}/\d{2}/[^\s\\<]*"
        matches = re.findall(pattern, content, re.IGNORECASE)

        # 额外查找完整的.txt链接（处理污染格式）
        txt_pattern = (
            r"(https?://node\.freeclashnode\.com/uploads/\d{4}/\d{2}/[^\\s\\<]*\.txt)"
        )
        txt_matches = re.findall(txt_pattern, content, re.IGNORECASE)

        # 合并匹配结果
        all_matches = list(set(matches + txt_matches))

        # 为每个匹配找到完整的URL
        for match in all_matches:
            # 尝试不同的文件扩展名
            for ext in [".txt", ".yaml", ".json"]:
                # 构建基础URL模式
                base_pattern = f"(https?://{match}[^\\s]*)"
                base_matches = re.findall(base_pattern, content, re.IGNORECASE)

                for base_match in base_matches:
                    # 清理URL
                    clean_url = base_match
                    # 移除污染部分
                    for separator in [
                        "pp",
                        "Clash免费节点",
                        "Sing-Box免费节点:",
                        "strong",
                        "span",
                    ]:
                        if separator in clean_url:
                            clean_url = clean_url.split(separator)[0]

                    # 确保以正确的扩展名结尾
                    if not clean_url.endswith(ext):
                        # 尝试找到正确的结尾位置
                        if ext in clean_url:
                            # 截取到扩展名位置
                            ext_pos = clean_url.find(ext)
                            clean_url = clean_url[: ext_pos + len(ext)]
                        else:
                            continue

                    # 验证URL格式
                    if clean_url.endswith(ext) and len(clean_url) > 40:
                        links.append(clean_url)

        # 备用方法：手动解析特定的污染字符串
        if "node.freeclashnode.com" in content:
            # 查找所有以https://node.freeclashnode.com开头的部分
            parts = content.split("https://node.freeclashnode.com")
            for i, part in enumerate(parts[1:], 1):  # 跳过第一个空部分
                # 查找下一个分隔符
                separators = [
                    "pphttps://",
                    "Clash免费节点https://",
                    "Sing-Box免费节点:https://",
                    "stronghttps://",
                    "spanhttps://",
                ]
                clean_part = part

                for sep in separators:
                    if sep in clean_part:
                        clean_part = clean_part.split(sep)[0]
                        break

                # 尝试不同的文件扩展名
                candidate = "https://node.freeclashnode.com" + clean_part
                for ext in [".txt", ".yaml", ".json"]:
                    if ext in candidate:
                        ext_pos = candidate.find(ext)
                        final_url = candidate[: ext_pos + len(ext)]
                        if final_url not in links and len(final_url) > 40:
                            links.append(final_url)

        return links

    def get_nodes_from_subscription(self, subscription_url):
        """使用统一订阅解析器处理订阅链接"""
        from src.core.subscription_parser import get_subscription_parser

        parser = get_subscription_parser()
        return parser.parse_subscription_url(subscription_url, self.session)

    def get_v2ray_subscription_links(self, article_url):
        """获取V2Ray订阅链接（重写方法以处理特殊格式）"""
        try:
            self.logger.info(f"正在解析文章获取V2Ray订阅链接: {article_url}")
            response = self.session.get(article_url, timeout=self.timeout, verify=False)
            response.raise_for_status()

            content = response.text

            # 使用专门的污染链接提取方法
            links = self._extract_polluted_links(content)

            # 过滤V2Ray订阅链接
            v2ray_links = []
            for link in links:
                if self.is_v2ray_subscription(link):
                    v2ray_links.append(link)

            self.logger.info(f"从文章中找到 {len(v2ray_links)} 个V2Ray订阅链接")
            return v2ray_links

        except Exception as e:
            self.logger.error(f"获取V2Ray订阅链接失败: {str(e)}")
            return []
