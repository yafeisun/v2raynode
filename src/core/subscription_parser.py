#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一订阅链接解析器
负责解析各种格式的订阅链接，提取节点信息
"""

import re
import base64
import requests
import time
from typing import List, Optional, Dict, Any
from urllib.parse import unquote

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

from src.core.config_manager import get_config
from src.core.protocol_converter import get_converter, extract_nodes_from_text
from src.utils.logger import get_logger
from src.core.exceptions import (
    NetworkError,
    RequestTimeoutError,
    ConnectionError as V2RayConnectionError,
    ProxyError,
    SubscriptionParseError,
    NodeParseError,
)


class SubscriptionParser:
    """统一订阅链接解析器"""

    def __init__(self):
        self.config_manager = get_config()
        self.logger = get_logger("subscription_parser")

        # 配置参数
        self.timeout = self.config_manager.base.REQUEST_TIMEOUT
        self.min_node_length = self.config_manager.base.MIN_NODE_LENGTH

        # 协议转换器
        self.converter = get_converter(self.logger)

        # 节点协议模式
        self.node_patterns = [
            r'vmess://[^\s<>"]+',  # VMess
            r'vless://[^\s<>"]+',  # VLESS
            r'trojan://[^\s<>"]+',  # Trojan
            r'ss://[^\s<>"]+',  # Shadowsocks
            r'ssr://[^\s<>"]+',  # ShadowsocksR
            r'hysteria://[^\s<>"]+',  # Hysteria
            r'hysteria2://[^\s<>"]+',  # Hysteria2
            r'socks5://[^\s<>"]+',  # SOCKS5
            r'reality://[^\s<>"]+',  # Reality
        ]

    def parse_subscription_url(
        self, url: str, session: Optional[requests.Session] = None
    ) -> List[str]:
        """
        解析订阅链接，提取节点信息

        Args:
            url: 订阅链接URL
            session: 可选的requests会话

        Returns:
            节点列表
        """
        try:
            # 过滤掉HTML页面（文章页面，不是订阅内容）
            if url.endswith((".htm", ".html", ".htm/", ".html/")):
                self.logger.info(f"跳过HTML页面: {url}")
                return []

            # 获取订阅内容
            content = self._fetch_subscription_content(url, session)
            if content is None:
                simplified_url = (
                    url.replace("https://", "").replace("http://", "").split("/")[0]
                    + "/"
                    + "/".join(url.split("/")[-2:])
                )
                self.logger.warning(f"❌ {simplified_url}: 无法获取订阅内容")
                return []
            elif not content.strip():
                simplified_url = (
                    url.replace("https://", "").replace("http://", "").split("/")[0]
                    + "/"
                    + "/".join(url.split("/")[-2:])
                )
                self.logger.warning(f"❌ {simplified_url}: 订阅内容为空")
                return []

            # 解析不同格式的内容
            nodes = self._parse_subscription_content(content)

            # 只在有节点时记录成功，否则记录失败
            if nodes:
                # 显示简化的URL（保留域名和关键路径）
                simplified_url = (
                    url.replace("https://", "").replace("http://", "").split("/")[0]
                    + "/"
                    + "/".join(url.split("/")[-2:])
                )
                self.logger.info(f"✓ {simplified_url}: {len(nodes)} 个节点")
            else:
                simplified_url = (
                    url.replace("https://", "").replace("http://", "").split("/")[0]
                    + "/"
                    + "/".join(url.split("/")[-2:])
                )
                self.logger.debug(f"⚠️ {simplified_url}: 0 个节点")

            return nodes

        except Exception as e:
            simplified_url = (
                url.replace("https://", "").replace("http://", "").split("/")[0]
                + "/"
                + "/".join(url.split("/")[-2:])
            )
            self.logger.warning(f"❌ {simplified_url}: 解析失败 - {str(e)}")
            return []

    def _fetch_subscription_content(
        self, url: str, session: Optional[requests.Session] = None
    ) -> Optional[str]:
        """获取订阅内容"""
        try:
            if session:
                # 使用提供的会话（通常来自BaseCollector）
                response = session.get(url, timeout=self.timeout)
            else:
                # 创建带有合适头的会话
                import os
                import random

                # 多种真实的浏览器User-Agent
                real_user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
                ]

                temp_session = requests.Session()

                # 根据环境选择User-Agent
                if os.getenv("GITHUB_ACTIONS") == "true":
                    ua = random.choice(real_user_agents)
                else:
                    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

                temp_session.headers.update(
                    {
                        "User-Agent": ua,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
                        "Accept-Encoding": "gzip, deflate",
                        "Connection": "keep-alive",
                    }
                )
                temp_session.verify = False
                response = temp_session.get(url, timeout=self.timeout)

            response.raise_for_status()
            return response.text.strip()

        except requests.exceptions.Timeout as e:
            self.logger.error(f"获取订阅内容超时 {url}: {str(e)}")
            return None
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"获取订阅内容连接错误 {url}: {str(e)}")
            return None
        except requests.exceptions.ProxyError as e:
            self.logger.error(f"获取订阅内容代理错误 {url}: {str(e)}")
            return None
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"获取订阅内容HTTP错误 {url}: {e.response.status_code}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取订阅内容网络请求错误 {url}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"获取订阅内容失败 {url}: {str(e)}")
            return None

    def _parse_subscription_content(self, content: str) -> List[str]:
        """
        解析订阅内容，支持多种格式

        解析顺序：
        1. YAML/JSON格式（Clash配置）
        2. Base64编码
        3. URL解码
        4. 直接文本解析
        """
        nodes = []

        # 1. 尝试YAML/JSON格式解析
        if HAS_YAML:
            yaml_nodes = self._parse_yaml_json_content(content)
            if yaml_nodes:
                nodes.extend(yaml_nodes)
                return nodes  # YAML成功则直接返回

        # 2. 尝试Base64解码
        base64_nodes = self._parse_base64_content(content)
        if base64_nodes:
            self.logger.debug(f"Base64解码成功，提取到 {len(base64_nodes)} 个节点")
            return base64_nodes  # Base64成功则直接返回

        # 3. 尝试URL解码
        url_nodes = self._parse_url_decoded_content(content)
        if url_nodes:
            self.logger.debug(f"URL解码成功，提取到 {len(url_nodes)} 个节点")
            return url_nodes  # URL解码成功则直接返回

        # 4. 直接从文本提取节点
        direct_nodes = self._extract_nodes_from_text(content)
        nodes.extend(direct_nodes)

        # 去重并过滤
        unique_nodes = self._filter_and_deduplicate(nodes)

        return unique_nodes

    def _parse_yaml_json_content(self, content: str) -> List[str]:
        """解析YAML/JSON格式内容（Clash配置）"""
        if not HAS_YAML:
            return []

        try:
            # 检查内容是否可能是YAML/JSON格式
            stripped_content = content.strip()
            if not stripped_content:
                return []

            # 如果内容看起来像是纯文本（包含大量节点协议），跳过YAML解析
            node_count = len(
                re.findall(
                    r"(?:vmess|vless|trojan|ss|ssr|hysteria)://",
                    stripped_content,
                    re.IGNORECASE,
                )
            )
            if node_count > 5:  # 如果包含5个以上节点协议，认为这是纯文本
                return []

            # 检查是否可能是YAML格式（包含YAML特征）
            yaml_indicators = [":", "-", "{", "}", "[", "]"]
            has_yaml_features = any(
                indicator in stripped_content for indicator in yaml_indicators
            )

            if not has_yaml_features:
                # 不包含YAML特征，跳过解析
                return []

            # 尝试解析为YAML
            data = yaml.safe_load(stripped_content)

            # 处理Clash配置文件格式
            if isinstance(data, dict) and "proxies" in data:
                proxies_list = data["proxies"]
                if isinstance(proxies_list, list):
                    self.logger.debug(
                        f"识别为Clash配置格式，包含 {len(proxies_list)} 个代理"
                    )
                    return self._convert_clash_proxies_to_nodes(proxies_list)

            # 处理纯代理列表格式
            elif isinstance(data, list):
                self.logger.debug(f"识别为代理列表格式，包含 {len(data)} 个代理")
                return self._convert_clash_proxies_to_nodes(data)

            # 如果解析结果是字符串或其他不支持的类型，记录但不报错
            elif isinstance(data, str):
                self.logger.debug("YAML解析返回字符串，可能是其他格式的内容")
                return []
            else:
                self.logger.debug(f"YAML解析返回不支持的类型: {type(data)}")
                return []

        except Exception as e:
            self.logger.debug(f"YAML/JSON解析失败: {str(e)}")

        return []

    def _parse_base64_content(self, content: str) -> List[str]:
        """解析Base64编码的内容，支持单层和双层编码"""
        try:
            # 标准化Base64内容
            clean_content = content.strip()

            # 补齐padding
            padding_needed = (-len(clean_content)) % 4
            if padding_needed:
                clean_content += "=" * padding_needed

            # 解码
            decoded_bytes = base64.b64decode(clean_content)
            decoded_text = decoded_bytes.decode("utf-8", errors="ignore")

            # 从解码内容提取节点
            nodes = self._extract_nodes_from_text(decoded_text)
            if nodes:
                self.logger.debug(f"Base64解码成功，提取到 {len(nodes)} 个节点")
                return nodes

            # 尝试双重Base64解码（某些订阅使用双层编码）
            try:
                double_padding = (-len(decoded_bytes)) % 4
                if double_padding:
                    double_content = decoded_bytes + b"=" * double_padding
                else:
                    double_content = decoded_bytes
                double_decoded = base64.b64decode(double_content)
                double_text = double_decoded.decode("utf-8", errors="ignore")
                nodes = self._extract_nodes_from_text(double_text)
                if nodes:
                    self.logger.debug(f"双重Base64解码成功，提取到 {len(nodes)} 个节点")
                    return nodes
            except Exception:
                pass

        except Exception as e:
            self.logger.debug(f"Base64解码失败: {str(e)}")

        return []

    def _parse_url_decoded_content(self, content: str) -> List[str]:
        """解析URL编码的内容"""
        try:
            from urllib.parse import unquote

            decoded_content = unquote(content)
            if decoded_content != content:  # 确实发生了解码
                nodes = self._extract_nodes_from_text(decoded_content)
                if nodes:
                    self.logger.debug(f"URL解码成功，提取到 {len(nodes)} 个节点")
                    return nodes

        except Exception as e:
            self.logger.debug(f"URL解码失败: {str(e)}")

        return []

    def _extract_nodes_from_text(self, text: str) -> List[str]:
        """从文本中提取节点"""
        nodes = []

        for pattern in self.node_patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    node = match.strip()
                    if len(node) >= self.min_node_length:
                        nodes.append(node)
            except Exception as e:
                self.logger.debug(f"节点模式匹配失败: {pattern} - {str(e)}")

        return nodes

    def _convert_clash_proxies_to_nodes(
        self, proxies: List[Dict[str, Any]]
    ) -> List[str]:
        """将Clash代理配置转换为节点URI"""
        nodes = []

        for proxy in proxies:
            try:
                node = self.converter.convert(proxy)
                if node and len(node) >= self.min_node_length:
                    nodes.append(node)
            except Exception as e:
                self.logger.debug(f"Clash代理转换失败: {str(e)}")

        return nodes

    def _filter_and_deduplicate(self, nodes: List[str]) -> List[str]:
        """过滤和去重节点"""
        # 长度过滤
        filtered_nodes = [node for node in nodes if len(node) >= self.min_node_length]

        # 去重
        unique_nodes = list(set(filtered_nodes))

        return unique_nodes


# 全局单例实例
_subscription_parser = None


def get_subscription_parser() -> SubscriptionParser:
    """获取订阅解析器单例实例"""
    global _subscription_parser
    if _subscription_parser is None:
        _subscription_parser = SubscriptionParser()
    return _subscription_parser
