#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：handlers.article_finder
测试文章查找器的功能
"""

import pytest
import sys
import os
from bs4 import BeautifulSoup

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.handlers.article_finder import ArticleFinder


class TestArticleFinder:
    """文章查找器测试"""

    @pytest.fixture
    def sample_html(self):
        """创建示例HTML"""
        return """
        <html>
        <body>
            <div class="article">
                <h2><a href="/article/2026-01-21/">今天文章</a></h2>
            </div>
            <div class="article">
                <h2><a href="/article/2026-01-20/">昨天文章</a></h2>
            </div>
            <article>
                <h3><a href="/post/2026-01-21/">今日更新</a></h3>
            </article>
        </body>
        </html>
        """

    def test_find_articles_by_selectors(self, sample_html):
        """测试通过选择器查找文章"""
        soup = BeautifulSoup(sample_html, "html.parser")
        selectors = [".article h2 a", "article h3 a"]

        articles = ArticleFinder.find_articles_by_selectors(soup, selectors)

        assert len(articles) > 0
        assert all("href" in article for article in articles)

    def test_find_articles_by_selectors_empty(self):
        """测试空HTML"""
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        selectors = [".article a"]

        articles = ArticleFinder.find_articles_by_selectors(soup, selectors)

        assert len(articles) == 0

    def test_find_articles_by_selectors_no_match(self, sample_html):
        """测试不匹配的选择器"""
        soup = BeautifulSoup(sample_html, "html.parser")
        selectors = [".nonexistent a"]

        articles = ArticleFinder.find_articles_by_selectors(soup, selectors)

        assert len(articles) == 0

    def test_find_articles_by_selectors_multiple_selectors(self, sample_html):
        """测试多个选择器"""
        soup = BeautifulSoup(sample_html, "html.parser")
        selectors = [".article h2 a", "article h3 a"]

        articles = ArticleFinder.find_articles_by_selectors(soup, selectors)

        # 应该找到两个选择器的结果
        assert len(articles) >= 2

    def test_find_articles_in_content(self, sample_html):
        """测试在内容中查找文章"""
        soup = BeautifulSoup(sample_html, "html.parser")

        articles = ArticleFinder.find_articles_in_content(soup)

        assert len(articles) > 0

    def test_find_articles_in_content_empty(self):
        """测试空内容"""
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        articles = ArticleFinder.find_articles_in_content(soup)

        assert len(articles) == 0

    def test_extract_article_info(self):
        """测试提取文章信息"""
        html = """
        <a href="/article/2026-01-21/" title="文章标题">
            <span class="date">2026-01-21</span>
            文章内容
        </a>
        """
        soup = BeautifulSoup(html, "html.parser")
        link = soup.find("a")

        info = ArticleFinder.extract_article_info(link)

        assert info["url"] == "/article/2026-01-21/"
        assert info["title"] == "文章标题"
        assert "text" in info

    def test_filter_articles_by_date(self):
        """测试按日期过滤文章"""
        from datetime import datetime

        articles = [
            {"url": "/article/2026-01-21/", "date": datetime(2026, 1, 21)},
            {"url": "/article/2026-01-20/", "date": datetime(2026, 1, 20)},
            {"url": "/article/2026-01-19/", "date": datetime(2026, 1, 19)},
        ]

        target_date = datetime(2026, 1, 21)
        filtered = ArticleFinder.filter_articles_by_date(articles, target_date)

        assert len(filtered) > 0
        assert any(article["date"] == target_date for article in filtered)

    def test_filter_articles_by_date_none(self):
        """测试过滤没有日期的文章"""
        articles = [
            {"url": "/article/test1/", "date": None},
            {"url": "/article/test2/", "date": None},
        ]

        target_date = datetime(2026, 1, 21)
        filtered = ArticleFinder.filter_articles_by_date(articles, target_date)

        assert len(filtered) == 0

    def test_get_latest_article(self):
        """测试获取最新文章"""
        from datetime import datetime

        articles = [
            {"url": "/article/2026-01-21/", "date": datetime(2026, 1, 21)},
            {"url": "/article/2026-01-20/", "date": datetime(2026, 1, 20)},
            {"url": "/article/2026-01-19/", "date": datetime(2026, 1, 19)},
        ]

        latest = ArticleFinder.get_latest_article(articles)

        assert latest is not None
        assert latest["url"] == "/article/2026-01-21/"

    def test_get_latest_article_empty(self):
        """测试空列表"""
        articles = []

        latest = ArticleFinder.get_latest_article(articles)

        assert latest is None

    def test_get_latest_article_no_dates(self):
        """测试没有日期的文章"""
        articles = [
            {"url": "/article/test1/", "date": None},
            {"url": "/article/test2/", "date": None},
        ]

        latest = ArticleFinder.get_latest_article(articles)

        assert latest is not None
        assert latest["url"] in ["/article/test1/", "/article/test2/"]

    def test_find_article_links(self, sample_html):
        """测试查找文章链接"""
        soup = BeautifulSoup(sample_html, "html.parser")

        links = ArticleFinder.find_article_links(soup)

        assert len(links) > 0
        assert all(link.get("href") for link in links)

    def test_find_article_links_empty(self):
        """测试空HTML"""
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        links = ArticleFinder.find_article_links(soup)

        assert len(links) == 0

    def test_find_article_links_with_pattern(self):
        """测试按模式查找链接"""
        html = """
        <html>
        <body>
            <a href="/article/2026-01-21/">文章1</a>
            <a href="/post/test.html">文章2</a>
            <a href="/news/2026-01-21/">文章3</a>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        pattern = r"/article/\d{4}-\d{1,2}-\d{1,2}/"

        links = ArticleFinder.find_article_links(soup, pattern)

        assert len(links) == 1
        assert links[0].get("href") == "/article/2026-01-21/"

    def test_find_article_links_exclude_patterns(self):
        """测试排除特定模式的链接"""
        html = """
        <html>
        <body>
            <a href="/article/2026-01-21/">文章1</a>
            <a href="/page/1/">分页</a>
            <a href="/category/test/">分类</a>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        exclude_patterns = [r"/page/", r"/category/"]

        links = ArticleFinder.find_article_links(soup, exclude_patterns=exclude_patterns)

        assert len(links) == 1
        assert links[0].get("href") == "/article/2026-01-21/"

    def test_build_full_url(self):
        """测试构建完整URL"""
        relative_url = "/article/2026-01-21/"
        base_url = "https://example.com"

        full_url = ArticleFinder.build_full_url(relative_url, base_url)

        assert full_url == "https://example.com/article/2026-01-21/"

    def test_build_full_url_already_full(self):
        """测试已经是完整URL"""
        full_url = "https://example.com/article/2026-01-21/"
        base_url = "https://example.com"

        result = ArticleFinder.build_full_url(full_url, base_url)

        assert result == full_url

    def test_build_full_url_none_base(self):
        """测试没有base URL"""
        relative_url = "/article/2026-01-21/"

        result = ArticleFinder.build_full_url(relative_url, None)

        assert result == relative_url