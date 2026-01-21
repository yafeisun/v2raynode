#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：handlers.subscription_extractor
测试订阅提取器的功能
"""

import pytest
import sys
import os
from bs4 import BeautifulSoup
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.handlers.subscription_extractor import SubscriptionExtractor


class TestSubscriptionExtractor:
    """订阅提取器测试"""

    @pytest.fixture
    def sample_html_with_subscription(self):
        """创建包含订阅的HTML"""
        return """
        <html>
        <body>
            <div class="subscription">
                <code>vmess://eyJ2IjoiMiJ9</code>
            </div>
            <pre>vless://uuid@example.com:443</pre>
            <textarea>trojan://password@example.com:443</textarea>
            <p>vmess://eyJ2IjoiMiJ9</p>
        </body>
        </html>
        """

    def test_extract_subscriptions_from_text(self):
        """测试从文本中提取订阅"""
        text = """
        vmess://eyJ2IjoiMiJ9
        vless://uuid@example.com:443
        trojan://password@example.com:443
        """
        subscriptions = SubscriptionExtractor.extract_subscriptions_from_text(text)

        assert len(subscriptions) == 3
        assert "vmess://" in subscriptions
        assert "vless://" in subscriptions
        assert "trojan://" in subscriptions

    def test_extract_subscriptions_from_text_empty(self):
        """测试空文本"""
        text = ""
        subscriptions = SubscriptionExtractor.extract_subscriptions_from_text(text)

        assert len(subscriptions) == 0

    def test_extract_subscriptions_from_text_invalid(self):
        """测试无效文本"""
        text = "这不是订阅内容"
        subscriptions = SubscriptionExtractor.extract_subscriptions_from_text(text)

        assert len(subscriptions) == 0

    def test_extract_subscriptions_from_html(self, sample_html_with_subscription):
        """测试从HTML中提取订阅"""
        soup = BeautifulSoup(sample_html_with_subscription, "html.parser")
        subscriptions = SubscriptionExtractor.extract_subscriptions_from_html(soup)

        assert len(subscriptions) >= 3
        assert any("vmess://" in sub for sub in subscriptions)
        assert any("vless://" in sub for sub in subscriptions)
        assert any("trojan://" in sub for sub in subscriptions)

    def test_extract_subscriptions_from_html_empty(self):
        """测试空HTML"""
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        subscriptions = SubscriptionExtractor.extract_subscriptions_from_html(soup)

        assert len(subscriptions) == 0

    def test_extract_from_code_tag(self, sample_html_with_subscription):
        """测试从code标签提取"""
        soup = BeautifulSoup(sample_html_with_subscription, "html.parser")

        code_subscriptions = SubscriptionExtractor.extract_from_code_tags(soup)

        assert len(code_subscriptions) > 0
        assert any("vmess://" in sub for sub in code_subscriptions)

    def test_extract_from_pre_tag(self, sample_html_with_subscription):
        """测试从pre标签提取"""
        soup = BeautifulSoup(sample_html_with_subscription, "html.parser")

        pre_subscriptions = SubscriptionExtractor.extract_from_pre_tags(soup)

        assert len(pre_subscriptions) > 0
        assert any("vless://" in sub for sub in pre_subscriptions)

    def test_extract_from_textarea_tag(self, sample_html_with_subscription):
        """测试从textarea标签提取"""
        soup = BeautifulSoup(sample_html_with_subscription, "html.parser")

        textarea_subscriptions = SubscriptionExtractor.extract_from_textarea_tags(soup)

        assert len(textarea_subscriptions) > 0
        assert any("trojan://" in sub for sub in textarea_subscriptions)

    def test_extract_from_paragraphs(self, sample_html_with_subscription):
        """测试从段落提取"""
        soup = BeautifulSoup(sample_html_with_subscription, "html.parser")

        paragraph_subscriptions = SubscriptionExtractor.extract_from_paragraphs(soup)

        assert len(paragraph_subscriptions) > 0

    def test_extract_multiple_protocols(self):
        """测试多种协议"""
        text = """
        vmess://eyJ2IjoiMiJ9
        vless://uuid@example.com:443
        trojan://password@example.com:443
        ss://Y2lwaGVyOnRlc3RAZXhhbXBsZS5jb206ODM4OA==
        ssr://Y2lwaGVyOnRlc3RAZXhhbXBsZS5jb206ODM4OA==
        hysteria2://password@example.com:443
        """
        subscriptions = SubscriptionExtractor.extract_subscriptions_from_text(text)

        assert len(subscriptions) == 6
        assert "vmess://" in subscriptions
        assert "vless://" in subscriptions
        assert "trojan://" in subscriptions
        assert "ss://" in subscriptions
        assert "ssr://" in subscriptions
        assert "hysteria2://" in subscriptions

    def test_deduplicate_subscriptions(self):
        """测试去重"""
        text = """
        vmess://eyJ2IjoiMiJ9
        vmess://eyJ2IjoiMiJ9
        vless://uuid@example.com:443
        """
        subscriptions = SubscriptionExtractor.extract_subscriptions_from_text(text)

        # 应该去重
        assert len(subscriptions) == 2

    def test_clean_subscriptions(self):
        """测试清理订阅"""
        text = """
        vmess://eyJ2IjoiMiJ9
        vless://uuid@example.com:443

        trojan://password@example.com:443
        """
        subscriptions = SubscriptionExtractor.extract_subscriptions_from_text(text)

        # 应该去除空行和多余空格
        assert all(sub.strip() == sub for sub in subscriptions)
        assert all(sub for sub in subscriptions)  # 没有空字符串

    def test_extract_with_html_entities(self):
        """测试包含HTML实体的文本"""
        text = "vmess://eyJ2IjoiMiJ9&nbsp;vless://uuid@example.com:443"

        subscriptions = SubscriptionExtractor.extract_subscriptions_from_text(text)

        assert len(subscriptions) == 2

    def test_extract_with_special_chars(self):
        """测试包含特殊字符"""
        text = """
        vmess://eyJ2IjoiMiJ9
        vless://uuid@example.com:443?security=tls#test节点
        """
        subscriptions = SubscriptionExtractor.extract_subscriptions_from_text(text)

        assert len(subscriptions) == 2
        assert "test节点" in subscriptions[1]

    def test_extract_long_subscription(self):
        """测试长订阅"""
        long_vmess = "vmess://" + "a" * 1000
        text = f"{long_vmess}\nvless://uuid@example.com:443"

        subscriptions = SubscriptionExtractor.extract_subscriptions_from_text(text)

        assert len(subscriptions) == 2

    def test_extract_with_comments(self):
        """测试包含注释"""
        text = """
        <!-- vmess://eyJ2IjoiMiJ9 -->
        vmess://eyJ2IjoiMiJ9
        vless://uuid@example.com:443
        """
        subscriptions = SubscriptionExtractor.extract_subscriptions_from_text(text)

        # 应该忽略注释中的内容
        assert len(subscriptions) == 2

    def test_extract_with_script_tags(self):
        """测试包含script标签"""
        html = """
        <html>
        <body>
            <script>vmess://eyJ2IjoiMiJ9</script>
            <p>vless://uuid@example.com:443</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        subscriptions = SubscriptionExtractor.extract_subscriptions_from_html(soup)

        # 应该忽略script标签中的内容
        assert len(subscriptions) == 1
        assert "vless://" in subscriptions[0]

    def test_extract_from_nested_elements(self):
        """测试从嵌套元素提取"""
        html = """
        <html>
        <body>
            <div>
                <div>
                    <code>vmess://eyJ2IjoiMiJ9</code>
                </div>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        subscriptions = SubscriptionExtractor.extract_subscriptions_from_html(soup)

        assert len(subscriptions) > 0
        assert "vmess://" in subscriptions[0]

    def test_extract_with_base64_content(self):
        """测试Base64编码的内容"""
        import base64
        vmess_nodes = "vmess://eyJ2IjoiMiJ9\nvless://uuid@example.com:443"
        base64_content = base64.b64encode(vmess_nodes.encode()).decode()

        text = base64_content
        subscriptions = SubscriptionExtractor.extract_subscriptions_from_text(text)

        # Base64内容可能不被识别为订阅
        # 这个测试主要是确保不会崩溃
        assert isinstance(subscriptions, list)

    def test_extract_from_multiple_code_blocks(self):
        """测试多个代码块"""
        html = """
        <html>
        <body>
            <code>vmess://eyJ2IjoiMiJ9</code>
            <code>vless://uuid@example.com:443</code>
            <code>trojan://password@example.com:443</code>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        subscriptions = SubscriptionExtractor.extract_from_code_tags(soup)

        assert len(subscriptions) == 3