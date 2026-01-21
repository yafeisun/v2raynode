#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理管理模块
提供代理池管理、健康检查和自动切换功能
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import time
import random


@dataclass
class ProxyConfig:
    """代理配置"""
    url: str
    name: str = ""
    enabled: bool = True
    max_failures: int = 3  # 最大失败次数
    timeout: int = 10  # 健康检查超时（秒）
    check_interval: int = 300  # 健康检查间隔（秒）


@dataclass
class ProxyStatus:
    """代理状态"""
    config: ProxyConfig
    is_healthy: bool = True
    failure_count: int = 0
    last_check_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    response_time: float = 0.0  # 毫秒
    total_requests: int = 0
    successful_requests: int = 0

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def is_available(self) -> bool:
        """是否可用"""
        return self.config.enabled and self.is_healthy

    def record_success(self, response_time: float) -> None:
        """记录成功"""
        self.total_requests += 1
        self.successful_requests += 1
        self.last_success_time = datetime.now()
        self.response_time = response_time
        self.failure_count = 0
        self.is_healthy = True

    def record_failure(self) -> None:
        """记录失败"""
        self.total_requests += 1
        self.last_failure_time = datetime.now()
        self.failure_count += 1

        # 检查是否需要禁用
        if self.failure_count >= self.config.max_failures:
            self.is_healthy = False


class ProxyPool:
    """代理池"""

    def __init__(self):
        """初始化代理池"""
        self.proxies: Dict[str, ProxyStatus] = {}
        self._lock = threading.Lock()
        self._current_proxy: Optional[str] = None
        self._check_thread: Optional[threading.Thread] = None
        self._running = False

    def add_proxy(self, config: ProxyConfig) -> None:
        """
        添加代理

        Args:
            config: 代理配置
        """
        proxy_key = self._get_proxy_key(config.url)

        with self._lock:
            if proxy_key not in self.proxies:
                self.proxies[proxy_key] = ProxyStatus(config=config)

    def remove_proxy(self, url: str) -> None:
        """
        移除代理

        Args:
            url: 代理URL
        """
        proxy_key = self._get_proxy_key(url)

        with self._lock:
            if proxy_key in self.proxies:
                del self.proxies[proxy_key]

    def get_proxy(self) -> Optional[str]:
        """
        获取可用代理

        Returns:
            代理URL，如果没有可用代理则返回None
        """
        with self._lock:
            # 获取所有可用代理
            available_proxies = [
                key for key, status in self.proxies.items()
                if status.is_available
            ]

            if not available_proxies:
                return None

            # 如果当前代理可用，继续使用
            if self._current_proxy and self._current_proxy in available_proxies:
                return self._current_proxy

            # 否则随机选择一个可用代理
            self._current_proxy = random.choice(available_proxies)
            return self._current_proxy

    def get_proxy_dict(self) -> Optional[Dict[str, str]]:
        """
        获取代理字典（用于requests）

        Returns:
            代理字典，如果没有可用代理则返回None
        """
        proxy_url = self.get_proxy()
        if not proxy_url:
            return None

        return {
            "http": proxy_url,
            "https": proxy_url
        }

    def record_success(self, url: str, response_time: float) -> None:
        """
        记录请求成功

        Args:
            url: 代理URL
            response_time: 响应时间（毫秒）
        """
        proxy_key = self._get_proxy_key(url)

        with self._lock:
            if proxy_key in self.proxies:
                self.proxies[proxy_key].record_success(response_time)

    def record_failure(self, url: str) -> None:
        """
        记录请求失败

        Args:
            url: 代理URL
        """
        proxy_key = self._get_proxy_key(url)

        with self._lock:
            if proxy_key in self.proxies:
                self.proxies[proxy_key].record_failure()

                # 如果当前代理失败，切换到下一个
                if self._current_proxy == proxy_key:
                    self._current_proxy = None

    def get_status(self) -> Dict[str, Dict]:
        """
        获取所有代理状态

        Returns:
            代理状态字典
        """
        with self._lock:
            status_dict = {}

            for key, status in self.proxies.items():
                status_dict[key] = {
                    "url": status.config.url,
                    "name": status.config.name,
                    "enabled": status.config.enabled,
                    "is_healthy": status.is_healthy,
                    "is_available": status.is_available,
                    "failure_count": status.failure_count,
                    "max_failures": status.config.max_failures,
                    "success_rate": f"{status.success_rate:.2f}%",
                    "response_time": f"{status.response_time:.2f}ms",
                    "total_requests": status.total_requests,
                    "successful_requests": status.successful_requests,
                    "last_check_time": status.last_check_time.isoformat() if status.last_check_time else None,
                    "last_success_time": status.last_success_time.isoformat() if status.last_success_time else None,
                    "last_failure_time": status.last_failure_time.isoformat() if status.last_failure_time else None,
                }

            return status_dict

    def start_health_check(self, check_url: str = "https://httpbin.org/ip") -> None:
        """
        启动健康检查线程

        Args:
            check_url: 健康检查URL
        """
        if self._running:
            return

        self._running = True
        self._check_thread = threading.Thread(
            target=self._health_check_loop,
            args=(check_url,),
            daemon=True
        )
        self._check_thread.start()

    def stop_health_check(self) -> None:
        """停止健康检查"""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=5)

    def _health_check_loop(self, check_url: str) -> None:
        """
        健康检查循环

        Args:
            check_url: 健康检查URL
        """
        while self._running:
            try:
                self._check_all_proxies(check_url)
            except Exception as e:
                print(f"健康检查异常: {e}")

            # 等待下一次检查
            time.sleep(60)  # 每分钟检查一次

    def _check_all_proxies(self, check_url: str) -> None:
        """
        检查所有代理健康状态

        Args:
            check_url: 健康检查URL
        """
        import requests

        with self._lock:
            for proxy_key, status in self.proxies.items():
                if not status.config.enabled:
                    continue

                # 检查是否需要进行健康检查
                if status.last_check_time:
                    time_since_check = datetime.now() - status.last_check_time
                    if time_since_check.total_seconds() < status.config.check_interval:
                        continue

                # 执行健康检查
                try:
                    start_time = time.time()
                    response = requests.get(
                        check_url,
                        proxies={"http": status.config.url, "https": status.config.url},
                        timeout=status.config.timeout,
                        verify=False
                    )
                    response_time = (time.time() - start_time) * 1000

                    if response.status_code == 200:
                        status.record_success(response_time)
                    else:
                        status.record_failure()

                except Exception as e:
                    status.record_failure()

                status.last_check_time = datetime.now()

    def _get_proxy_key(self, url: str) -> str:
        """
        获取代理键

        Args:
            url: 代理URL

        Returns:
            代理键
        """
        # 移除用户名密码（如果有）
        if "@" in url:
            protocol, rest = url.split("://", 1)
            auth, host = rest.split("@", 1)
            return f"{protocol}://{host}"
        return url

    def print_status(self) -> None:
        """打印代理状态"""
        status = self.get_status()

        print("\n" + "="*60)
        print("代理池状态")
        print("="*60)

        if not status:
            print("\n⚠️  代理池为空")
            return

        for proxy_key, proxy_status in status.items():
            status_icon = "✅" if proxy_status["is_available"] else "❌"
            print(f"\n{status_icon} {proxy_status.get('name', proxy_key)}")
            print(f"  URL: {proxy_status['url']}")
            print(f"  状态: {'可用' if proxy_status['is_available'] else '不可用'}")
            print(f"  健康状态: {'健康' if proxy_status['is_healthy'] else '不健康'}")
            print(f"  成功率: {proxy_status['success_rate']}")
            print(f"  响应时间: {proxy_status['response_time']}")
            print(f"  失败次数: {proxy_status['failure_count']}/{proxy_status['max_failures']}")
            print(f"  总请求数: {proxy_status['total_requests']}")
            print(f"  成功请求: {proxy_status['successful_requests']}")

        print("\n" + "="*60)


# 全局代理池实例
_global_proxy_pool: Optional[ProxyPool] = None
_pool_lock = threading.Lock()


def get_proxy_pool() -> ProxyPool:
    """获取全局代理池实例"""
    global _global_proxy_pool

    if _global_proxy_pool is None:
        with _pool_lock:
            if _global_proxy_pool is None:
                _global_proxy_pool = ProxyPool()

    return _global_proxy_pool


def init_proxy_pool_from_env() -> ProxyPool:
    """
    从环境变量初始化代理池

    Returns:
        代理池实例
    """
    import os

    pool = get_proxy_pool()

    # 从环境变量读取代理
    http_proxy = os.getenv("http_proxy") or os.getenv("HTTP_PROXY")
    https_proxy = os.getenv("https_proxy") or os.getenv("HTTPS_PROXY")

    # 添加HTTP代理
    if http_proxy:
        pool.add_proxy(ProxyConfig(
            url=http_proxy,
            name="HTTP代理"
        ))

    # 添加HTTPS代理（如果与HTTP不同）
    if https_proxy and https_proxy != http_proxy:
        pool.add_proxy(ProxyConfig(
            url=https_proxy,
            name="HTTPS代理"
        ))

    return pool
