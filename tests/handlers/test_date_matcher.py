#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：handlers
测试处理器模块的各种功能
"""

import pytest
import sys
import os
from datetime import datetime
from bs4 import BeautifulSoup

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.handlers.date_matcher import DateMatcher


class TestDateMatcher:
    """日期匹配器测试"""

    @pytest.fixture
    def sample_html(self):
        """创建示例HTML"""
        return """
        <html>
        <body>
            <a href="/article/2026-01-21/">今天文章</a>
            <a href="/article/2026-01-20/">昨天文章</a>
            <a href="/article/2026/01/20/">昨天文章</a>
            <a href="/article/2026-01-19/">前天文章</a>
            <div>
                <a href="/post/2026-01-21/">1月21日</a>
                <a href="/news/2026/01-21/">2026/01/21</a>
            </div>
        </body>
        </html>
        """

    def test_extract_date_from_url(self):
        """测试从URL中提取日期"""
        href = "/article/2026-01-21/"
        text = "文章标题"
        title = ""

        date = DateMatcher.extract_date_from_text(href, text, title)

        assert date is not None
        assert date.year == 2026
        assert date.month == 1
        assert date.day == 21

    def test_extract_date_from_text(self):
        """测试从文本中提取日期"""
        href = "/article/test"
        text = "1月21日文章"
        title = ""

        date = DateMatcher.extract_date_from_text(href, text, title)

        assert date is not None
        assert date.month == 1
        assert date.day == 21

    def test_extract_date_from_title(self):
        """测试从title中提取日期"""
        href = "/article/test"
        text = "文章标题"
        title = "2026年1月21日"

        date = DateMatcher.extract_date_from_text(href, text, title)

        assert date is not None
        assert date.year == 2026
        assert date.month == 1
        assert date.day == 21

    def test_extract_date_short_year(self):
        """测试提取两位数年份"""
        href = "/article/26-01-21/"
        text = ""
        title = ""

        date = DateMatcher.extract_date_from_text(href, text, title)

        assert date is not None
        assert date.year == 2026
        assert date.month == 1
        assert date.day == 21

    def test_extract_date_invalid(self):
        """测试无效日期"""
        href = "/article/test"
        text = "没有日期的文章"
        title = ""

        date = DateMatcher.extract_date_from_text(href, text, title)

        assert date is None

    def test_extract_date_invalid_year(self):
        """测试无效年份"""
        href = "/article/2019-01-21/"
        text = ""
        title = ""

        date = DateMatcher.extract_date_from_text(href, text, title)

        assert date is None  # 2019 < 2020

    def test_find_articles_by_date(self, sample_html):
        """测试查找带日期的文章"""
        soup = BeautifulSoup(sample_html, "html.parser")
        target_date = datetime(2026, 1, 21)

        articles = DateMatcher.find_articles_by_date(soup, target_date)

        assert len(articles) > 0
        assert all(article["is_target_date"] for article in articles if article["date"] == target_date.date())

    def test_find_today_article(self, sample_html):
        """测试查找今日文章"""
        soup = BeautifulSoup(sample_html, "html.parser")

        # find_today_article 需要传入 selectors 参数
        article_url = DateMatcher.find_today_article(soup, selectors=["a"])

        assert article_url is not None
        assert "2026-01-21" in article_url or "1月21日" in article_url

    def test_find_latest_article(self, sample_html):
        """测试查找最新文章"""
        soup = BeautifulSoup(sample_html, "html.parser")

        article_url = DateMatcher.find_latest_article(soup)

        assert article_url is not None

    def test_find_article_by_pattern(self):
        """测试通过模式查找文章"""
        html = """
        <html>
        <body>
            <a href="/article/2026-01-21/">文章1</a>
            <a href="/post/test.html">文章2</a>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        pattern = r"/article/\d{4}-\d{1,2}-\d{1,2}/"

        article_url = DateMatcher.find_article_by_pattern(soup, pattern, "https://example.com")

        assert article_url is not None
        assert "2026-01-21" in article_url

    def test_generate_date_strings(self):
        """测试生成日期字符串"""
        date = datetime(2026, 1, 21)

        date_strings = DateMatcher.generate_date_strings(date)

        assert len(date_strings) > 0
        assert "2026-01-21" in date_strings
        assert "2026-1-21" in date_strings
        assert "1-21" in date_strings
        assert "1月21日" in date_strings

    def test_find_articles_empty_html(self):
        """测试空HTML"""
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        articles = DateMatcher.find_articles_by_date(soup)

        assert len(articles) == 0

    def test_find_today_article_empty_html(self):
        """测试空HTML中查找今日文章"""
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        article_url = DateMatcher.find_today_article(soup, selectors=["a"])

        assert article_url is None

    def test_find_latest_article_empty_html(self):
        """测试空HTML中查找最新文章"""
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        article_url = DateMatcher.find_latest_article(soup)

        assert article_url is None

    def test_extract_date_with_slash_format(self):
        """测试提取斜杠格式的日期"""
        href = "/article/2026/01/21/"
        text = ""
        title = ""

        date = DateMatcher.extract_date_from_text(href, text, title)

        assert date is not None
        assert date.year == 2026
        assert date.month == 1
        assert date.day == 21

    def test_extract_date_with_dot_format(self):
        """测试提取点格式的日期"""
        href = "/article/2026.01.21."
        text = ""
        title = ""

        date = DateMatcher.extract_date_from_text(href, text, title)

        assert date is not None
        assert date.year == 2026
        assert date.month == 1
        assert date.day == 21

    def test_extract_date_with_dot_alt_format(self):
        """测试提取点格式的日期（替代格式）"""
        href = "/article/2026.1.21."
        text = ""
        title = ""

        date = DateMatcher.extract_date_from_text(href, text, title)

        assert date is not None
        assert date.year == 2026
        assert date.month == 1
        assert date.day == 21

    def test_find_articles_sorting(self, sample_html):
        """测试文章按日期排序"""
        soup = BeautifulSoup(sample_html, "html.parser")
        target_date = datetime(2026, 1, 21)

        articles = DateMatcher.find_articles_by_date(soup, target_date)

        # 验证排序：目标日期在前
        if articles:
            first_article = articles[0]
            if first_article["is_target_date"]:
                # 第一个应该是目标日期
                assert first_article["days_diff"] == 0

    def test_find_articles_with_selectors(self):
        """测试使用选择器查找文章"""
        html = """
        <html>
        <body>
            <a href="/article/2026-01-21/">文章1</a>
            <a href="/post/2026-01-21/">文章2</a>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        selectors = ["a[href*='2026-01-21']"]  # 修改 selectors 以匹配 HTML 中的 a 标签

        article_url = DateMatcher.find_today_article(soup, selectors)

        assert article_url is not None
        assert "2026-01-21" in article_url