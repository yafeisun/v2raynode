#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期匹配辅助类
提供日期匹配和文章查找的公共逻辑
"""

from typing import Optional, List, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
import re


class DateMatcher:
    """日期匹配器"""

    # 常见日期格式模式
    DATE_PATTERNS = [
        # URL中的日期格式
        r"/(\d{4})-(\d{1,2})-(\d{1,2})/",  # /2026-1-19/ 或 /2026-01-19/
        r"/(\d{4})/(\d{1,2})/(\d{1,2})/",  # /2026/1/19/ 或 /2026/01/19/
        r"/(\d{4})-(\d{1,2})-(\d{1,2})\.",  # /2026-1-19. 或 /2026-01-19.
        r"/(\d{4})/(\d{1,2})/(\d{1,2})\.",  # /2026/1/19. 或 /2026/01/19.
        # 文本中的日期格式 - 中文格式
        r"(\d{1,2})月(\d{1,2})日",  # 1月19日 或 01月19日
        r"(\d{4})年(\d{1,2})月(\d{1,2})日",  # 2026年1月19日
        r"(\d{2})-(\d{1,2})-(\d{1,2})",  # 26-01-19 (假设21世纪)
        r"(\d{2})\.(\d{1,2})\.(\d{1,2})",  # 26.01.19 (假设21世纪)
    ]

    @classmethod
    def extract_date_from_text(cls, href: str, text: str, title: str = "") -> Optional[datetime]:
        """
        从链接URL、文本或title属性中提取日期

        Args:
            href: 链接URL
            text: 链接文本
            title: 链接title属性

        Returns:
            提取到的日期对象，如果未找到则返回None
        """
        # 合并所有可用文本
        combined_text = f"{href} {text} {title}"

        today = datetime.now()

        for pattern in cls.DATE_PATTERNS:
            match = re.search(pattern, combined_text)
            if match:
                try:
                    groups = match.groups()
                    groups_len = len(groups)

                    year = None
                    month = None
                    day = None

                    # 根据模式和组数处理
                    if groups_len == 3:
                        # 3个组：可能是 URL 格式或 "年/月/日" 中文格式
                        if "月" in pattern and "年" in pattern:
                            # 2026年1月19日 格式
                            year, month, day = (
                                int(groups[0]),
                                int(groups[1]),
                                int(groups[2]),
                            )
                        else:
                            # URL 格式: 2026-1-19 或 26-01-19
                            year = int(groups[0])
                            month = int(groups[1])
                            day = int(groups[2])

                            # 处理两位数年份
                            if year < 100:
                                year = 2000 + year

                    elif groups_len == 2:
                        # 2个组：只有月日的中文格式 (如 1月18日)
                        if "月" in pattern:
                            year = today.year
                            month = int(groups[0])
                            day = int(groups[1])
                        else:
                            # 其他2组格式，不处理
                            continue

                    else:
                        # 不支持的组数
                        continue

                    # 验证日期有效性
                    if (
                        year
                        and month
                        and day
                        and 2020 <= year <= 2030
                        and 1 <= month <= 12
                        and 1 <= day <= 31
                    ):
                        return datetime(year, month, day)

                except (ValueError, TypeError):
                    continue

        return None

    @classmethod
    def find_articles_by_date(
        cls,
        soup: BeautifulSoup,
        target_date: Optional[datetime] = None,
        date_patterns: Optional[List[str]] = None
    ) -> List[dict]:
        """
        从BeautifulSoup对象中查找带日期的文章链接

        Args:
            soup: BeautifulSoup对象
            target_date: 目标日期（默认为今天）
            date_patterns: 自定义日期模式（默认使用内置模式）

        Returns:
            包含日期信息的链接列表
        """
        # 默认使用今天作为目标日期
        if target_date is None:
            target_date = datetime.now()

        # 使用自定义日期模式或内置模式
        patterns = date_patterns if date_patterns else cls.DATE_PATTERNS

        # 收集所有包含日期的链接及其日期信息
        dated_links = []
        all_links = soup.find_all("a", href=True)

        for link in all_links:
            href = link.get("href")
            text = link.get_text(strip=True)
            title = link.get("title", "")

            if not href:
                continue

            # 尝试从链接、文本或title中提取日期
            link_date = cls.extract_date_from_text(href, text, title)

            if link_date is not None:
                # 计算与目标日期的天数差
                days_diff = abs((link_date.date() - target_date.date()).days)

                # 检查是否是目标日期
                is_target_date = link_date.date() == target_date.date()

                dated_links.append({
                    "url": href,
                    "date": link_date,
                    "days_diff": days_diff,
                    "is_target_date": is_target_date,
                    "text": text,
                })

        # 按日期排序：目标日期在前，其次按日期新旧
        dated_links.sort(key=lambda x: (not x["is_target_date"], x["days_diff"]))

        return dated_links

    @classmethod
    def find_today_article(
        cls,
        soup: BeautifulSoup,
        selectors: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        查找今日文章

        Args:
            soup: BeautifulSoup对象
            selectors: CSS选择器列表

        Returns:
            文章URL，如果未找到则返回None
        """
        today = datetime.now()
        dated_links = cls.find_articles_by_date(soup, today)

        # 如果有今天的日期，返回第一个
        for item in dated_links:
            if item["is_target_date"]:
                return item["url"]

        # 如果没有今天的日期，尝试使用选择器
        if selectors:
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    href = links[0].get("href")
                    if href:
                        return href

        return None

    @classmethod
    def find_latest_article(
        cls,
        soup: BeautifulSoup,
        selectors: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        查找最新文章（不限制日期）

        Args:
            soup: BeautifulSoup对象
            selectors: CSS选择器列表

        Returns:
            文章URL，如果未找到则返回None
        """
        dated_links = cls.find_articles_by_date(soup)

        # 返回最新的文章
        if dated_links:
            return dated_links[0]["url"]

        # 如果没有带日期的链接，尝试使用选择器
        if selectors:
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    href = links[0].get("href")
                    if href:
                        return href

        return None

    @classmethod
    def generate_date_strings(cls, date: datetime) -> List[str]:
        """
        生成多种日期格式字符串

        Args:
            date: 日期对象

        Returns:
            日期字符串列表
        """
        return [
            date.strftime("%Y-%m-%d"),  # 2026-01-19
            f"{date.year}-{date.month}-{date.day}",  # 2026-1-19
            date.strftime("%Y/%m/%d"),  # 2026/01/19
            f"{date.year}/{date.month}/{date.day}",  # 2026/1/19
            date.strftime("%m-%d"),  # 01-19
            f"{date.month}-{date.day}",  # 1-19
            f"{date.month}月{date.day}日",  # 1月19日
            f"{date.month:02d}月{date.day:02d}日",  # 01月19日
            f"{date.year}年{date.month:02d}月{date.day:02d}日",  # 2026年01月19日
        ]

    @classmethod
    def find_article_by_pattern(
        cls,
        soup: BeautifulSoup,
        pattern: str,
        base_url: str
    ) -> Optional[str]:
        """
        通过模式查找文章链接

        Args:
            soup: BeautifulSoup对象
            pattern: 匹配模式
            base_url: 基础URL

        Returns:
            文章URL，如果未找到则返回None
        """
        from urllib.parse import urljoin

        links = soup.find_all("a", href=True)
        for link in links:
            href = link.get("href", "")
            if re.search(pattern, href, re.IGNORECASE):
                article_url = urljoin(base_url, href)
                return article_url

        return None