#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：subscription_parser
测试订阅解析器的各种解析功能
"""

import pytest
import sys
import os
import base64
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.subscription_parser import SubscriptionParser
from src.core.exceptions import SubscriptionParseError


class TestSubscriptionParser:
    """订阅解析器测试"""

    @pytest.fixture
    def parser(self):
        """创建订阅解析器实例"""
        return SubscriptionParser()

    @pytest.fixture
    def mock_session(self):
        """创建模拟的 requests.Session"""
        session = Mock()
        return session

    def test_parse_vmess_subscription(self, parser, mock_session):
        """测试解析 VMess 订阅"""
        # 创建模拟响应
        mock_response = Mock()
        vmess_config = {
            "v": "2",
            "ps": "测试节点",
            "add": "example.com",
            "port": 443,
            "id": "12345678-1234-1234-1234-123456789abc",
            "aid": 0,
            "net": "tcp",
            "type": "none",
            "host": "example.com",
            "path": "",
            "tls": True,
        }
        vmess_json = str(vmess_config).replace("'", '"')
        vmess_base64 = base64.b64encode(vmess_json.encode()).decode()

        mock_response.text = vmess_base64
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        assert len(nodes) > 0
        assert all(node.startswith("vmess://") for node in nodes)

    def test_parse_base64_subscription(self, parser, mock_session):
        """测试解析 Base64 编码的订阅"""
        # 创建模拟响应
        mock_response = Mock()
        vmess_nodes = "vmess://eyJ2IjoiMiJ9\nvless://uuid@example.com:443"
        mock_response.text = base64.b64encode(vmess_nodes.encode()).decode()
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        assert len(nodes) == 2
        assert "vmess://" in nodes
        assert "vless://" in nodes

    def test_parse_yaml_subscription(self, parser, mock_session):
        """测试解析 YAML 格式的订阅（Clash配置）"""
        # 创建模拟响应
        mock_response = Mock()
        yaml_content = """
proxies:
  - {name: "节点1", type: vmess, server: example1.com, port: 443, uuid: uuid1, alterId: 0, cipher: auto}
  - {name: "节点2", type: vless, server: example2.com, port: 443, uuid: uuid2, network: ws, tls: true}
"""
        mock_response.text = yaml_content
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        assert len(nodes) == 2
        assert all(node.startswith(("vmess://", "vless://")) for node in nodes)

    def test_parse_empty_subscription(self, parser, mock_session):
        """测试解析空订阅"""
        # 创建模拟响应
        mock_response = Mock()
        mock_response.text = ""
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        assert len(nodes) == 0

    def test_parse_invalid_subscription(self, parser, mock_session):
        """测试解析无效订阅"""
        # 创建模拟响应
        mock_response = Mock()
        mock_response.text = "这不是有效的节点内容"
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        assert len(nodes) == 0

    def test_parse_subscription_with_http_error(self, parser, mock_session):
        """测试处理HTTP错误"""
        # 创建模拟响应
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        # 应该返回空列表，不抛出异常
        assert nodes == []

    def test_parse_subscription_with_timeout(self, parser, mock_session):
        """测试处理超时错误"""
        # 创建模拟响应
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Timeout")
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        # 应该返回空列表，不抛出异常
        assert nodes == []

    def test_skip_html_pages(self, parser):
        """测试跳过HTML页面"""
        # HTML页面应该被跳过
        nodes = parser.parse_subscription_url("http://example.com/article.html")

        assert nodes == []

    def test_parse_double_base64_subscription(self, parser, mock_session):
        """测试解析双重 Base64 编码的订阅"""
        # 创建双重编码的内容
        vmess_nodes = "vmess://eyJ2IjoiMiJ9"
        first_encoded = base64.b64encode(vmess_nodes.encode()).decode()
        second_encoded = base64.b64encode(first_encoded.encode()).decode()

        # 创建模拟响应
        mock_response = Mock()
        mock_response.text = second_encoded
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        assert len(nodes) > 0
        assert "vmess://" in nodes

    def test_parse_url_encoded_subscription(self, parser, mock_session):
        """测试解析 URL 编码的订阅"""
        # 创建URL编码的内容
        vmess_nodes = "vmess://eyJ2IjoiMiJ9"
        from urllib.parse import quote
        url_encoded = quote(vmess_nodes)

        # 创建模拟响应
        mock_response = Mock()
        mock_response.text = url_encoded
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        assert len(nodes) > 0
        assert "vmess://" in nodes

    def test_parse_mixed_format_subscription(self, parser, mock_session):
        """测试解析混合格式的订阅"""
        # 创建包含多种格式的模拟响应
        mock_response = Mock()
        mixed_content = """
vmess://eyJ2IjoiMiJ9
vless://uuid@example.com:443
"""
        mock_response.text = mixed_content
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        assert len(nodes) == 2
        assert "vmess://" in nodes
        assert "vless://" in nodes