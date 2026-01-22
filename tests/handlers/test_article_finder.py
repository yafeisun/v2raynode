#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：handlers.article_finder
测试文章查找器的功能
"""

import pytest
import sys
import os
from datetime import datetime
from bs4 import BeautifulSoup

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.handlers.article_finder import ArticleFinder


class TestArticleFinder:
    """文章查找器测试"""

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
    def finder(self, mock_logger):
        """创建文章查找器实例"""
        return ArticleFinder(
            base_url="http://example.com",
            site_name="test_site",
            logger=mock_logger,
            site_config={}
        )

    @pytest.fixture
    def sample_html(self):
        """示例HTML内容"""
        return """
        <html>
        <body>
            <div>
                <a href="/article/2026-01-21/">今日文章</a>
                <a href="/article/2026-01-20/">昨日文章</a>
                <a href="/article/2026-01-19/">前日文章</a>
            </div>
        </body>
        </html>
        """

    def test_find_latest_article(self, finder, sample_html):
        """测试查找最新文章"""
        soup = BeautifulSoup(sample_html, "html.parser")
        target_date = datetime(2026, 1, 21)

        article_url = finder.find_latest_article(soup, target_date)

        assert article_url is not None
        assert "2026-01-21" in article_url

    def test_find_latest_article_empty_html(self, finder):
        """测试查找空HTML"""
        soup = BeautifulSoup("", "html.parser")
        target_date = datetime(2026, 1, 21)

        article_url = finder.find_latest_article(soup, target_date)

        assert article_url is None

    def test_find_latest_article_no_match(self, finder):
        """测试查找没有匹配的文章 - 返回最近的文章"""
        html = """
        <html>
        <body>
            <a href="/article/2026-01-20/">昨日文章</a>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        target_date = datetime(2026, 1, 21)

        article_url = finder.find_latest_article(soup, target_date)

        # 如果找不到目标日期的文章，会返回最近的文章
        assert article_url is not None
        assert "2026-01-20" in article_url

    def test_find_latest_article_with_full_url(self, finder):
        """测试查找完整URL的文章"""
        html = """
        <html>
        <body>
            <a href="http://example.com/article/2026-01-21/">今日文章</a>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        target_date = datetime(2026, 1, 21)

        article_url = finder.find_latest_article(soup, target_date)

        assert article_url is not None
        assert "2026-01-21" in article_url


# 导入 Mock
from unittest.mock import Mock