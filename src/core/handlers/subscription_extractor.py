#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订阅提取器 - 提取订阅链接和节点
"""

import re
import base64
from urllib.parse import unquote
from typing import List, Dict, Any


class SubscriptionExtractor:
    """订阅提取器"""

    def __init__(self, logger, site_config, converter, min_node_length=20):
        """
        初始化订阅提取器

        Args:
            logger: 日志记录器
            site_config: 网站配置
            converter: 协议转换器
            min_node_length: 最小节点长度
        """
        self.logger = logger
        self.site_config = site_config
        self.converter = converter
        self.min_node_length = min_node_length

    def find_subscription_links(self, content: str) -> List[str]:
        """
        查找订阅链接

        Args:
            content: 页面内容

        Returns:
            订阅链接列表
        """
        from src.config.websites import SUBSCRIPTION_PATTERNS, SUBSCRIPTION_KEYWORDS

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
            except Exception:
                self.logger.debug(f"SUBSCRIPTION_KEYWORDS模式匹配失败: {keyword}")

        # 清理和去重
        cleaned_links = []
        seen = set()

        for link in links:
            # 先从原始链接中提取所有独立的.txt URL（避免先清理导致URL合并）
            url_matches = re.findall(r'https?://[^<\s"]+(?:\.(?:txt|TXT))', link)

            for url_match in url_matches:
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

    def extract_nodes_from_text(self, text: str) -> List[str]:
        """
        从文本中提取节点

        Args:
            text: 文本内容

        Returns:
            节点列表
        """
        from src.config.websites import NODE_PATTERNS

        nodes = []
        for pattern in NODE_PATTERNS:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    node = match.strip()
                    if node and len(node) >= self.min_node_length:
                        nodes.append(node)
            except Exception as e:
                self.logger.warning(f"节点模式匹配失败: {pattern} - {str(e)}")
        return nodes

    def parse_subscription_content(self, content: str) -> List[str]:
        """
        解析订阅内容，支持多种编码格式

        Args:
            content: 订阅内容

        Returns:
            节点列表
        """
        # 检查内容是否为空
        if not content:
            self.logger.warning("订阅链接返回空内容")
            return []

        if len(content) < 10:  # 太短不可能是有效节点
            self.logger.warning(f"订阅链接内容过短 ({len(content)} 字符)")
            return []

        # 尝试多种解析方式
        all_nodes = []

        # 方式1: 直接从原始内容提取
        nodes = self.extract_nodes_from_text(content)
        if nodes:
            self.logger.info(f"直接解析获取到 {len(nodes)} 个节点")
            all_nodes.extend(nodes)

        # 方式2: 尝试Base64解码
        try:
            # 补齐base64 padding
            padded_content = content + "=" * (-len(content) % 4)
            decoded_content = base64.b64decode(padded_content).decode(
                "utf-8", errors="ignore"
            )
            nodes = self.extract_nodes_from_text(decoded_content)
            if nodes:
                self.logger.info(f"Base64解码后获取到 {len(nodes)} 个节点")
                all_nodes.extend(nodes)
            else:
                # 尝试双重Base64解码（某些订阅链接使用双重编码）
                try:
                    decoded_bytes = base64.b64decode(padded_content)
                    double_padded = decoded_bytes + b"=" * (-len(decoded_bytes) % 4)
                    double_decoded = base64.b64decode(double_padded).decode(
                        "utf-8", errors="ignore"
                    )
                    nodes = self.extract_nodes_from_text(double_decoded)
                    if nodes:
                        self.logger.info(f"双重Base64解码后获取到 {len(nodes)} 个节点")
                        all_nodes.extend(nodes)
                except Exception:
                    pass
        except Exception as e:
            self.logger.debug(f"Base64解码失败: {str(e)}")

        # 方式3: 尝试URL解码
        try:
            url_decoded = unquote(content)
            if url_decoded != content:  # 确实发生了解码
                nodes = self.extract_nodes_from_text(url_decoded)
                if nodes:
                    self.logger.info(f"URL解码后获取到 {len(nodes)} 个节点")
                    all_nodes.extend(nodes)
        except Exception as e:
            self.logger.debug(f"URL解码失败: {str(e)}")

        # 方式4: 逐行分割后提取（处理某些特殊格式）
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue

            # 尝试从单行提取节点
            nodes = self.extract_nodes_from_text(line)
            all_nodes.extend(nodes)

            # 尝试Base64解码单行
            try:
                padded_line = line + "=" * (-len(line) % 4)
                decoded_line = base64.b64decode(padded_line).decode(
                    "utf-8", errors="ignore"
                )
                nodes = self.extract_nodes_from_text(decoded_line)
                all_nodes.extend(nodes)

                # 尝试双重Base64解码
                try:
                    decoded_bytes = base64.b64decode(padded_line)
                    double_padded = decoded_bytes + b"=" * (-len(decoded_bytes) % 4)
                    double_decoded = base64.b64decode(double_padded).decode(
                        "utf-8", errors="ignore"
                    )
                    nodes = self.extract_nodes_from_text(double_decoded)
                    all_nodes.extend(nodes)
                except Exception:
                    pass
            except Exception:
                pass

        # 方式5: 尝试解析 YAML/JSON 格式（Clash配置）
        yaml_nodes = self._extract_yaml_json_nodes(content)
        if yaml_nodes:
            self.logger.info(f"YAML/JSON格式解析获取到 {len(yaml_nodes)} 个节点")
            all_nodes.extend(yaml_nodes)

        # 去重
        unique_nodes = list(set(all_nodes))

        # 过滤长度
        unique_nodes = [
            node for node in unique_nodes if len(node) >= self.min_node_length
        ]

        self.logger.info(
            f"从订阅链接获取到 {len(unique_nodes)} 个节点 (原始: {len(all_nodes)})"
        )
        return unique_nodes

    def _extract_yaml_json_nodes(self, content: str) -> List[str]:
        """
        从 YAML/JSON 格式提取节点（Clash配置格式）

        Args:
            content: YAML/JSON内容

        Returns:
            节点列表
        """
        nodes = []
        try:
            import json
            import yaml

            # 首先尝试作为完整JSON解析
            try:
                data = json.loads(content.strip())
                proxies_list = None

                if isinstance(data, list):
                    # JSON数组格式
                    proxies_list = data
                    self.logger.info(
                        f"识别为JSON数组格式，包含 {len(proxies_list)} 个代理"
                    )
                elif isinstance(data, dict):
                    # JSON对象格式
                    if "proxies" in data:
                        proxies_list = data["proxies"]
                        self.logger.info(
                            f"识别为JSON对象格式，包含 {len(proxies_list)} 个代理"
                        )

                if proxies_list:
                    for proxy in proxies_list:
                        try:
                            node = self.converter.convert(proxy)
                            if node and len(node) >= self.min_node_length:
                                nodes.append(node)
                        except Exception as e:
                            self.logger.debug(f"JSON代理转换失败: {str(e)}")
                    return nodes

            except json.JSONDecodeError:
                # 不是JSON格式，尝试YAML
                pass

            # 尝试作为YAML解析
            try:
                self.logger.info("开始尝试YAML解析...")
                yaml_data = yaml.safe_load(content.strip())
                self.logger.info(f"YAML解析成功，数据类型: {type(yaml_data)}")

                # 处理Clash配置文件格式（包含proxies字段的完整配置）
                if isinstance(yaml_data, dict) and "proxies" in yaml_data:
                    proxies_list = yaml_data["proxies"]
                    self.logger.info(
                        f"识别为Clash配置格式，包含 {len(proxies_list)} 个代理"
                    )

                    for i, proxy in enumerate(proxies_list):
                        try:
                            node = self.converter.convert(proxy)
                            self.logger.debug(
                                f"YAML代理 {i + 1} 转换结果长度: {len(node) if node else 0}"
                            )
                            if node and len(node) >= self.min_node_length:
                                nodes.append(node)
                            else:
                                self.logger.warning(
                                    f"YAML代理 {i + 1} 转换结果太短或为空"
                                )
                        except Exception as e:
                            self.logger.warning(f"YAML代理 {i + 1} 转换失败: {str(e)}")
                    self.logger.info(f"YAML解析完成，共转换 {len(nodes)} 个节点")
                    return nodes

                # 处理只有代理列表的格式（兼容旧格式）
                elif isinstance(yaml_data, list):
                    self.logger.info(
                        f"识别为代理列表格式，包含 {len(yaml_data)} 个代理"
                    )
                    for i, proxy in enumerate(yaml_data):
                        try:
                            node = self.converter.convert(proxy)
                            if node and len(node) >= self.min_node_length:
                                nodes.append(node)
                        except Exception as e:
                            self.logger.warning(f"YAML代理 {i + 1} 转换失败: {str(e)}")
                    self.logger.info(f"YAML解析完成，共转换 {len(nodes)} 个节点")
                    return nodes
                else:
                    self.logger.info(f"YAML数据格式不支持: {type(yaml_data)}")

            except Exception as e:
                # YAML解析失败，回退到行内JSON解析
                pass

            # 回退方案：从文本中提取行内JSON对象
            if "proxies:" in content or "proxies" in content:
                lines = content.split("\n")
                json_objects = []

                for line in lines:
                    line = line.strip()
                    # 查找行内的 JSON 对象（支持嵌套）
                    json_matches = re.findall(r"-\s*(\{[^}]*\{[^}]*\}[^}]*\})", line)
                    if not json_matches:
                        json_match = re.search(r"-\s*(\{.+\})", line)
                        if json_match:
                            json_matches.append(json_match.group(1))

                    for json_str in json_matches:
                        json_objects.append(json_str)

                self.logger.info(f"从YAML文本中找到 {len(json_objects)} 个行内JSON对象")

                success_count = 0
                error_count = 0

                for json_str in json_objects:
                    try:
                        proxy = json.loads(json_str)
                        node = self.converter.convert(proxy)
                        if node and len(node) >= self.min_node_length:
                            nodes.append(node)
                            success_count += 1
                        else:
                            error_count += 1
                    except json.JSONDecodeError as e:
                        error_count += 1
                        if error_count <= 3:  # 只显示前3个错误
                            self.logger.warning(f"行内JSON解析失败: {str(e)[:100]}")
                    except Exception as e:
                        error_count += 1

                self.logger.info(
                    f"YAML行内JSON解析完成: {success_count} 成功, {error_count} 失败"
                )

        except ImportError as e:
            self.logger.warning(f"模块导入失败: {str(e)}")
        except Exception as e:
            self.logger.warning(f"YAML/JSON 解析失败: {str(e)}")

        return nodes

    def _clean_link(self, link: str) -> str:
        """
        清理链接

        Args:
            link: 原始链接

        Returns:
            清理后的链接
        """
        if not link:
            return ""

        clean_link = link.strip()

        # 移除HTML实体编码
        clean_link = (
            clean_link.replace("%3C", "").replace("%3E", "").replace("%20", " ")
        )
        clean_link = (
            clean_link.replace("&lt;", "").replace("&gt;", "").replace("&nbsp;", " ")
        )

        # 处理常见的错误链接格式（只在末尾匹配）
        for suffix in ["/strong", "/span", "/pp", "/h3", "&nbsp;", "/div", "div", "/p"]:
            if clean_link.endswith(suffix):
                clean_link = clean_link[: -len(suffix)]

        # 移除末尾的HTML标签（包括完整标签如</p>、</div>等）
        clean_link = re.sub(r"<[^>]+>$", "", clean_link)
        # 移除末尾的无效字符
        clean_link = re.sub(r'[<>"]+$', "", clean_link)
        clean_link = clean_link.rstrip(";/")

        # 确保只返回有效的URL
        if not clean_link.startswith("http"):
            return ""

        # 验证URL格式
        if not re.match(r"^https?://[^\s/$.?#][^\s]*$", clean_link):
            return ""

        return clean_link.strip()

    def _is_valid_url(self, url: str) -> bool:
        """
        验证URL是否有效

        Args:
            url: URL字符串

        Returns:
            是否有效
        """
        try:
            url_pattern = re.compile(
                r"^https?://"
                r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
                r"localhost|"
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                r"(?::\d+)?"
                r"(?:/?|[/?]\S+)$",
                re.IGNORECASE,
            )
            return url_pattern.match(url) is not None
        except Exception as e:
            self.logger.debug(f"URL验证失败: {str(e)}")
            return False

    def _is_valid_subscription_link(self, url: str) -> bool:
        """
        验证是否为有效的V2Ray订阅链接

        Args:
            url: URL字符串

        Returns:
            是否有效
        """
        try:
            # 导入排除模式
            from src.config.websites import EXCLUDED_SUBSCRIPTION_PATTERNS

            # 检查是否匹配排除模式
            for pattern in EXCLUDED_SUBSCRIPTION_PATTERNS:
                if re.match(pattern, url, re.IGNORECASE):
                    self.logger.debug(f"链接被排除规则过滤: {url}")
                    return False

            # 必须以订阅文件扩展名结尾，排除网页文件
            valid_extensions = [".txt", ".yaml", ".yml", ".json", ".sub"]
            web_extensions = [".htm", ".html", ".php", ".asp", ".jsp"]

            url_lower = url.lower()
            has_valid_ext = any(url_lower.endswith(ext) for ext in valid_extensions)
            has_web_ext = any(url_lower.endswith(ext) for ext in web_extensions)

            if not has_valid_ext or has_web_ext:
                return False

            # 对于.yaml/.yml/.json文件，更宽松的验证（因为这些通常是结构化配置文件）
            if url_lower.endswith((".yaml", ".yml", ".json")):
                return True

            from urllib.parse import urlparse

            parsed = urlparse(url)
            path_part = parsed.path.lower()

            # 首先排除明显的非V2Ray文件（基于文件名模式，只检查路径部分）
            non_v2ray_patterns = [
                r".*/[^/]*clash[^/]*\.txt$",  # 排除clash相关的txt文件
                r".*/[^/]*sing.*box[^/]*\.txt$",  # 排除sing-box相关的txt文件
                r".*/[^/]*config[^/]*\.txt$",  # 排除config相关的txt文件
            ]

            for pattern in non_v2ray_patterns:
                if re.match(pattern, url, re.IGNORECASE):
                    return False

            # 检查URL路径中是否包含V2Ray相关关键词
            v2ray_keywords = [
                "v2ray",
                "sub",
                "subscribe",
                "node",
                "link",
                "vmess",
                "vless",
                "trojan",
            ]
            has_keyword = any(keyword in path_part for keyword in v2ray_keywords)

            # 如果路径中没有关键词，检查域名
            if not has_keyword:
                domain = parsed.netloc.lower()
                domain_keywords = ["v2ray", "node", "sub", "vmess", "vless", "trojan"]
                has_domain_keyword = any(
                    keyword in domain for keyword in domain_keywords
                )

                # 如果域名也没有关键词，则检查是否为常见的节点服务域名模式
                if not has_domain_keyword:
                    # 常见的节点服务域名模式
                    common_patterns = [
                        r".*\.mibei77\.com",
                        r".*\.freeclashnode\.com",
                        r".*node\..*",
                        r".*sub\..*",
                        r".*api\..*",
                        r".*\..*\.txt$",  # 任何包含数字和字母的.txt文件
                    ]

                    for pattern in common_patterns:
                        if re.match(pattern, url, re.IGNORECASE):
                            return True

                    # 如果都不匹配，则认为不是V2Ray订阅
                    return False

            # 排除明显的内容转换网站
            excluded_domains = [
                "subconverter",
                "subx",
                "sub.xeton",
                "api.v1.mk",
                "v1.mk",
                "raw.git",
                "githubusercontent.com",
                "gitlab.com",
            ]
            for domain in excluded_domains:
                if domain in parsed.netloc.lower():
                    return False

            return True

        except Exception as e:
            self.logger.warning(f"验证订阅链接时出错: {url} - {str(e)}")
            return False