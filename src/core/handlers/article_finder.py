#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章查找器 - 查找文章链接和提取日期
"""

import re
import os
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright


class ArticleFinder:
    """文章查找器"""

    def __init__(self, base_url, site_name, logger, site_config):
        """
        初始化文章查找器

        Args:
            base_url: 网站基础URL
            site_name: 网站名称
            logger: 日志记录器
            site_config: 网站配置
        """
        self.base_url = base_url
        self.site_name = site_name
        self.logger = logger
        self.site_config = site_config

    def find_latest_article(self, soup, target_date=None):
        """
        从BeautifulSoup对象中查找最新文章URL

        Args:
            soup: BeautifulSoup对象
            target_date: 目标日期（默认为今天）

        Returns:
            文章URL或None
        """
        if target_date is None:
            target_date = datetime.now()

        # 收集所有包含日期的链接及其日期信息
        dated_links = []
        all_links = soup.find_all("a", href=True)

        self.logger.debug(f"找到 {len(all_links)} 个链接，开始提取日期...")

        extracted_count = 0
        exclusion_reasons = {}  # 统计排除原因

        for link in all_links:
            href = link.get("href")
            text = link.get_text(strip=True)
            title = link.get("title", "")  # 提取title属性，可能包含日期

            if not href:
                continue

            # 排除导航链接
            excluded = False
            exclusion_reason = ""
            if any(
                x in href
                for x in ["category", "tag", "page", "search", "about", "feed"]
            ):
                excluded = True
                exclusion_reason = "navigation link"
            elif href.startswith("#"):
                excluded = True
                exclusion_reason = "anchor link"
            elif len(href) < 10:
                excluded = True
                exclusion_reason = "href too short"

            if excluded:
                exclusion_reasons[exclusion_reason] = (
                    exclusion_reasons.get(exclusion_reason, 0) + 1
                )
                continue

            # 尝试从链接、文本或title中提取日期
            link_date = self._extract_date_from_text(href, text, title)

            if link_date is not None:
                extracted_count += 1
                # 计算与今天的天数差
                days_diff = abs((link_date.date() - target_date.date()).days)

                # 检查是否是今天的日期
                is_today = link_date.date() == target_date.date()

                dated_links.append(
                    {
                        "url": href,
                        "date": link_date,
                        "days_diff": days_diff,
                        "is_today": is_today,
                        "text": text,
                    }
                )

        self.logger.debug(
            f"提取到 {len(dated_links)} 个带日期的链接 (共尝试提取 {extracted_count} 个)"
        )

        # 显示排除统计
        if exclusion_reasons:
            self.logger.debug(f"链接排除统计: {exclusion_reasons}")

        # 显示前几个带日期的链接
        if dated_links:
            sample = dated_links[:5]
            for item in sample:
                self.logger.debug(
                    f"  📅 日期链接: {item['date'].strftime('%Y-%m-%d')} - {item['url'][:80]}... (文本: {item['text'][:30] if item['text'] else 'N/A'})"
                )
        else:
            # 显示一些样例链接，帮助诊断问题
            self.logger.warning(f"未找到带日期的链接，显示前10个链接样例:")
            sample_links = all_links[:10]
            for i, link in enumerate(sample_links):
                href = link.get("href", "")
                text = link.get_text(strip=True)[:50]
                self.logger.warning(f"  [{i + 1}] {href[:80]}... (文本: {text})")

        # 按日期排序：今天的在前，其次按日期新旧
        dated_links.sort(key=lambda x: (not x["is_today"], x["days_diff"]))

        # 如果有今天的日期，返回第一个
        today_article = None
        latest_article = None

        for item in dated_links:
            if item["is_today"] and today_article is None:
                today_article = item
            if latest_article is None:
                latest_article = item

        if today_article:
            article_url = self._process_url(today_article["url"])
            self.logger.info(f"✅ 找到今天的文章: {article_url}")
            return article_url

        # 如果没有今天的日期，返回最近的
        if latest_article:
            article_url = self._process_url(latest_article["url"])
            days_ago = (target_date.date() - latest_article["date"].date()).days
            if days_ago == 0:
                date_hint = "今天"
            elif days_ago == 1:
                date_hint = "昨天"
            else:
                date_hint = f"{days_ago}天前"

            self.logger.info(
                f"⚠️ 未找到今天的文章，使用最新的 ({date_hint} - {latest_article['date'].strftime('%Y-%m-%d')}): {article_url}"
            )
            return article_url

        # 如果日期匹配失败，尝试特定选择器
        selectors = self.site_config.get("selectors", [])
        for selector in selectors:
            links = soup.select(selector)
            if links:
                href = links[0].get("href")
                if href:
                    article_url = self._process_url(href)
                    self.logger.info(f"通过选择器找到文章: {article_url}")
                    return article_url

        # 如果都没找到，返回None
        self.logger.warning(f"未找到文章链接")
        return None

    def _extract_date_from_text(self, href, text, title=""):
        """
        从链接URL、文本或title属性中提取日期

        Args:
            href: 链接URL
            text: 链接文本
            title: 链接title属性

        Returns:
            datetime对象或None
        """
        # 常见日期格式模式
        date_patterns = [
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

        # 合并所有可用文本
        combined_text = f"{href} {text} {title}"

        today = datetime.now()

        for pattern in date_patterns:
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

    def _process_url(self, url):
        """处理URL，将相对URL转换为绝对URL"""
        if url.startswith("/"):
            return urljoin(self.base_url, url)
        return url

    def fetch_with_playwright(self, target_date=None):
        """
        使用Playwright浏览器自动化获取页面内容（禁用代理）

        Args:
            target_date: 目标日期

        Returns:
            文章URL或None
        """
        try:
            self.logger.info(f"启动浏览器访问: {self.base_url} (禁用代理)")

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                )
                page = context.new_page()
                # 使用 domcontentloaded 避免 networkidle 超时
                page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                # 等待额外时间让JS执行
                page.wait_for_timeout(3000)
                content = page.content()
                browser.close()

            self.logger.info(f"浏览器获取到 {len(content)} 字节内容")

            # 保存调试HTML
            debug_dir = os.path.join(os.getcwd(), "data", "debug")
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(
                debug_dir,
                f"debug_{self.site_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            )
            try:
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(content)
                self.logger.info(
                    f"💾 保存调试HTML到: {debug_file} ({len(content)} bytes)"
                )
            except Exception as e:
                self.logger.warning(f"保存调试HTML失败: {str(e)}")

            soup = BeautifulSoup(content, "html.parser")
            article_url = self.find_latest_article(soup, target_date)

            if article_url:
                self.logger.info(f"✅ 找到文章URL: {article_url}")
            else:
                self.logger.warning(f"❌ 未找到文章URL")

            return article_url

        except Exception as e:
            self.logger.error(f"Playwright访问失败: {str(e)}")
            return None