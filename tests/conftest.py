#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest配置文件
提供测试所需的fixtures和配置
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="session")
def project_root_dir():
    """项目根目录"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return os.path.join(project_root, "tests", "data")


@pytest.fixture(scope="session")
def sample_html_content():
    """示例HTML内容"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>测试页面</title>
    </head>
    <body>
        <div class="container">
            <h1>测试标题</h1>
            <div class="article">
                <h2><a href="/article/2026-01-21/">今天文章</a></h2>
                <p>文章内容...</p>
            </div>
            <div class="article">
                <h2><a href="/article/2026-01-20/">昨天文章</a></h2>
                <p>文章内容...</p>
            </div>
            <div class="subscription">
                <code>vmess://eyJ2IjoiMiJ9</code>
            </div>
            <pre>vless://uuid@example.com:443</pre>
        </div>
    </body>
    </html>
    """


@pytest.fixture(scope="session")
def sample_subscription_text():
    """示例订阅文本"""
    return """
    vmess://eyJ2IjoiMiJ9
    vless://uuid@example.com:443
    trojan://password@example.com:443
    ss://Y2lwaGVyOnRlc3RAZXhhbXBsZS5jb206ODM4OA==
    """


@pytest.fixture(scope="session")
def sample_vmess_config():
    """示例VMess配置"""
    return {
        "v": "2",
        "ps": "测试节点",
        "add": "example.com",
        "port": 443,
        "id": "12345678-1234-1234-1234-123456789abc",
        "aid": 0,
        "net": "tcp",
        "type": "none",
        "host": "example.com",
        "path": "",
        "tls": "tls",
    }


@pytest.fixture(scope="session")
def sample_vless_config():
    """示例VLESS配置"""
    return {
        "type": "vless",
        "name": "VLESS节点",
        "server": "example.com",
        "port": 443,
        "uuid": "12345678-1234-1234-1234-123456789abc",
        "network": "ws",
        "tls": True,
        "security": "tls",
    }


@pytest.fixture(scope="session")
def sample_trojan_config():
    """示例Trojan配置"""
    return {
        "type": "trojan",
        "name": "Trojan节点",
        "server": "example.com",
        "port": 443,
        "password": "test_password",
        "sni": "example.com",
    }


@pytest.fixture(scope="session")
def sample_ss_config():
    """示例Shadowsocks配置"""
    return {
        "type": "ss",
        "name": "SS节点",
        "server": "example.com",
        "port": 8388,
        "cipher": "aes-256-gcm",
        "password": "test_password",
    }


@pytest.fixture(scope="session")
def sample_ssr_config():
    """示例ShadowsocksR配置"""
    return {
        "type": "ssr",
        "name": "SSR节点",
        "server": "example.com",
        "port": 8388,
        "protocol": "origin",
        "cipher": "aes-256-cfb",
        "password": "test_password",
        "obfs": "plain",
    }


@pytest.fixture(scope="session")
def sample_hysteria2_config():
    """示例Hysteria2配置"""
    return {
        "type": "hysteria2",
        "name": "Hysteria2节点",
        "server": "example.com",
        "port": 443,
        "password": "test_password",
        "sni": "example.com",
    }


@pytest.fixture
def mock_requests_session():
    """创建模拟的requests.Session"""
    from unittest.mock import Mock
    session = Mock()
    return session


@pytest.fixture
def mock_response():
    """创建模拟的HTTP响应"""
    from unittest.mock import Mock
    response = Mock()
    response.status_code = 200
    response.text = "测试内容"
    response.content = "测试内容".encode("utf-8")
    response.headers = {"Content-Type": "text/html; charset=utf-8"}
    response.encoding = "utf-8"
    response.raise_for_status = Mock()
    return response


# pytest配置
def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# 测试收集配置
collect_ignore = [
    "venv",
    ".git",
    ".ruff_cache",
    "__pycache__",
]


# 测试输出配置
def pytest_report_header(config):
    """测试报告头部"""
    return f"""
    ==================== 测试配置 ====================
    Python版本: {sys.version}
    项目根目录: {PROJECT_ROOT}
    测试数据目录: {os.path.join(PROJECT_ROOT, 'tests', 'data')}
    =================================================
    """


# 测试失败时的钩子
def pytest_runtest_makereport(item, call):
    """测试失败时的钩子"""
    if call.when == "call" and call.excinfo is not None:
        # 可以在这里添加失败时的处理逻辑
        pass


# 测试完成后的钩子
def pytest_sessionfinish(session, exitstatus):
    """测试完成后的钩子"""
    pass