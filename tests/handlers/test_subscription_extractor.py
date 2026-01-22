#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：handlers.subscription_extractor
测试订阅提取器的功能
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.handlers.subscription_extractor import SubscriptionExtractor
from src.core.protocol_converter import ProtocolConverter


class TestSubscriptionExtractor:
    """订阅提取器测试"""

    @pytest.fixture
    def mock_logger(self):
        """创建模拟的日志记录器"""
        logger = Mock()
        logger.debug = Mock()
        logger.warning = Mock()
        logger.error = Mock()
        logger.info = Mock()
        return logger

    @pytest.fixture
    def extractor(self, mock_logger):
        """创建订阅提取器实例"""
        converter = ProtocolConverter()
        return SubscriptionExtractor(
            logger=mock_logger,
            site_config={},
            converter=converter,
            min_node_length=20
        )

    def test_find_subscription_links(self, extractor):
        """测试查找订阅链接"""
        content = """
        <html>
        <body>
            <a href="https://example.com/sub1">订阅1</a>
            <a href="https://example.com/sub2">订阅2</a>
        </body>
        </html>
        """
        links = extractor.find_subscription_links(content)

        assert isinstance(links, list)

    def test_find_subscription_links_empty(self, extractor):
        """测试查找空内容"""
        content = ""
        links = extractor.find_subscription_links(content)

        assert isinstance(links, list)
        assert len(links) == 0

    def test_extract_nodes_from_text(self, extractor):
        """测试从文本中提取节点"""
        text = """
        vmess://eyJ2IjoiMiIsInBzIjoidGVzdCIsImFkZCI6ImV4YW1wbGUuY29tIn0=
        vless://uuid@example.com:443#test
        """
        nodes = extractor.extract_nodes_from_text(text)

        assert isinstance(nodes, list)
        assert len(nodes) > 0

    def test_extract_nodes_from_text_empty(self, extractor):
        """测试从空文本中提取节点"""
        text = ""
        nodes = extractor.extract_nodes_from_text(text)

        assert isinstance(nodes, list)
        assert len(nodes) == 0

    def test_parse_subscription_content(self, extractor):
        """测试解析订阅内容"""
        content = "vmess://eyJ2IjoiMiIsInBzIjoidGVzdCIsImFkZCI6ImV4YW1wbGUuY29tIn0="
        nodes = extractor.parse_subscription_content(content)

        assert isinstance(nodes, list)

    def test_parse_subscription_content_empty(self, extractor):
        """测试解析空订阅内容"""
        content = ""
        nodes = extractor.parse_subscription_content(content)

        assert isinstance(nodes, list)
        assert len(nodes) == 0

    def test_clean_link(self, extractor):
        """测试清理链接"""
        link = "  https://example.com/sub  "
        cleaned = extractor._clean_link(link)

        assert cleaned.strip() == cleaned

    def test_is_valid_url(self, extractor):
        """测试验证URL"""
        valid_url = "https://example.com/sub"
        invalid_url = "not-a-url"

        assert extractor._is_valid_url(valid_url) == True
        assert extractor._is_valid_url(invalid_url) == False


# 导入 Mock
from unittest.mock import Mock