#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求处理器 - 处理网络请求和重试逻辑
"""

import requests
import time
import os
import random
from typing import Optional
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RequestHandler:
    """请求处理器"""

    def __init__(self, session, timeout, retry_count, logger):
        """
        初始化请求处理器

        Args:
            session: requests会话对象
            timeout: 请求超时时间（秒）
            retry_count: 重试次数
            logger: 日志记录器
        """
        self.session = session
        self.timeout = timeout
        self.retry_count = retry_count
        self.logger = logger

    def make_request(self, url, method="GET", **kwargs):
        """
        带重试机制的请求方法，支持代理失败时自动切换到直接连接

        Args:
            url: 请求URL
            method: 请求方法（GET/POST等）
            **kwargs: 其他请求参数

        Returns:
            requests.Response对象

        Raises:
            Exception: 所有重试都失败后抛出异常
        """
        last_exception = None
        using_proxy = bool(
            self.session.proxies.get("http") or self.session.proxies.get("https")
        )

        for attempt in range(self.retry_count + 1):
            try:
                # GitHub Actions环境下添加随机延迟
                if os.getenv("GITHUB_ACTIONS") == "true" and attempt > 0:
                    time.sleep(random.uniform(1, 3))

                response = self.session.request(
                    method, url, timeout=self.timeout, verify=False, **kwargs
                )
                response.raise_for_status()

                # 检查返回内容是否过短（可能被拦截）
                if using_proxy and len(response.text) < 1000:
                    self.logger.warning(
                        f"返回内容过短（{len(response.text)}字节），可能被拦截: {url}"
                    )
                    if attempt == 0:
                        self.logger.info(f"尝试禁用代理直接访问: {url}")
                        self.session.proxies = {"http": None, "https": None}
                        using_proxy = False
                        continue

                return response

            except requests.exceptions.Timeout as e:
                last_exception = e
                self.logger.warning(
                    f"请求超时 (尝试 {attempt + 1}/{self.retry_count + 1}): {url}"
                )
                if attempt < self.retry_count:
                    time.sleep(2**attempt)  # 指数退避

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                self.logger.warning(
                    f"连接错误 (尝试 {attempt + 1}/{self.retry_count + 1}): {url}"
                )

                # 如果使用代理且连接失败，尝试禁用代理重试
                if using_proxy and attempt == 0:
                    self.logger.info(f"代理连接失败，尝试直接访问: {url}")
                    self.session.proxies = {"http": None, "https": None}
                    using_proxy = False
                    continue

                if attempt < self.retry_count:
                    time.sleep(2**attempt)

            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(
                    f"请求错误 (尝试 {attempt + 1}/{self.retry_count + 1}): {url}"
                )
                if attempt < self.retry_count:
                    time.sleep(1)

        # 所有重试都失败
        self.logger.error(
            f"请求失败，已重试 {self.retry_count + 1} 次: {last_exception}"
        )
        raise last_exception

    def test_proxy_connection(self):
        """测试代理连接"""
        if not self.session.proxies.get("http"):
            self.logger.debug("未设置代理，跳过测试")
            return False

        try:
            test_response = self.session.get(
                "https://httpbin.org/ip", timeout=10, verify=False
            )
            if test_response.status_code == 200:
                ip_info = test_response.json()
                self.logger.info(
                    f"✅ 代理连接测试成功，当前IP: {ip_info.get('origin', 'unknown')}"
                )
                return True
            else:
                self.logger.warning(
                    f"⚠️ 代理连接测试失败，状态码: {test_response.status_code}"
                )
                return False
        except Exception as e:
            self.logger.warning(f"⚠️ 代理连接测试异常: {str(e)}")
            return False