#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：protocol_converter
测试协议转换器的各种协议转换功能
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.protocol_converter import ProtocolConverter, extract_nodes_from_text


class TestProtocolConverter:
    """协议转换器测试"""

    @pytest.fixture
    def converter(self):
        """创建协议转换器实例"""
        return ProtocolConverter()

    def test_convert_vmess(self, converter):
        """测试 VMess 协议转换"""
        proxy = {
            "type": "vmess",
            "name": "测试节点",
            "server": "example.com",
            "port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "alterId": 0,
            "cipher": "auto",
            "network": "tcp",
            "tls": True,
        }
        result = converter.convert(proxy)

        assert result is not None
        assert result.startswith("vmess://")
        assert "example.com" in result
        assert "测试节点" in result

    def test_convert_vless(self, converter):
        """测试 VLESS 协议转换"""
        proxy = {
            "type": "vless",
            "name": "VLESS节点",
            "server": "example.com",
            "port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "network": "ws",
            "tls": True,
            "security": "tls",
        }
        result = converter.convert(proxy)

        assert result is not None
        assert result.startswith("vless://")
        assert "example.com" in result
        assert "VLESS节点" in result

    def test_convert_trojan(self, converter):
        """测试 Trojan 协议转换"""
        proxy = {
            "type": "trojan",
            "name": "Trojan节点",
            "server": "example.com",
            "port": 443,
            "password": "test_password",
            "sni": "example.com",
        }
        result = converter.convert(proxy)

        assert result is not None
        assert result.startswith("trojan://")
        assert "example.com" in result
        assert "Trojan节点" in result

    def test_convert_ss(self, converter):
        """测试 Shadowsocks 协议转换"""
        proxy = {
            "type": "ss",
            "name": "SS节点",
            "server": "example.com",
            "port": 8388,
            "cipher": "aes-256-gcm",
            "password": "test_password",
        }
        result = converter.convert(proxy)

        assert result is not None
        assert result.startswith("ss://")
        assert "example.com" in result
        assert "SS节点" in result

    def test_convert_ssr(self, converter):
        """测试 ShadowsocksR 协议转换"""
        proxy = {
            "type": "ssr",
            "name": "SSR节点",
            "server": "example.com",
            "port": 8388,
            "protocol": "origin",
            "cipher": "aes-256-cfb",
            "password": "test_password",
            "obfs": "plain",
        }
        result = converter.convert(proxy)

        assert result is not None
        assert result.startswith("ssr://")
        assert "example.com" in result
        assert "SSR节点" in result

    def test_convert_hysteria2(self, converter):
        """测试 Hysteria2 协议转换"""
        proxy = {
            "type": "hysteria2",
            "name": "Hysteria2节点",
            "server": "example.com",
            "port": 443,
            "password": "test_password",
            "sni": "example.com",
        }
        result = converter.convert(proxy)

        assert result is not None
        assert result.startswith("hysteria2://")
        assert "example.com" in result
        assert "Hysteria2节点" in result

    def test_convert_invalid_type(self, converter):
        """测试无效协议类型"""
        proxy = {
            "type": "invalid",
            "name": "无效节点",
            "server": "example.com",
            "port": 443,
        }
        result = converter.convert(proxy)

        assert result is None

    def test_convert_missing_required_fields(self, converter):
        """测试缺少必需字段"""
        proxy = {
            "type": "vmess",
            "name": "测试节点",
            # 缺少 server, port, uuid
        }
        result = converter.convert(proxy)

        assert result is None


class TestExtractNodesFromText:
    """从文本提取节点测试"""

    def test_extract_vmess_nodes(self):
        """测试提取 VMess 节点"""
        text = """
        vmess://eyJ2IjoiMiIsInBzIjoidGVzdCIsImFkZCI6ImV4YW1wbGUuY29tIiwicG9ydCI6IjQ0MyIsImlkIjoiMTIzNDU2NzgifQ==
        vless://uuid@example.com:443?security=tls#test
        """
        nodes = extract_nodes_from_text(text)

        assert len(nodes) == 2
        assert all(node.startswith(("vmess://", "vless://")) for node in nodes)

    def test_extract_mixed_protocols(self):
        """测试提取混合协议节点"""
        text = """
        vmess://eyJ2IjoiMiJ9
        vless://uuid@example.com:443
        trojan://password@example.com:443
        ss://Y2lwaGVyOnRlc3RAZXhhbXBsZS5jb206ODM4OA==
        """
        nodes = extract_nodes_from_text(text)

        assert len(nodes) == 4
        assert all(node.startswith(("vmess://", "vless://", "trojan://", "ss://")) for node in nodes)

    def test_extract_empty_text(self):
        """测试空文本"""
        text = ""
        nodes = extract_nodes_from_text(text)

        assert len(nodes) == 0

    def test_extract_invalid_text(self):
        """测试无效文本"""
        text = "这不是节点内容"
        nodes = extract_nodes_from_text(text)

        assert len(nodes) == 0

    def test_extract_nodes_with_html_tags(self):
        """测试包含HTML标签的文本"""
        text = """
        <div>
            vmess://eyJ2IjoiMiJ9
        </div>
        <p>vless://uuid@example.com:443</p>
        """
        nodes = extract_nodes_from_text(text)

        assert len(nodes) == 2
        assert all(node.startswith(("vmess://", "vless://")) for node in nodes)

    def test_extract_duplicate_nodes(self):
        """测试去重功能"""
        text = """
        vmess://eyJ2IjoiMiJ9
        vmess://eyJ2IjoiMiJ9
        vless://uuid@example.com:443
        """
        nodes = extract_nodes_from_text(text)

        # 应该去重
        assert len(nodes) == 2

    def test_extract_nodes_with_whitespace(self):
        """测试包含空格的文本"""
        text = """
        vmess://eyJ2IjoiMiJ9  
        vless://uuid@example.com:443  
        """
        nodes = extract_nodes_from_text(text)

        assert len(nodes) == 2
        assert all(node.strip() == node for node in nodes)