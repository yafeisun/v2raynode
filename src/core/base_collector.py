#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础爬虫类
"""

import requests
import re
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from playwright.sync_api import sync_playwright

from src.config.settings import *
from src.config.websites import *
from src.utils.logger import get_logger
from src.core.protocol_converter import get_converter
from src.core.exceptions import (
    CollectorDisabledError,
    ArticleLinkNotFoundError,
    SubscriptionLinkNotFoundError,
    NetworkError,
    RequestTimeoutError,
    ConnectionError as V2RayConnectionError,
    ProxyError,
)


class BaseCollector(ABC):
    """基础爬虫抽象类"""

    def __init__(self, site_config):
        self.site_config = site_config
        self.site_name = site_config["name"]
        self.base_url = site_config["url"]
        self.enabled = site_config.get("enabled", True)
        self.last_article_url = None  # 记录最后访问的文章URL

        # 设置日志
        self.logger = get_logger(f"collector.{self.site_name}")

        # 创建会话
        self.session = requests.Session()

        # 添加更真实的请求头以绕过反爬虫
        # 在GitHub Actions环境中使用随机真实的User-Agent和更完整的请求头
        import os
        import random

        real_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

        if os.getenv("GITHUB_ACTIONS") == "true":
            browser_ua = random.choice(real_user_agents)
        else:
            browser_ua = USER_AGENT

        self.session.headers.update(
            {
                "User-Agent": browser_ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
                "DNT": "1",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-arch": '"x86"',
                "sec-ch-ua-bitness": '"64"',
                "sec-ch-ua-full-version": '"120.0.6099.109"',
                "sec-ch-ua-full-version-list": '"Not_A Brand";v="8.0.0.0", "Chromium";v="120.0.6099.109", "Google Chrome";v="120.0.6099.109"',
                "sec-ch-ua-model": '""',
                "sec-ch-ua-platform-version": '"15.0.0"',
            }
        )

        if os.getenv("GITHUB_ACTIONS") == "true":
            import time
            import random

            time.sleep(random.uniform(2, 4))

        # 禁用SSL验证（与代理使用保持一致）
        self.session.verify = False

        # 配置代理（如果系统有设置代理）
        import os
        from src.config.websites import BROWSER_ONLY_SITES

        http_proxy = os.getenv("http_proxy") or os.getenv("HTTP_PROXY")
        https_proxy = os.getenv("https_proxy") or os.getenv("HTTPS_PROXY")

        # 检查是否需要禁用代理（使用浏览器直连访问）
        site_key = self.site_config.get("collector_key", self.site_config.get("name"))
        if site_key in BROWSER_ONLY_SITES:
            self.logger.info(f"⚠️ {self.site_name} 使用浏览器直连访问（禁用代理）")
            http_proxy = None
            https_proxy = None

        # 设置session代理
        if http_proxy or https_proxy:
            self.session.proxies = {
                "http": http_proxy,
                "https": https_proxy,
            }
            self.logger.info(
                f"✅ 已设置代理 - HTTP: {http_proxy}, HTTPS: {https_proxy}"
            )
            # 验证代理设置
            self.logger.info(f"当前session代理设置: {self.session.proxies}")

            # 测试代理连接
            try:
                test_response = self.session.get(
                    "https://httpbin.org/ip", timeout=10, verify=False
                )
                if test_response.status_code == 200:
                    ip_info = test_response.json()
                    self.logger.info(
                        f"✅ 代理连接测试成功，当前IP: {ip_info.get('origin', 'unknown')}"
                    )
                else:
                    self.logger.warning(
                        f"⚠️ 代理连接测试失败，状态码: {test_response.status_code}"
                    )
            except Exception as e:
                self.logger.warning(f"⚠️ 代理连接测试异常: {str(e)}")
        else:
            self.logger.info("❌ 未检测到代理环境变量，将使用直连")

        # 配置参数
        self.timeout = REQUEST_TIMEOUT
        self.retry_count = REQUEST_RETRY
        self.delay = REQUEST_DELAY

        # 存储结果
        self.collected_nodes = []
        self.subscription_links = []

        self.raw_data = ""

        # 协议转换器
        self.converter = get_converter(self.logger)

        # 初始化辅助处理器
        from src.core.handlers import RequestHandler, ArticleFinder, SubscriptionExtractor

        self.request_handler = RequestHandler(
            self.session, self.timeout, self.retry_count, self.logger
        )
        self.article_finder = ArticleFinder(
            self.base_url, self.site_name, self.logger, self.site_config
        )
        self.subscription_extractor = SubscriptionExtractor(
            self.logger, self.site_config, self.converter, MIN_NODE_LENGTH
        )

    def _make_request(self, url, method="GET", **kwargs):
        """带重试机制的请求方法，支持代理失败时自动切换到直接连接"""
        return self.request_handler.make_request(url, method, **kwargs)

    def collect(self):
        """收集节点的主方法"""
        if not self.enabled:
            self.logger.info(f"{self.site_name} 已禁用，跳过收集")
            return []

        try:
            self.logger.info(f"开始收集 {self.site_name} 的节点")

            # 获取最新文章URL
            article_url = self.get_latest_article_url()
            if not article_url:
                self.logger.warning(f"{self.site_name}: 未找到最新文章")
                return []

            # 记录文章URL
            self.last_article_url = article_url

            # 提取节点信息
            nodes = self.extract_nodes_from_article(article_url)

            # 保存原始数据
            self.save_raw_data(article_url)

            self.logger.info(f"{self.site_name}: 收集到 {len(nodes)} 个节点")
            return nodes

        except requests.exceptions.Timeout as e:
            self.logger.error(f"{self.site_name}: 请求超时 - {str(e)}")
            return []
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"{self.site_name}: 连接错误 - {str(e)}")
            return []
        except requests.exceptions.ProxyError as e:
            self.logger.error(f"{self.site_name}: 代理错误 - {str(e)}")
            return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"{self.site_name}: 网络请求错误 - {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"{self.site_name}: 收集失败 - {str(e)}")
            return []

    def collect_links(self) -> Dict[str, Any]:
        """
        阶段1：只收集文章链接和订阅链接，不解析节点

        Returns:
            包含文章URL和订阅链接的字典
        """
        if not self.enabled:
            self.logger.info(f"{self.site_name} 已禁用，跳过链接收集")
            return {}

        try:
            self.logger.info(f"开始收集 {self.site_name} 的链接")

            # 获取最新文章URL
            article_url = self.get_latest_article_url()
            if not article_url:
                self.logger.warning(f"{self.site_name}: 未找到最新文章")
                return {}

            # 记录文章URL
            self.last_article_url = article_url

            # 检查是否为特殊标记（直接订阅链接）
            if article_url.endswith("#direct_subscription"):
                subscription_url = article_url.replace("#direct_subscription", "")
                self.logger.info(f"检测到直接订阅链接: {subscription_url}")
                return {
                    "article_url": article_url,
                    "subscription_links": [subscription_url],
                    "raw_data": "",
                }

            # 访问文章页面并提取订阅链接
            # 对于 BROWSER_ONLY_SITES，直接使用浏览器访问（不使用代理）
            from src.config.websites import BROWSER_ONLY_SITES

            site_key = self.site_config.get(
                "collector_key", self.site_config.get("name")
            )

            if site_key in BROWSER_ONLY_SITES:
                # 直接使用浏览器访问（跳过代理尝试）
                self.logger.info(f"使用浏览器访问文章页面: {article_url}")

                # 临时禁用代理
                original_proxies = self.session.proxies
                self.session.proxies = {"http": None, "https": None}

                try:
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
                        page.goto(
                            article_url, wait_until="domcontentloaded", timeout=90000
                        )
                        # 等待额外时间让JS执行
                        page.wait_for_timeout(5000)
                        content = page.content()
                        browser.close()

                    self.logger.info(f"浏览器访问成功，获取到 {len(content)} 字节内容")
                finally:
                    # 恢复代理设置
                    self.session.proxies = original_proxies
            else:
                response = self._make_request(article_url)
                content = response.text

            self.raw_data = content

            # 查找订阅链接
            subscription_links = self.find_subscription_links(content)
            self.subscription_links = subscription_links

            self.logger.info(
                f"{self.site_name}: 找到 {len(subscription_links)} 个订阅链接"
            )

            return {
                "article_url": article_url,
                "subscription_links": subscription_links,
                "raw_data": content,
            }

        except requests.exceptions.Timeout as e:
            self.logger.error(f"{self.site_name}: 链接收集超时 - {str(e)}")
            return {}
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"{self.site_name}: 链接收集连接错误 - {str(e)}")
            return {}
        except requests.exceptions.ProxyError as e:
            self.logger.error(f"{self.site_name}: 链接收集代理错误 - {str(e)}")
            return {}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"{self.site_name}: 链接收集网络请求错误 - {str(e)}")
            return {}
        except Exception as e:
            self.logger.error(f"{self.site_name}: 链接收集失败 - {str(e)}")
            return {}

    def get_latest_article_url(self, target_date=None):
        """获取文章URL，支持指定日期"""
        from src.config.websites import BROWSER_ONLY_SITES

        try:
            site_key = self.site_config.get(
                "collector_key", self.site_config.get("name")
            )
            use_browser_directly = site_key in BROWSER_ONLY_SITES

            self.logger.debug(
                f"site_key='{site_key}', BROWSER_ONLY_SITES={BROWSER_ONLY_SITES}, use_browser_directly={use_browser_directly}"
            )

            if use_browser_directly:
                self.logger.info(
                    f"使用浏览器直接访问 (BROWSER_ONLY_SITES): {self.base_url}"
                )
                article_url = self._fetch_with_playwright(target_date)
            else:
                self.logger.info(f"访问网站: {self.base_url}")
                response = self._make_request(self.base_url)
                soup = BeautifulSoup(response.text, "html.parser")

                article_url = self._find_article_from_soup(soup, target_date)

                if not article_url and self.session.proxies.get("http"):
                    self.logger.warning(f"使用代理未找到文章，尝试禁用代理直接访问")
                    self.session.proxies = {"http": None, "https": None}
                    self.logger.info(f"访问网站: {self.base_url} (直接连接)")
                    response = self._make_request(self.base_url)
                    soup = BeautifulSoup(response.text, "html.parser")
                    article_url = self._find_article_from_soup(soup, target_date)

                if not article_url:
                    self.logger.warning(f"{self.site_name}: 使用浏览器自动化重试")
                    article_url = self._fetch_with_playwright(target_date)

            if not article_url:
                self.logger.warning(f"{self.site_name}: 未找到最新文章")
                return None

            return article_url

        except Exception as e:
            self.logger.error(f"{self.site_name}: 获取文章URL失败 - {str(e)}")
            import traceback

            self.logger.error(f"详细错误: {traceback.format_exc()}")
            return None

    def _find_article_from_soup(self, soup, target_date=None):
        """从BeautifulSoup对象中查找文章URL - 优先今天，其次最近的"""
        # 默认使用今天作为目标日期
        if target_date is None:
            target_date = datetime.now()

        # 生成多种日期格式用于匹配
        date_str = target_date.strftime("%Y-%m-%d")  # 2026-01-19
        date_str_no_padding = (
            f"{target_date.year}-{target_date.month}-{target_date.day}"  # 2026-1-19
        )
        date_str_alt = target_date.strftime("%Y/%m/%d")  # 2026/01/19
        date_str_alt_no_padding = (
            f"{target_date.year}/{target_date.month}/{target_date.day}"  # 2026/1/19
        )
        date_str_month_day_cn = f"{target_date.month}月{target_date.day}日"  # 1月19日
        date_str_month_day_cn_alt = (
            f"{target_date.month:02d}月{target_date.day:02d}日"  # 01月19日
        )
        date_str_month_day = target_date.strftime("%m-%d")  # 01-19
        date_str_month_day_no_padding = f"{target_date.month}-{target_date.day}"  # 1-19
        date_str_year_month = target_date.strftime("%Y-%m")  # 2026-01
        date_str_year_month_cn = f"{target_date.year}年{target_date.month:02d}月{target_date.day:02d}日"  # 2026年01月19日

        # 收集所有包含日期的链接及其日期信息
        dated_links = []
        all_links = soup.find_all("a", href=True)

        self.logger.debug(f"找到 {len(all_links)} 个链接，开始提取日期...")

        # 保存HTML内容用于调试（问题网站）
        from src.config.websites import BROWSER_ONLY_SITES

        site_key = self.site_config.get("collector_key", self.site_config.get("name"))
        if site_key in BROWSER_ONLY_SITES:
            import os
            from datetime import datetime as dt

            debug_dir = os.path.join(os.getcwd(), "data", "debug")
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(
                debug_dir,
                f"debug_{self.site_name}_{dt.now().strftime('%Y%m%d_%H%M%S')}.html",
            )
            try:
                html_content = str(soup)
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                self.logger.info(
                    f"💾 保存调试HTML到: {debug_file} ({len(html_content)} bytes)"
                )
            except Exception as e:
                self.logger.warning(f"保存调试HTML失败: {str(e)}")

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

        # 尝试通用选择器
        for selector in UNIVERSAL_SELECTORS:
            links = soup.select(selector)
            if links:
                href = links[0].get("href")
                if href:
                    article_url = self._process_url(href)
                    self.logger.info(f"通过通用选择器找到文章: {article_url}")
                    return article_url

        # 尝试查找今日链接
        today_url = self._find_today_article(soup)
        if today_url:
            return today_url

        # 尝试通过时间查找
        time_url = self._find_by_time(soup)
        if time_url:
            return time_url

        # 如果所有方法都失败，才显示警告信息
        self.logger.warning(f"未找到带日期的链接，显示前3个链接样例:")
        sample_links = all_links[:3]
        for i, link in enumerate(sample_links):
            href = link.get("href", "")
            text = link.get_text(strip=True)[:50]
            self.logger.warning(f"  [{i + 1}] {href[:80]}... (文本: {text})")
        
        self.logger.warning(f"未找到文章链接")
        return None

    def _extract_date_from_text(self, href, text, title=""):
        """从链接URL、文本或title属性中提取日期"""
        import re
        from datetime import datetime

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

    def _fetch_with_playwright(self, target_date=None):
        """使用Playwright浏览器自动化获取页面内容（禁用代理）"""
        try:
            self.logger.info(f"启动浏览器访问: {self.base_url} (禁用代理)")

            # 临时禁用代理
            original_proxies = self.session.proxies
            self.session.proxies = {"http": None, "https": None}
            self.logger.debug("临时禁用代理")

            # 使用浏览器获取内容
            content = self._fetch_page_content_with_browser()

            # 恢复代理设置
            self.session.proxies = original_proxies
            self.logger.debug("恢复代理设置")

            self.logger.info(f"浏览器获取到 {len(content)} 字节内容")

            # 保存调试HTML
            self._save_debug_html(content)

            # 解析文章URL
            soup = BeautifulSoup(content, "html.parser")
            article_url = self._find_article_from_soup(soup, target_date)

            if article_url:
                self.logger.info(f"✅ 找到文章URL: {article_url}")
            else:
                self.logger.warning(f"❌ 未找到文章URL")

            return article_url

        except Exception as e:
            self.logger.error(f"Playwright访问失败: {str(e)}")
            # 恢复代理设置（即使失败也要恢复）
            if "original_proxies" in dir():
                self.session.proxies = original_proxies
            return None

    def _fetch_page_content_with_browser(self) -> str:
        """
        使用浏览器获取页面内容

        Returns:
            页面HTML内容
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
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

        return content

    def _save_debug_html(self, content: str):
        """
        保存调试HTML到文件

        Args:
            content: HTML内容
        """
        import os
        from datetime import datetime as dt

        debug_dir = os.path.join(os.getcwd(), "data", "debug")
        os.makedirs(debug_dir, exist_ok=True)
        debug_file = os.path.join(
            debug_dir,
            f"debug_{self.site_name}_{dt.now().strftime('%Y%m%d_%H%M%S')}.html",
        )
        try:
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.info(f"💾 保存调试HTML到: {debug_file} ({len(content)} bytes)")
        except Exception as e:
            self.logger.warning(f"保存调试HTML失败: {str(e)}")

    def extract_nodes_from_article(self, article_url):
        """从文章中提取节点"""
        try:
            self.logger.info(f"解析文章: {article_url}")
            response = self._make_request(article_url)

            content = response.text
            self.raw_data = content

            # 查找订阅链接
            subscription_links = self.find_subscription_links(content)
            self.subscription_links = subscription_links

            nodes = []

            # 从订阅链接获取节点
            for link in subscription_links:
                self.logger.info(f"找到订阅链接: {link}")
                sub_nodes = self.get_nodes_from_subscription(link)
                nodes.extend(sub_nodes)
                time.sleep(self.delay)  # 避免请求过快

            # 直接从页面提取节点
            direct_nodes = self.extract_direct_nodes(content)
            nodes.extend(direct_nodes)

            # 去重
            nodes = list(set(nodes))

            return nodes

        except Exception as e:
            self.logger.error(f"解析文章失败: {str(e)}")
            return []

    def find_subscription_links(self, content):
        """查找订阅链接"""
        links = []

        # 使用特定网站的模式
        patterns = self.site_config.get("patterns", [])
        for pattern in patterns:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                links.extend(matches)
            except Exception as e:
                self.logger.warning(f"模式匹配失败: {pattern} - {str(e)}")

        # 使用通用订阅模式
        for pattern in SUBSCRIPTION_PATTERNS:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        links.extend(match)
                    else:
                        links.append(match)
            except Exception as e:
                self.logger.warning(f"通用模式匹配失败: {pattern} - {str(e)}")

        # 在关键词附近查找
        for keyword in SUBSCRIPTION_KEYWORDS:
            try:
                pattern = rf"{keyword}[^:]*[:：]\s*(https?://[^\s\n\r]+)"
                matches = re.findall(pattern, content, re.IGNORECASE)
                links.extend(matches)
            except Exception:
                self.logger.debug(f"SUBSCRIPTION_KEYWORDS模式匹配失败: {keyword}")

        # 清理和去重
        cleaned_links = []
        seen = set()

        for link in links:
            # 先从原始链接中提取所有独立的.txt URL（避免先清理导致URL合并）
            # 使用正则表达式直接提取所有URL，在遇到HTML标签时停止
            url_matches = re.findall(r'https?://[^<\s"]+(?:\.(?:txt|TXT))', link)

            for url_match in url_matches:
                # 然后对每个提取的URL进行清理
                clean_link = self._clean_link(url_match)
                if (
                    clean_link
                    and clean_link not in seen
                    and self._is_valid_url(clean_link)
                    and self._is_valid_subscription_link(clean_link)
                ):
                    cleaned_links.append(clean_link)
                    seen.add(clean_link)

        return cleaned_links

    def get_nodes_from_subscription(self, subscription_url):
        """从订阅链接获取节点 - 支持多种编码格式"""
        try:
            self.logger.info(f"获取订阅内容: {subscription_url}")
            response = self._make_request(subscription_url)

            content = response.text.strip()

            # 检查内容是否为空
            if not content:
                self.logger.warning(f"订阅链接返回空内容: {subscription_url}")
                return []

            if len(content) < 10:  # 太短不可能是有效节点
                self.logger.warning(
                    f"订阅链接内容过短 ({len(content)} 字符): {subscription_url}"
                )
                return []

            # 尝试多种解析方式
            all_nodes = []

            # 方式1: 直接从原始内容提取
            nodes = self._extract_nodes_from_text(content)
            if nodes:
                self.logger.info(f"直接解析获取到 {len(nodes)} 个节点")
                all_nodes.extend(nodes)

            # 方式2: 尝试Base64解码
            all_nodes.extend(self._try_base64_decode(content))

            # 方式3: 尝试URL解码
            all_nodes.extend(self._try_url_decode(content))

            # 方式4: 逐行分割后提取（处理某些特殊格式）
            all_nodes.extend(self._try_line_by_line_parse(content))

            # 方式5: 尝试解析 YAML/JSON 格式（Clash配置）
            yaml_nodes = self._extract_yaml_json_nodes(content)
            if yaml_nodes:
                self.logger.info(f"YAML/JSON格式解析获取到 {len(yaml_nodes)} 个节点")
                all_nodes.extend(yaml_nodes)

            # 去重和过滤
            unique_nodes = self._deduplicate_and_filter_nodes(all_nodes)

            self.logger.info(
                f"从订阅链接获取到 {len(unique_nodes)} 个节点 (原始: {len(all_nodes)})"
            )
            return unique_nodes

        except Exception as e:
            self.logger.error(f"获取订阅链接失败: {str(e)}")
            return []

    def _try_base64_decode(self, content: str) -> List[str]:
        """
        尝试Base64解码内容

        Args:
            content: 原始内容

        Returns:
            解析到的节点列表
        """
        nodes = []
        try:
            import base64

            # 补齐base64 padding
            padded_content = content + "=" * (-len(content) % 4)
            decoded_content = base64.b64decode(padded_content).decode(
                "utf-8", errors="ignore"
            )
            nodes = self._extract_nodes_from_text(decoded_content)
            if nodes:
                self.logger.info(f"Base64解码后获取到 {len(nodes)} 个节点")
                return nodes

            # 尝试双重Base64解码（某些订阅链接使用双重编码）
            decoded_bytes = base64.b64decode(padded_content)
            double_padded = decoded_bytes + b"=" * (-len(decoded_bytes) % 4)
            double_decoded = base64.b64decode(double_padded).decode(
                "utf-8", errors="ignore"
            )
            nodes = self._extract_nodes_from_text(double_decoded)
            if nodes:
                self.logger.info(f"双重Base64解码后获取到 {len(nodes)} 个节点")

        except Exception as e:
            self.logger.debug(f"Base64解码失败: {str(e)}")

        return nodes

    def _try_url_decode(self, content: str) -> List[str]:
        """
        尝试URL解码内容

        Args:
            content: 原始内容

        Returns:
            解析到的节点列表
        """
        nodes = []
        try:
            from urllib.parse import unquote

            url_decoded = unquote(content)
            if url_decoded != content:  # 确实发生了解码
                nodes = self._extract_nodes_from_text(url_decoded)
                if nodes:
                    self.logger.info(f"URL解码后获取到 {len(nodes)} 个节点")
        except Exception as e:
            self.logger.debug(f"URL解码失败: {str(e)}")

        return nodes

    def _try_line_by_line_parse(self, content: str) -> List[str]:
        """
        逐行解析内容（处理某些特殊格式）

        Args:
            content: 原始内容

        Returns:
            解析到的节点列表
        """
        nodes = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue

            # 尝试从单行提取节点
            nodes.extend(self._extract_nodes_from_text(line))

            # 尝试Base64解码单行
            try:
                import base64

                padded_line = line + "=" * (-len(line) % 4)
                decoded_line = base64.b64decode(padded_line).decode(
                    "utf-8", errors="ignore"
                )
                nodes.extend(self._extract_nodes_from_text(decoded_line))

                # 尝试双重Base64解码
                decoded_bytes = base64.b64decode(padded_line)
                double_padded = decoded_bytes + b"=" * (-len(decoded_bytes) % 4)
                double_decoded = base64.b64decode(double_padded).decode(
                    "utf-8", errors="ignore"
                )
                nodes.extend(self._extract_nodes_from_text(double_decoded))
            except Exception:
                pass

        return nodes

    def _deduplicate_and_filter_nodes(self, nodes: List[str]) -> List[str]:
        """
        去重和过滤节点

        Args:
            nodes: 原始节点列表

        Returns:
            去重和过滤后的节点列表
        """
        # 去重
        unique_nodes = list(set(nodes))

        # 过滤长度
        unique_nodes = [
            node for node in unique_nodes if len(node) >= MIN_NODE_LENGTH
        ]

        return unique_nodes

    def _extract_nodes_from_text(self, text):
        """从文本中提取节点"""
        nodes = []
        for pattern in NODE_PATTERNS:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    node = match.strip()
                    if node and len(node) >= MIN_NODE_LENGTH:
                        nodes.append(node)
            except Exception as e:
                self.logger.warning(f"节点模式匹配失败: {pattern} - {str(e)}")
        return nodes

    def _extract_yaml_json_nodes(self, content):
        """从 YAML/JSON 格式提取节点（Clash配置格式）"""
        nodes = []
        try:
            # 首先尝试作为完整JSON解析
            json_nodes = self._parse_json_format(content)
            if json_nodes:
                return json_nodes

            # 尝试作为YAML解析
            yaml_nodes = self._parse_yaml_format(content)
            if yaml_nodes:
                return yaml_nodes

            # 回退方案：从文本中提取行内JSON对象
            inline_json_nodes = self._parse_inline_json(content)
            if inline_json_nodes:
                return inline_json_nodes

        except ImportError as e:
            self.logger.warning(f"模块导入失败: {str(e)}")
        except Exception as e:
            self.logger.warning(f"YAML/JSON 解析失败: {str(e)}")

        return nodes

    def _parse_json_format(self, content: str) -> List[str]:
        """解析JSON格式内容"""
        nodes = []
        try:
            import json

            data = json.loads(content.strip())
            proxies_list = None

            if isinstance(data, list):
                proxies_list = data
                self.logger.info(f"识别为JSON数组格式，包含 {len(proxies_list)} 个代理")
            elif isinstance(data, dict) and "proxies" in data:
                proxies_list = data["proxies"]
                self.logger.info(f"识别为JSON对象格式，包含 {len(proxies_list)} 个代理")

            if proxies_list:
                for proxy in proxies_list:
                    try:
                        node = self._convert_clash_proxy_to_node(proxy)
                        if node and len(node) >= MIN_NODE_LENGTH:
                            nodes.append(node)
                    except Exception as e:
                        self.logger.debug(f"JSON代理转换失败: {str(e)}")

        except json.JSONDecodeError:
            pass

        return nodes

    def _parse_yaml_format(self, content: str) -> List[str]:
        """解析YAML格式内容"""
        nodes = []
        try:
            import yaml

            self.logger.info("开始尝试YAML解析...")
            yaml_data = yaml.safe_load(content.strip())
            self.logger.info(f"YAML解析成功，数据类型: {type(yaml_data)}")

            if isinstance(yaml_data, dict) and "proxies" in yaml_data:
                return self._process_yaml_proxies(yaml_data["proxies"], "Clash配置格式")

            elif isinstance(yaml_data, list):
                return self._process_yaml_proxies(yaml_data, "代理列表格式")

            else:
                self.logger.info(f"YAML数据格式不支持: {type(yaml_data)}")

        except Exception as e:
            pass

        return nodes

    def _process_yaml_proxies(self, proxies_list: List, format_name: str) -> List[str]:
        """处理YAML代理列表"""
        nodes = []
        self.logger.info(f"识别为{format_name}，包含 {len(proxies_list)} 个代理")

        for i, proxy in enumerate(proxies_list):
            try:
                node = self._convert_clash_proxy_to_node(proxy)
                if node and len(node) >= MIN_NODE_LENGTH:
                    nodes.append(node)
                else:
                    self.logger.warning(f"YAML代理 {i + 1} 转换结果太短或为空")
            except Exception as e:
                self.logger.warning(f"YAML代理 {i + 1} 转换失败: {str(e)}")

        self.logger.info(f"YAML解析完成，共转换 {len(nodes)} 个节点")
        return nodes

    def _parse_inline_json(self, content: str) -> List[str]:
        """从YAML文本中提取行内JSON对象"""
        nodes = []

        if "proxies:" not in content and "proxies" not in content:
            return nodes

        try:
            import json

            lines = content.split("\n")
            json_objects = self._extract_json_objects_from_lines(lines)

            self.logger.info(f"从YAML文本中找到 {len(json_objects)} 个行内JSON对象")

            success_count = 0
            error_count = 0

            for json_str in json_objects:
                try:
                    proxy = json.loads(json_str)
                    node = self._convert_clash_proxy_to_node(proxy)
                    if node and len(node) >= MIN_NODE_LENGTH:
                        nodes.append(node)
                        success_count += 1
                    else:
                        error_count += 1
                except json.JSONDecodeError as e:
                    error_count += 1
                    if error_count <= 3:
                        self.logger.warning(f"行内JSON解析失败: {str(e)[:100]}")
                except Exception as e:
                    error_count += 1

            self.logger.info(f"YAML行内JSON解析完成: {success_count} 成功, {error_count} 失败")

        except Exception as e:
            self.logger.warning(f"行内JSON解析失败: {str(e)}")

        return nodes

    def _extract_json_objects_from_lines(self, lines: List[str]) -> List[str]:
        """从行列表中提取JSON对象"""
        json_objects = []

        for line in lines:
            line = line.strip()
            # 查找行内的 JSON 对象（支持嵌套）
            json_matches = re.findall(r"-\s*(\{[^}]*\{[^}]*\}[^}]*\})", line)
            if not json_matches:
                json_match = re.search(r"-\s*(\{.+\})", line)
                if json_match:
                    json_matches.append(json_match.group(1))

            for json_str in json_matches:
                json_objects.append(json_str)

        return json_objects

    def _convert_clash_proxy_to_node(self, proxy):
        """将 Clash proxy 对象转换为 V2Ray 节点 URI 格式"""
        return self.converter.convert(proxy)

    def get_v2ray_subscription_links(self, article_url):
        """获取V2Ray订阅链接"""
        try:
            # 检查是否为特殊标记（直接订阅链接）
            if article_url.endswith("#direct_subscription"):
                subscription_url = article_url.replace("#direct_subscription", "")
                self.logger.info(f"检测到直接订阅链接: {subscription_url}")
                return [subscription_url]

            self.logger.info(f"解析文章: {article_url}")
            response = self._make_request(article_url)

            content = response.text

            # 查找所有订阅链接
            subscription_links = self.find_subscription_links(content)

            # 过滤出V2Ray订阅链接
            v2ray_links = []
            for link in subscription_links:
                if self.is_v2ray_subscription(link):
                    v2ray_links.append(link)

            self.logger.info(f"从文章中找到 {len(v2ray_links)} 个V2Ray订阅链接")
            return v2ray_links

        except Exception as e:
            self.logger.error(f"获取V2Ray订阅链接失败: {str(e)}")
            return []

    def is_v2ray_subscription(self, url):
        """判断是否为V2Ray订阅链接"""
        try:
            # 订阅链接通常以http开头
            if not url.startswith("http"):
                return False

            from urllib.parse import urlparse

            parsed = urlparse(url)
            path_part = parsed.path.lower()
            domain = parsed.netloc.lower()

            # 必须以.txt、.yaml、.json结尾（V2Ray格式）
            if not path_part.endswith((".txt", ".yaml", ".json")):
                return False

            # 排除明显的Clash和Sing-Box订阅链接
            excluded_keywords = [
                "sing-box",
                "singbox",
                "yaml",
                "yml",
                "clash免费节点",
                "sing-box免费节点",
                "Clash免费节点",
                "Sing-Box免费节点",
            ]

            # 只检查路径部分，不检查域名
            for keyword in excluded_keywords:
                if keyword in path_part:
                    return False

            # 检查是否包含V2Ray相关关键词
            v2ray_keywords = ["v2ray", "sub", "subscribe", "node", "link"]
            for keyword in v2ray_keywords:
                if keyword in path_part:
                    return True

            return True

        except Exception:
            return False

    def extract_direct_nodes(self, content):
        """直接从页面内容提取节点"""
        nodes = []

        # 使用标准节点模式
        for pattern in NODE_PATTERNS:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    node = match.strip()
                    if len(node) >= MIN_NODE_LENGTH:
                        nodes.append(node)
            except Exception as e:
                self.logger.warning(f"节点模式匹配失败: {pattern} - {str(e)}")

        # 从代码块中提取
        for selector in CODE_BLOCK_SELECTORS:
            try:
                matches = re.findall(selector, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    block_nodes = self.parse_node_text(match)
                    nodes.extend(block_nodes)
            except Exception as e:
                self.logger.warning(f"代码块匹配失败: {selector} - {str(e)}")

        # 从Base64内容中提取
        for pattern in BASE64_PATTERNS:
            try:
                matches = re.findall(pattern, content)
                for match in matches:
                    try:
                        import base64

                        decoded = base64.b64decode(match).decode(
                            "utf-8", errors="ignore"
                        )
                        if any(
                            proto in decoded.lower() for proto in SUPPORTED_PROTOCOLS
                        ):
                            decoded_nodes = self.parse_node_text(decoded)
                            nodes.extend(decoded_nodes)
                    except Exception as e:
                        self.logger.debug(f"单行Base64解码失败: {str(e)}")
            except Exception as e:
                self.logger.debug(f"逐行处理失败: {str(e)}")

        return list(set(nodes))  # 去重

    def parse_node_text(self, text):
        """解析文本中的节点信息"""
        nodes = []

        for pattern in NODE_PATTERNS:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    node = match.strip()
                    if node and len(node) >= MIN_NODE_LENGTH:
                        nodes.append(node)
            except Exception as e:
                self.logger.warning(f"节点解析失败: {pattern} - {str(e)}")

        # 修复被错误标记为ss://的VMess节点
        nodes = self._fix_misidentified_nodes(nodes)

        return list(set(nodes))  # 去重

    def _fix_misidentified_nodes(self, nodes):
        """修复被错误标记为ss://的VMess节点"""
        fixed_nodes = []

        for node in nodes:
            if node.startswith("ss://"):
                # 尝试解码并检查是否为VMess节点
                try:
                    import base64
                    import json

                    # 去掉 ss://
                    data = node[5:]
                    # 补齐base64
                    data += "=" * (-len(data) % 4)
                    # URL解码
                    try:
                        from urllib.parse import unquote

                        data = unquote(data)
                    except Exception as e:
                        self.logger.debug(f"URL解码失败: {str(e)}")

                    decoded = base64.b64decode(data).decode("utf-8", errors="ignore")

                    # 检查是否为VMess JSON格式
                    if decoded.startswith("{") and decoded.endswith("}"):
                        try:
                            config = json.loads(decoded)
                            if config.get("v") == "2":
                                # 这是VMess节点，转换为正确的格式
                                self.logger.debug(
                                    f"检测到被错误标记为ss://的VMess节点，已修复"
                                )
                                fixed_nodes.append(
                                    f"vmess://{base64.b64encode(decoded.encode()).decode()}"
                                )
                                continue
                        except Exception as e:
                            self.logger.debug(f"VMess JSON解析失败: {str(e)}")
                except Exception as e:
                    self.logger.debug(f"ss节点修复失败: {str(e)}")

            # 保持原样
            fixed_nodes.append(node)

        return fixed_nodes

    def save_raw_data(self, article_url):
        """保存原始数据"""
        try:
            if not os.path.exists(RAW_DATA_DIR):
                os.makedirs(RAW_DATA_DIR)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.site_name}_{timestamp}.html"
            filepath = os.path.join(RAW_DATA_DIR, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"<!-- URL: {article_url} -->\n")
                f.write(f"<!-- Time: {datetime.now().isoformat()} -->\n")
                f.write(self.raw_data)

            self.logger.info(f"原始数据已保存: {filepath}")

        except Exception as e:
            self.logger.error(f"保存原始数据失败: {str(e)}")

    def _process_url(self, url):
        """处理URL"""
        if url.startswith("/"):
            return urljoin(self.base_url, url)
        return url

    def _find_today_article(self, soup):
        """查找今日文章"""
        try:
            today = datetime.now()
            date_patterns = [
                f"{today.month}-{today.day}",
                f"{today.year}-{today.month}-{today.day}",
                f"{today.month}月{today.day}日",
                f"{today.year}年{today.month}月{today.day}日",
            ]

            all_links = soup.find_all("a", href=True)

            for link in all_links:
                href = link.get("href")
                text = link.get_text().strip()

                for pattern in date_patterns:
                    if pattern in text:
                        article_url = self._process_url(href)
                        self.logger.info(f"找到今日文章: {article_url}")
                        return article_url

            return None

        except Exception as e:
            self.logger.error(f"查找今日文章失败: {str(e)}")
            return None

    def _find_by_time(self, soup):
        """通过时间查找文章"""
        try:
            for time_selector in TIME_SELECTORS:
                time_elements = soup.select(time_selector)
                if time_elements:
                    for time_elem in time_elements:
                        parent = time_elem.find_parent(["article", ".post", ".entry"])
                        if parent:
                            article_link = parent.find("a")
                            if article_link and article_link.get("href"):
                                article_url = self._process_url(
                                    article_link.get("href")
                                )
                                self.logger.info(f"通过时间找到文章: {article_url}")
                                return article_url

            return None

        except Exception as e:
            self.logger.error(f"通过时间查找文章失败: {str(e)}")
            return None

    def _clean_link(self, link):
        """清理链接 - 现在接收的已经是独立的URL"""
        if not link:
            return ""

        clean_link = link.strip()

        # 移除HTML实体编码
        clean_link = (
            clean_link.replace("%3C", "").replace("%3E", "").replace("%20", " ")
        )
        clean_link = (
            clean_link.replace("&lt;", "").replace("&gt;", "").replace("&nbsp;", " ")
        )

        # 处理常见的错误链接格式（只在末尾匹配）
        for suffix in ["/strong", "/span", "/pp", "/h3", "&nbsp;", "/div", "div", "/p"]:
            if clean_link.endswith(suffix):
                clean_link = clean_link[: -len(suffix)]

        # 移除末尾的HTML标签（包括完整标签如</p>、</div>等）
        clean_link = re.sub(r"<[^>]+>$", "", clean_link)
        # 移除末尾的无效字符
        clean_link = re.sub(r'[<>"]+$', "", clean_link)
        clean_link = clean_link.rstrip(";/")

        # 确保只返回有效的URL
        if not clean_link.startswith("http"):
            return ""

        # 验证URL格式
        if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", clean_link):
            return ""

        return clean_link.strip()

    def _is_valid_url(self, url):
        """验证URL是否有效"""
        try:
            url_pattern = re.compile(
                r"^https?://"
                r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
                r"localhost|"
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                r"(?::\d+)?"
                r"(?:/?|[/?]\S+)$",
                re.IGNORECASE,
            )
            return url_pattern.match(url) is not None
        except Exception as e:
            self.logger.debug(f"URL验证失败: {str(e)}")
            return False

    def _is_valid_subscription_link(self, url):
        """验证是否为有效的V2Ray订阅链接"""
        try:
            # 导入排除模式
            from src.config.websites import EXCLUDED_SUBSCRIPTION_PATTERNS

            # 检查是否匹配排除模式
            for pattern in EXCLUDED_SUBSCRIPTION_PATTERNS:
                if re.match(pattern, url, re.IGNORECASE):
                    self.logger.debug(f"链接被排除规则过滤: {url}")
                    return False

            # 必须以订阅文件扩展名结尾，排除网页文件
            valid_extensions = [".txt", ".yaml", ".yml", ".json", ".sub"]
            web_extensions = [".htm", ".html", ".php", ".asp", ".jsp"]

            url_lower = url.lower()
            has_valid_ext = any(url_lower.endswith(ext) for ext in valid_extensions)
            has_web_ext = any(url_lower.endswith(ext) for ext in web_extensions)

            if not has_valid_ext or has_web_ext:
                return False

            # 对于.yaml/.yml/.json文件，更宽松的验证（因为这些通常是结构化配置文件）
            if url_lower.endswith((".yaml", ".yml", ".json")):
                return True

            from urllib.parse import urlparse

            parsed = urlparse(url)
            path_part = parsed.path.lower()

            # 首先排除明显的非V2Ray文件（基于文件名模式，只检查路径部分）
            non_v2ray_patterns = [
                r".*/[^/]*clash[^/]*\.txt$",  # 排除clash相关的txt文件
                r".*/[^/]*sing.*box[^/]*\.txt$",  # 排除sing-box相关的txt文件
                r".*/[^/]*config[^/]*\.txt$",  # 排除config相关的txt文件
                # 注意：yaml和yml扩展名的文件现在是允许的
            ]

            for pattern in non_v2ray_patterns:
                if re.match(pattern, url, re.IGNORECASE):
                    return False

            # 检查URL路径中是否包含V2Ray相关关键词
            v2ray_keywords = [
                "v2ray",
                "sub",
                "subscribe",
                "node",
                "link",
                "vmess",
                "vless",
                "trojan",
            ]
            has_keyword = any(keyword in path_part for keyword in v2ray_keywords)

            # 如果路径中没有关键词，检查域名
            if not has_keyword:
                domain = parsed.netloc.lower()
                domain_keywords = ["v2ray", "node", "sub", "vmess", "vless", "trojan"]
                has_domain_keyword = any(
                    keyword in domain for keyword in domain_keywords
                )

                # 如果域名也没有关键词，则检查是否为常见的节点服务域名模式
                if not has_domain_keyword:
                    # 常见的节点服务域名模式
                    common_patterns = [
                        r".*\.mibei77\.com",
                        r".*\.freeclashnode\.com",
                        r".*node\..*",
                        r".*sub\..*",
                        r".*api\..*",
                        r".*\..*\.txt$",  # 任何包含数字和字母的.txt文件
                    ]

                    for pattern in common_patterns:
                        if re.match(pattern, url, re.IGNORECASE):
                            return True

                    # 如果都不匹配，则认为不是V2Ray订阅
                    return False

            # 排除明显的内容转换网站
            excluded_domains = [
                "subconverter",
                "subx",
                "sub.xeton",
                "api.v1.mk",
                "v1.mk",
                "raw.git",
                "githubusercontent.com",
                "gitlab.com",
            ]
            for domain in excluded_domains:
                if domain in parsed.netloc.lower():
                    return False

            return True

        except Exception as e:
            self.logger.warning(f"验证订阅链接时出错: {url} - {str(e)}")
            return False
