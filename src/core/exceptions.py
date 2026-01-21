#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一异常类
定义项目中所有自定义异常类型
"""


class V2RayNodeException(Exception):
    """基础异常类"""
    pass


class ConfigError(V2RayNodeException):
    """配置错误"""
    pass


class NetworkError(V2RayNodeException):
    """网络请求错误"""
    pass


class RequestTimeoutError(NetworkError):
    """请求超时错误"""
    pass


class ConnectionError(NetworkError):
    """连接错误"""
    pass


class ProxyError(NetworkError):
    """代理错误"""
    pass


class ParseError(V2RayNodeException):
    """解析错误"""
    pass


class SubscriptionParseError(ParseError):
    """订阅解析错误"""
    pass


class NodeParseError(ParseError):
    """节点解析错误"""
    pass


class ArticleNotFoundError(V2RayNodeException):
    """文章未找到错误"""
    pass


class ArticleLinkNotFoundError(ArticleNotFoundError):
    """文章链接未找到错误"""
    pass


class SubscriptionLinkNotFoundError(ArticleNotFoundError):
    """订阅链接未找到错误"""
    pass


class NodeNotFoundError(V2RayNodeException):
    """节点未找到错误"""
    pass


class ProtocolConversionError(V2RayNodeException):
    """协议转换错误"""
    pass


class InvalidNodeError(V2RayNodeException):
    """无效节点错误"""
    pass


class CollectorError(V2RayNodeException):
    """收集器错误"""
    pass


class CollectorDisabledError(CollectorError):
    """收集器已禁用错误"""
    pass


class CollectorTimeoutError(CollectorError):
    """收集器超时错误"""
    pass


class ValidationError(V2RayNodeException):
    """验证错误"""
    pass


class ConfigValidationError(ValidationError):
    """配置验证错误"""
    pass


class NodeValidationError(ValidationError):
    """节点验证错误"""
    pass