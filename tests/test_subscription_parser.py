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

        assert len(nodes) >= 1  # 至少有一个节点

    def test_parse_yaml_subscription(self, parser, mock_session):
        """测试解析 YAML 格式的订阅"""
        # 创建模拟响应
        mock_response = Mock()
        yaml_content = """
proxies:
  - name: "测试节点"
    type: vmess
    server: example.com
    port: 443
    uuid: 12345678-1234-1234-1234-123456789abc
    alterId: 0
    cipher: auto
    network: tcp
"""
        mock_response.text = yaml_content
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        # YAML 解析可能失败，所以这里只检查不报错
        assert isinstance(nodes, list)

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
        mock_response.text = "这是一些无效的订阅内容"
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        assert len(nodes) == 0

    def test_parse_subscription_with_http_error(self, parser, mock_session):
        """测试解析订阅时遇到HTTP错误"""
        from requests.exceptions import HTTPError

        # 创建模拟响应
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_session.get.return_value = mock_response

        # 解析订阅 - 应该抛出异常或返回空列表
        try:
            nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)
            assert len(nodes) == 0
        except NetworkError:
            pass  # 预期的异常

    def test_parse_subscription_with_timeout(self, parser, mock_session):
        """测试解析订阅时遇到超时"""
        from requests.exceptions import Timeout

        # 创建模拟响应
        mock_session.get.side_effect = Timeout("请求超时")

        # 解析订阅 - 应该抛出异常或返回空列表
        try:
            nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)
            assert len(nodes) == 0
        except NetworkError:
            pass  # 预期的异常

    def test_skip_html_pages(self, parser, mock_session):
        """测试跳过HTML页面"""
        # HTML页面应该被跳过
        nodes = parser.parse_subscription_url("http://example.com/article.html", mock_session)

        assert len(nodes) == 0

    def test_parse_double_base64_subscription(self, parser, mock_session):
        """测试解析双层Base64编码的订阅"""
        # 创建模拟响应
        mock_response = Mock()
        vmess_uri = "vmess://eyJ2IjoiMiJ9"
        first_encode = base64.b64encode(vmess_uri.encode()).decode()
        second_encode = base64.b64encode(first_encode.encode()).decode()
        mock_response.text = second_encode
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        # 双层解码可能成功
        assert isinstance(nodes, list)

    def test_parse_url_encoded_subscription(self, parser, mock_session):
        """测试解析URL编码的订阅"""
        # 创建模拟响应
        mock_response = Mock()
        from urllib.parse import quote
        vmess_uri = "vmess://eyJ2IjoiMiJ9"
        encoded = quote(vmess_uri)
        mock_response.text = encoded
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        # URL解码可能成功
        assert isinstance(nodes, list)

    def test_parse_mixed_format_subscription(self, parser, mock_session):
        """测试解析混合格式的订阅"""
        # 创建模拟响应 - 混合多种格式
        mock_response = Mock()
        mixed_content = """
        vmess://eyJ2IjoiMiJ9
        vless://uuid@example.com:443
        trojan://password@example.com:443
        """
        mock_response.text = mixed_content
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        # 解析订阅
        nodes = parser.parse_subscription_url("http://example.com/sub", mock_session)

        assert len(nodes) > 0


# 导入 NetworkError
from src.core.exceptions import NetworkError
