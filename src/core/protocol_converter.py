#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
协议转换器 - 共享的V2Ray节点协议转换模块

支持将 Clash 代理配置转换为各种 V2Ray 节点 URI 格式:
- vmess://
- vless://
- trojan://
- ss:// (Shadowsocks)
- ssr:// (ShadowsocksR)
- hysteria://
- hysteria2://
- socks5://
"""

import base64
import json
import re
from typing import Any, Dict, Optional
from urllib.parse import quote


class ProtocolConverter:
    """V2Ray 节点协议转换器"""

    def __init__(self, logger=None):
        """
        初始化协议转换器

        Args:
            logger: 可选的日志记录器实例
        """
        self.logger = logger

    def _log_debug(self, message: str):
        """输出调试日志"""
        if self.logger:
            self.logger.debug(message)

    def _log_warning(self, message: str):
        """输出警告日志"""
        if self.logger:
            self.logger.warning(message)

    def convert(self, proxy: Dict[str, Any]) -> Optional[str]:
        """
        将 Clash proxy 对象转换为 V2Ray 节点 URI 格式

        Args:
            proxy: Clash 代理配置字典

        Returns:
            节点 URI 字符串，失败时返回 None
        """
        try:
            proxy_type = proxy.get("type", "").lower()

            if proxy_type == "vless":
                return self._convert_vless(proxy)
            elif proxy_type == "vmess":
                return self._convert_vmess(proxy)
            elif proxy_type == "trojan":
                return self._convert_trojan(proxy)
            elif proxy_type == "ss":
                return self._convert_ss(proxy)
            elif proxy_type in ["hysteria", "hysteria2"]:
                return self._convert_hysteria(proxy)
            elif proxy_type == "ssr":
                return self._convert_ssr(proxy)
            elif proxy_type == "socks5":
                return self._convert_socks5(proxy)
            elif proxy_type == "reality":
                return self._convert_reality(proxy)
            else:
                self._log_debug(f"不支持的代理类型: {proxy_type}")
                return None

        except Exception as e:
            self._log_warning(f"代理转换失败: {str(e)}")
            return None

    def _convert_vless(self, proxy: Dict[str, Any]) -> Optional[str]:
        """转换 VLESS 配置为 URI"""
        try:
            server = proxy.get("server", "")
            port = proxy.get("port", "")
            uuid = proxy.get("uuid", "")
            name = proxy.get("name", "")
            tls = proxy.get("tls", False)
            servername = proxy.get("servername", "")
            network = proxy.get("network", "tcp")
            security = proxy.get("security", "")
            encryption = proxy.get("encryption", "none")
            client_fingerprint = proxy.get("client-fingerprint", "")

            # 构建 URI
            uri = f"vless://{uuid}@{server}:{port}"

            # 构建查询参数
            params = []
            if network:
                params.append(f"type={network}")
            if security:
                params.append(f"security={security}")
            if encryption:
                params.append(f"encryption={encryption}")
            if tls:
                params.append("security=tls")
            if servername:
                params.append(f"sni={servername}")
            if client_fingerprint:
                params.append(f"fp={client_fingerprint}")

            # WebSocket / gRPC 参数
            if network == "ws":
                ws_opts = proxy.get("ws-opts", {})
                if ws_opts:
                    headers = ws_opts.get("headers", {})
                    host = headers.get("Host", "")
                    if host:
                        params.append(f"host={host}")
                    path = ws_opts.get("path", "")
                    if path:
                        params.append(f"path={path}")
            elif network == "grpc":
                grpc_opts = proxy.get("grpc-opts", {})
                if grpc_opts:
                    service_name = grpc_opts.get("grpc-service-name", "")
                    if service_name:
                        params.append(f"serviceName={service_name}")

            if params:
                uri += "?" + "&".join(params)

            if name:
                uri += f"#{name}"

            return uri

        except Exception as e:
            self._log_warning(f"VLESS 转换失败: {str(e)}")
            return None

    def _convert_vmess(self, proxy: Dict[str, Any]) -> Optional[str]:
        """转换 VMess 配置为 URI（Base64 编码）"""
        try:
            vmess_config = {
                "v": "2",
                "ps": proxy.get("name", ""),
                "add": proxy.get("server", ""),
                "port": str(proxy.get("port", "")),
                "id": proxy.get("uuid", proxy.get("id", "")),
                "aid": proxy.get("alterId", 0),
                "net": proxy.get("network", "tcp"),
                "type": proxy.get("cipher", "auto"),
                "host": proxy.get("servername", ""),
                "path": proxy.get("path", ""),
                "tls": "tls" if proxy.get("tls") else "",
            }

            config_json = json.dumps(vmess_config, separators=(",", ":"))
            config_b64 = base64.b64encode(config_json.encode()).decode()

            uri = f"vmess://{config_b64}"

            name = proxy.get("name", "")
            if name:
                uri += f"#{name}"

            return uri

        except Exception as e:
            self._log_warning(f"VMess 转换失败: {str(e)}")
            return None

    def _convert_trojan(self, proxy: Dict[str, Any]) -> Optional[str]:
        """转换 Trojan 配置为 URI"""
        try:
            server = proxy.get("server", "")
            port = proxy.get("port", "")
            password = proxy.get("password", "")
            name = proxy.get("name", "")
            sni = proxy.get("sni", proxy.get("servername", ""))
            skip_verify = proxy.get("skip-cert-verify", False)

            if not all([server, port, password]):
                return None

            uri = f"trojan://{password}@{server}:{port}"

            params = []
            if sni:
                params.append(f"sni={sni}")
            if skip_verify:
                params.append("allowInsecure=1")

            # WebSocket 支持
            network = proxy.get("network", "tcp")
            if network == "ws":
                ws_opts = proxy.get("ws-opts", {})
                if ws_opts:
                    headers = ws_opts.get("headers", {})
                    host = headers.get("Host", "")
                    if host:
                        params.append(f"host={host}")
                    path = ws_opts.get("path", "")
                    if path:
                        params.append(f"path={path}")

            if params:
                uri += "?" + "&".join(params)

            if name:
                uri += f"#{name}"

            return uri

        except Exception as e:
            self._log_warning(f"Trojan 转换失败: {str(e)}")
            return None

    def _convert_ss(self, proxy: Dict[str, Any]) -> Optional[str]:
        """转换 Shadowsocks 配置为 URI"""
        try:
            server = proxy.get("server", "")
            port = proxy.get("port", "")
            password = proxy.get("password", "")
            method = proxy.get("cipher", proxy.get("method", "aes-256-gcm"))
            plugin = proxy.get("plugin", "")
            plugin_opts = proxy.get("plugin-opts", "")
            name = proxy.get("name", "")

            if not all([server, port, method, password]):
                return None

            # 构建 userinfo: method:password
            userinfo = f"{method}:{password}"
            userinfo_b64 = base64.b64encode(userinfo.encode()).decode()

            uri = f"ss://{userinfo_b64}@{server}:{port}"

            # 添加插件参数
            if plugin:
                params = f"plugin={plugin}"
                if plugin_opts:
                    if isinstance(plugin_opts, dict):
                        opts_list = []
                        for key, value in plugin_opts.items():
                            opts_list.append(f"{key}={value}")
                        params += ";" + ";".join(opts_list)
                    else:
                        params += f";{plugin_opts}"
                uri += f"?{params}"

            if name:
                uri += f"#{name}"

            return uri

        except Exception as e:
            self._log_warning(f"Shadowsocks 转换失败: {str(e)}")
            return None

    def _convert_ssr(self, proxy: Dict[str, Any]) -> Optional[str]:
        """转换 ShadowsocksR 配置为 URI"""
        try:
            server = proxy.get("server", "")
            port = proxy.get("port", "")
            password = proxy.get("password", "")
            method = proxy.get("cipher", "aes-256-cfb")
            protocol = proxy.get("protocol", "origin")
            obfs = proxy.get("obfs", "plain")
            name = proxy.get("name", "")

            if not all([server, port, password]):
                return None

            # SSR 格式: ssr://server:port:protocol:method:obfs:base64(password)/?params
            uri = f"ssr://{server}:{port}:{protocol}:{method}:{obfs}:{base64.b64encode(password.encode()).decode()}"

            params = []
            # 插件/混淆参数
            if obfs and obfs != "plain":
                obfs_param = proxy.get("obfs-param", "")
                if obfs_param:
                    params.append(
                        f"obfsparam={base64.b64encode(obfs_param.encode()).decode()}"
                    )

            protocol_param = proxy.get("protocol-param", "")
            if protocol_param:
                params.append(
                    f"protoparam={base64.b64encode(protocol_param.encode()).decode()}"
                )

            remarks = proxy.get("remarks", "")
            if remarks:
                params.append(f"remarks={base64.b64encode(remarks.encode()).decode()}")

            network = proxy.get("network", "tcp")
            if network != "tcp":
                params.append(f"network={network}")

            if params:
                uri += "?" + "&".join(params)

            if name:
                uri += f"#{name}"

            return uri

        except Exception as e:
            self._log_warning(f"ShadowsocksR 转换失败: {str(e)}")
            return None

    def _convert_hysteria(self, proxy: Dict[str, Any]) -> Optional[str]:
        """转换 Hysteria/Hysteria2 配置为 URI"""
        try:
            server = proxy.get("server", "")
            port = proxy.get("port", "")
            password = proxy.get("password", proxy.get("auth", ""))
            name = proxy.get("name", "")
            protocol_type = proxy.get("type", "hysteria")
            sni = proxy.get("sni", proxy.get("servername", ""))
            insecure = proxy.get("skip-cert-verify", False)

            if not all([server, port]):
                return None

            # URL encode password
            password_encoded = quote(password, safe="")

            if protocol_type == "hysteria2":
                uri = f"hysteria2://{password_encoded}@{server}:{port}"
            else:
                uri = f"hysteria://{password_encoded}@{server}:{port}"

            params = []
            if sni:
                params.append(f"sni={sni}")
            if insecure:
                params.append("insecure=1")

            # Hysteria2 额外参数
            if protocol_type == "hysteria2":
                # 暴力模式和倍数
                upload = proxy.get("upload", "")
                download = proxy.get("download", "")
                if upload:
                    params.append(f"upload={upload}")
                if download:
                    params.append(f"download={download}")

            # Hysteria v1 参数
            protocol = proxy.get("protocol", "udp")
            if protocol != "udp":
                params.append(f"protocol={protocol}")

            obfs = proxy.get("obfs", "")
            if obfs:
                params.append(f"obfs={obfs}")

            if params:
                uri += "?" + "&".join(params)

            if name:
                uri += f"#{name}"

            return uri

        except Exception as e:
            self._log_warning(f"Hysteria 转换失败: {str(e)}")
            return None

    def _convert_socks5(self, proxy: Dict[str, Any]) -> Optional[str]:
        """转换 SOCKS5 配置为 URI"""
        try:
            server = proxy.get("server", "")
            port = proxy.get("port", "")
            username = proxy.get("username", "")
            password = proxy.get("password", "")
            name = proxy.get("name", "")

            if not all([server, port]):
                return None

            if username and password:
                auth_b64 = base64.b64encode(f"{username}:{password}".encode()).decode()
                uri = f"socks5://{auth_b64}@{server}:{port}"
            else:
                uri = f"socks5://{server}:{port}"

            if name:
                uri += f"#{name}"

            return uri

        except Exception as e:
            self._log_warning(f"SOCKS5 转换失败: {str(e)}")
            return None

    def _convert_reality(self, proxy: Dict[str, Any]) -> Optional[str]:
        """转换 Reality 配置为 URI"""
        try:
            server = proxy.get("server", "")
            port = proxy.get("port", "")
            uuid = proxy.get("uuid", "")
            name = proxy.get("name", "")
            sni = proxy.get("sni", proxy.get("servername", ""))
            short_id = proxy.get("short-id", "")
            fingerprint = proxy.get("fp", proxy.get("client-fingerprint", ""))

            if not all([server, port, uuid, sni, short_id]):
                return None

            uri = f"vless://{uuid}@{server}:{port}"

            params = [
                "security=reality",
                f"type=tcp",
                f"sni={sni}",
                f"pbk=",
                f"sid={short_id}",
            ]

            if fingerprint:
                params.append(f"fp={fingerprint}")

            uri += "?" + "&".join(params)

            if name:
                uri += f"#{name}"

            return uri

        except Exception as e:
            self._log_warning(f"Reality 转换失败: {str(e)}")
            return None


# 便捷函数：从文本中提取节点
def extract_nodes_from_text(text: str, min_length: int = 20) -> list:
    """
    从文本中提取节点 URI

    Args:
        text: 源文本
        min_length: 最小节点长度

    Returns:
        节点 URI 列表
    """
    patterns = [
        r"(vmess://[^\s\n\r]+)",
        r"(vless://[^\s\n\r]+)",
        r"(trojan://[^\s\n\r]+)",
        r"(ss://[^\s\n\r]+)",
        r"(ssr://[^\s\n\r]+)",
        r"(hysteria2://[^\s\n\r]+)",
        r"(hysteria://[^\s\n\r]+)",
        r"(socks5://[^\s\n\r]+)",
        r"(reality://[^\s\n\r]+)",
    ]

    nodes = []
    for pattern in patterns:
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                node = match.strip()
                if len(node) >= min_length:
                    nodes.append(node)
        except Exception:
            continue

    return nodes


# 全局单例实例
_converter = None


def get_converter(logger=None) -> ProtocolConverter:
    """获取协议转换器单例实例"""
    global _converter
    if _converter is None:
        _converter = ProtocolConverter(logger)
    return _converter
