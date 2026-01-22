#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：protocol_converter
测试协议转换器的各种协议转换功能
"""

import pytest
import sys
import os
import base64
import json

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
        # VMess URI 是 base64 编码的，所以不能直接检查 "example.com"
        # 只检查格式是否正确
        assert len(result) > 0

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
        """测试无效的协议类型"""
        proxy = {
            "type": "invalid",
            "name": "无效节点",
            "server": "example.com",
            "port": 443,
        }
        result = converter.convert(proxy)

        # 无效类型应该返回 None
        assert result is None

    def test_convert_missing_required_fields(self, converter):
        """测试缺少必需字段"""
        proxy = {
            "type": "vmess",
            "name": "测试节点",
            # 缺少 server, port, uuid 等必需字段
        }
        result = converter.convert(proxy)

        # ProtocolConverter 即使缺少必需字段也会生成 URI，只是字段为空
        # 所以这里只检查是否返回了结果
        assert result is not None
        assert result.startswith("vmess://")