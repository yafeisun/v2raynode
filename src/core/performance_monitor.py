#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控模块
跟踪请求耗时、成功率等性能指标
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import time
import threading


@dataclass
class RequestMetrics:
    """请求指标"""
    url: str
    method: str
    success: bool
    duration: float  # 毫秒
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    status_code: Optional[int] = None


@dataclass
class CollectorMetrics:
    """收集器指标"""
    site_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration: float = 0.0  # 毫秒
    min_duration: float = float('inf')
    max_duration: float = 0.0
    last_request_time: Optional[datetime] = None
    last_error: Optional[str] = None
    recent_requests: List[RequestMetrics] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def avg_duration(self) -> float:
        """平均耗时（毫秒）"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_duration / self.successful_requests

    def add_request(self, metrics: RequestMetrics) -> None:
        """添加请求指标"""
        self.total_requests += 1
        self.last_request_time = metrics.timestamp

        if metrics.success:
            self.successful_requests += 1
            self.total_duration += metrics.duration
            self.min_duration = min(self.min_duration, metrics.duration)
            self.max_duration = max(self.max_duration, metrics.duration)
        else:
            self.failed_requests += 1
            self.last_error = metrics.error

        # 保留最近10个请求
        self.recent_requests.append(metrics)
        if len(self.recent_requests) > 10:
            self.recent_requests.pop(0)

    def get_summary(self) -> Dict[str, Any]:
        """获取摘要信息"""
        return {
            "site_name": self.site_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{self.success_rate:.2f}%",
            "avg_duration": f"{self.avg_duration:.2f}ms",
            "min_duration": f"{self.min_duration if self.min_duration != float('inf') else 0:.2f}ms",
            "max_duration": f"{self.max_duration:.2f}ms",
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "last_error": self.last_error,
        }


class PerformanceMonitor:
    """性能监控器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化监控器"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.metrics: Dict[str, CollectorMetrics] = defaultdict(
                lambda: CollectorMetrics(site_name="")
            )
            self.global_metrics = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_duration": 0.0,
                "start_time": datetime.now(),
            }

    def record_request(
        self,
        site_name: str,
        url: str,
        method: str,
        success: bool,
        duration: float,
        status_code: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """
        记录请求

        Args:
            site_name: 网站名称
            url: 请求URL
            method: 请求方法
            success: 是否成功
            duration: 耗时（毫秒）
            status_code: 状态码
            error: 错误信息
        """
        metrics = RequestMetrics(
            url=url,
            method=method,
            success=success,
            duration=duration,
            status_code=status_code,
            error=error
        )

        # 更新收集器指标
        collector_metrics = self.metrics[site_name]
        collector_metrics.site_name = site_name
        collector_metrics.add_request(metrics)

        # 更新全局指标
        self.global_metrics["total_requests"] += 1
        if success:
            self.global_metrics["successful_requests"] += 1
            self.global_metrics["total_duration"] += duration
        else:
            self.global_metrics["failed_requests"] += 1

    def get_collector_metrics(self, site_name: str) -> Optional[CollectorMetrics]:
        """
        获取收集器指标

        Args:
            site_name: 网站名称

        Returns:
            收集器指标对象
        """
        return self.metrics.get(site_name)

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有指标

        Returns:
            包含所有指标的字典
        """
        result = {
            "global": {
                "total_requests": self.global_metrics["total_requests"],
                "successful_requests": self.global_metrics["successful_requests"],
                "failed_requests": self.global_metrics["failed_requests"],
                "success_rate": f"{(self.global_metrics['successful_requests'] / self.global_metrics['total_requests'] * 100) if self.global_metrics['total_requests'] > 0 else 0:.2f}%",
                "avg_duration": f"{(self.global_metrics['total_duration'] / self.global_metrics['successful_requests']) if self.global_metrics['successful_requests'] > 0 else 0:.2f}ms",
                "uptime": str(datetime.now() - self.global_metrics["start_time"]),
            },
            "collectors": {}
        }

        for site_name, metrics in self.metrics.items():
            result["collectors"][site_name] = metrics.get_summary()

        return result

    def print_summary(self) -> None:
        """打印性能摘要"""
        metrics = self.get_all_metrics()

        print("\n" + "="*60)
        print("性能监控摘要")
        print("="*60)

        # 全局指标
        global_metrics = metrics["global"]
        print(f"\n📊 全局指标:")
        print(f"  总请求数: {global_metrics['total_requests']}")
        print(f"  成功请求: {global_metrics['successful_requests']}")
        print(f"  失败请求: {global_metrics['failed_requests']}")
        print(f"  成功率: {global_metrics['success_rate']}")
        print(f"  平均耗时: {global_metrics['avg_duration']}")
        print(f"  运行时间: {global_metrics['uptime']}")

        # 收集器指标
        print(f"\n📈 收集器指标:")
        for site_name, collector_metrics in metrics["collectors"].items():
            print(f"\n  {site_name}:")
            print(f"    总请求数: {collector_metrics['total_requests']}")
            print(f"    成功请求: {collector_metrics['successful_requests']}")
            print(f"    失败请求: {collector_metrics['failed_requests']}")
            print(f"    成功率: {collector_metrics['success_rate']}")
            print(f"    平均耗时: {collector_metrics['avg_duration']}")
            print(f"    最小耗时: {collector_metrics['min_duration']}")
            print(f"    最大耗时: {collector_metrics['max_duration']}")
            if collector_metrics['last_error']:
                print(f"    最后错误: {collector_metrics['last_error']}")

        print("\n" + "="*60)

    def reset(self) -> None:
        """重置所有指标"""
        self.metrics.clear()
        self.global_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_duration": 0.0,
            "start_time": datetime.now(),
        }


# 便捷函数
def get_monitor() -> PerformanceMonitor:
    """获取性能监控器实例"""
    return PerformanceMonitor()


def record_request(
    site_name: str,
    url: str,
    method: str,
    success: bool,
    duration: float,
    status_code: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """记录请求（便捷函数）"""
    monitor = get_monitor()
    monitor.record_request(site_name, url, method, success, duration, status_code, error)


class RequestTimer:
    """请求计时器上下文管理器"""

    def __init__(self, site_name: str, url: str, method: str = "GET"):
        """
        初始化计时器

        Args:
            site_name: 网站名称
            url: 请求URL
            method: 请求方法
        """
        self.site_name = site_name
        self.url = url
        self.method = method
        self.start_time = None
        self.end_time = None
        self.success = False
        self.error = None
        self.status_code = None

    def __enter__(self):
        """进入上下文"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.end_time = time.time()
        duration = (self.end_time - self.start_time) * 1000  # 转换为毫秒

        if exc_type is None:
            self.success = True
        else:
            self.success = False
            self.error = str(exc_val)

        # 记录请求
        record_request(
            site_name=self.site_name,
            url=self.url,
            method=self.method,
            success=self.success,
            duration=duration,
            status_code=self.status_code,
            error=self.error
        )

        # 不抑制异常
        return False

    def set_status_code(self, status_code: int) -> None:
        """设置状态码"""
        self.status_code = status_code
