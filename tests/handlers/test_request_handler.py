#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：handlers.request_handler
测试请求处理器的功能
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException, Timeout, ConnectionError

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.handlers.request_handler import RequestHandler
from src.core.exceptions import NetworkError


class TestRequestHandler:
    """请求处理器测试"""

    @pytest.fixture
    def handler(self):
        """创建请求处理器实例"""
        return RequestHandler()

    @pytest.fixture
    def mock_session(self):
        """创建模拟的 requests.Session"""
        session = Mock()
        return session

    @pytest.fixture
    def mock_response(self):
        """创建模拟的响应"""
        response = Mock()
        response.status_code = 200
        response.text = "测试内容"
        response.content = "测试内容".encode("utf-8")
        response.headers = {"Content-Type": "text/html; charset=utf-8"}
        response.raise_for_status = Mock()
        return response

    def test_get_request_success(self, handler, mock_session, mock_response):
        """测试成功的GET请求"""
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", session=mock_session)

        assert response.status_code == 200
        assert response.text == "测试内容"

    def test_get_request_with_headers(self, handler, mock_session, mock_response):
        """测试带请求头的GET请求"""
        headers = {"User-Agent": "test-agent"}
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", headers=headers, session=mock_session)

        assert response.status_code == 200
        mock_session.get.assert_called_once()

    def test_get_request_with_timeout(self, handler, mock_session, mock_response):
        """测试带超时的GET请求"""
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", timeout=10, session=mock_session)

        assert response.status_code == 200

    def test_get_request_timeout_error(self, handler, mock_session):
        """测试超时错误"""
        mock_session.get.side_effect = Timeout("请求超时")

        with pytest.raises(NetworkError):
            handler.get("http://example.com", session=mock_session)

    def test_get_request_connection_error(self, handler, mock_session):
        """测试连接错误"""
        mock_session.get.side_effect = ConnectionError("连接失败")

        with pytest.raises(NetworkError):
            handler.get("http://example.com", session=mock_session)

    def test_get_request_http_error(self, handler, mock_session, mock_response):
        """测试HTTP错误"""
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = RequestException("404 Not Found")
        mock_session.get.return_value = mock_response

        with pytest.raises(NetworkError):
            handler.get("http://example.com", session=mock_session)

    def test_post_request_success(self, handler, mock_session, mock_response):
        """测试成功的POST请求"""
        data = {"key": "value"}
        mock_session.post.return_value = mock_response

        response = handler.post("http://example.com", data=data, session=mock_session)

        assert response.status_code == 200

    def test_post_request_with_json(self, handler, mock_session, mock_response):
        """测试带JSON数据的POST请求"""
        json_data = {"key": "value"}
        mock_session.post.return_value = mock_response

        response = handler.post("http://example.com", json=json_data, session=mock_session)

        assert response.status_code == 200

    def test_post_request_timeout_error(self, handler, mock_session):
        """测试POST请求超时错误"""
        mock_session.post.side_effect = Timeout("请求超时")

        with pytest.raises(NetworkError):
            handler.post("http://example.com", session=mock_session)

    def test_retry_on_failure(self, handler, mock_session, mock_response):
        """测试失败重试"""
        # 第一次失败，第二次成功
        mock_session.get.side_effect = [
            ConnectionError("连接失败"),
            mock_response
        ]

        response = handler.get("http://example.com", max_retries=2, session=mock_session)

        assert response.status_code == 200
        assert mock_session.get.call_count == 2

    def test_retry_exhausted(self, handler, mock_session):
        """测试重试次数耗尽"""
        mock_session.get.side_effect = ConnectionError("连接失败")

        with pytest.raises(NetworkError):
            handler.get("http://example.com", max_retries=3, session=mock_session)

        # 应该尝试了4次（初始1次 + 重试3次）
        assert mock_session.get.call_count == 4

    def test_get_with_session_creation(self, handler):
        """测试自动创建session"""
        with patch('src.core.handlers.request_handler.Session') as mock_session_class:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "测试内容"
            mock_response.raise_for_status = Mock()

            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            response = handler.get("http://example.com")

            assert response.status_code == 200
            mock_session_class.assert_called_once()

    def test_get_with_cookies(self, handler, mock_session, mock_response):
        """测试带cookies的GET请求"""
        cookies = {"session": "test"}
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", cookies=cookies, session=mock_session)

        assert response.status_code == 200

    def test_get_with_proxies(self, handler, mock_session, mock_response):
        """测试带代理的GET请求"""
        proxies = {"http": "http://proxy.example.com:8080"}
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", proxies=proxies, session=mock_session)

        assert response.status_code == 200

    def test_get_with_verify_false(self, handler, mock_session, mock_response):
        """测试禁用SSL验证的GET请求"""
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", verify=False, session=mock_session)

        assert response.status_code == 200

    def test_get_with_allow_redirects_false(self, handler, mock_session, mock_response):
        """测试禁用重定向的GET请求"""
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", allow_redirects=False, session=mock_session)

        assert response.status_code == 200

    def test_get_with_stream(self, handler, mock_session, mock_response):
        """测试流式GET请求"""
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", stream=True, session=mock_session)

        assert response.status_code == 200

    def test_get_with_params(self, handler, mock_session, mock_response):
        """测试带查询参数的GET请求"""
        params = {"page": 1, "limit": 10}
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", params=params, session=mock_session)

        assert response.status_code == 200

    def test_handle_response_encoding(self, handler, mock_session):
        """测试处理响应编码"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = "测试内容".encode("utf-8")
        mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_response.encoding = "utf-8"
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", session=mock_session)

        assert response.encoding == "utf-8"
        assert "测试内容" in response.text

    def test_handle_response_without_encoding(self, handler, mock_session):
        """测试处理没有指定编码的响应"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = "测试内容".encode("utf-8")
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.encoding = None
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response

        response = handler.get("http://example.com", session=mock_session)

        # 应该自动检测编码
        assert response.text is not None

    def test_get_with_retry_delay(self, handler, mock_session, mock_response):
        """测试带延迟的重试"""
        mock_session.get.side_effect = [
            ConnectionError("连接失败"),
            mock_response
        ]

        import time
        with patch('time.sleep') as mock_sleep:
            response = handler.get("http://example.com", max_retries=2, retry_delay=1, session=mock_session)

            assert response.status_code == 200
            mock_sleep.assert_called_once_with(1)

    def test_get_empty_url(self, handler):
        """测试空URL"""
        with pytest.raises(ValueError):
            handler.get("")

    def test_get_invalid_url(self, handler):
        """测试无效URL"""
        with pytest.raises(ValueError):
            handler.get("not-a-url")