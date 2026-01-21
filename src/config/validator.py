#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证器
验证网站配置和基础配置的有效性
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str
    severity: str = "error"  # error, warning, info


class ConfigValidator:
    """配置验证器"""

    # 必需的网站配置字段
    REQUIRED_WEBSITE_FIELDS = ["name", "url", "enabled", "collector_key"]

    # 有效的协议类型
    VALID_PROTOCOLS = ["vmess", "vless", "trojan", "ss", "ssr", "hysteria", "hysteria2", "reality", "socks5"]

    # URL模式
    URL_PATTERN = r'^https?://[^\s/$.?#].[^\s]*$'

    @classmethod
    def validate_website_config(cls, site_key: str, config: Dict[str, Any]) -> List[ValidationError]:
        """
        验证网站配置

        Args:
            site_key: 网站键名
            config: 网站配置字典

        Returns:
            验证错误列表（空列表表示验证通过）
        """
        errors = []

        # 检查必需字段
        for field in cls.REQUIRED_WEBSITE_FIELDS:
            if field not in config:
                errors.append(ValidationError(
                    field=field,
                    message=f"缺少必需字段: {field}",
                    severity="error"
                ))

        # 验证URL
        if "url" in config:
            url = config["url"]
            if not isinstance(url, str):
                errors.append(ValidationError(
                    field="url",
                    message=f"URL必须是字符串类型，当前类型: {type(url)}",
                    severity="error"
                ))
            elif not url.startswith(("http://", "https://")):
                errors.append(ValidationError(
                    field="url",
                    message=f"URL必须以http://或https://开头，当前URL: {url}",
                    severity="error"
                ))

        # 验证enabled字段
        if "enabled" in config:
            enabled = config["enabled"]
            if not isinstance(enabled, bool):
                errors.append(ValidationError(
                    field="enabled",
                    message=f"enabled必须是布尔类型，当前类型: {type(enabled)}",
                    severity="error"
                ))

        # 验证selectors字段（如果存在）
        if "selectors" in config:
            selectors = config["selectors"]
            if not isinstance(selectors, list):
                errors.append(ValidationError(
                    field="selectors",
                    message=f"selectors必须是列表类型，当前类型: {type(selectors)}",
                    severity="error"
                ))
            elif not selectors:
                errors.append(ValidationError(
                    field="selectors",
                    message="selectors列表不能为空",
                    severity="warning"
                ))

        # 验证patterns字段（如果存在）
        if "patterns" in config:
            patterns = config["patterns"]
            if not isinstance(patterns, list):
                errors.append(ValidationError(
                    field="patterns",
                    message=f"patterns必须是列表类型，当前类型: {type(patterns)}",
                    severity="error"
                ))
            elif not patterns:
                errors.append(ValidationError(
                    field="patterns",
                    message="patterns列表不能为空",
                    severity="warning"
                ))

        return errors

    @classmethod
    def validate_base_config(cls, config: Dict[str, Any]) -> List[ValidationError]:
        """
        验证基础配置

        Args:
            config: 基础配置字典

        Returns:
            验证错误列表（空列表表示验证通过）
        """
        errors = []

        # 验证REQUEST_TIMEOUT
        if "REQUEST_TIMEOUT" in config:
            timeout = config["REQUEST_TIMEOUT"]
            if not isinstance(timeout, (int, float)):
                errors.append(ValidationError(
                    field="REQUEST_TIMEOUT",
                    message=f"REQUEST_TIMEOUT必须是数字类型，当前类型: {type(timeout)}",
                    severity="error"
                ))
            elif timeout <= 0:
                errors.append(ValidationError(
                    field="REQUEST_TIMEOUT",
                    message=f"REQUEST_TIMEOUT必须大于0，当前值: {timeout}",
                    severity="error"
                ))
            elif timeout > 300:
                errors.append(ValidationError(
                    field="REQUEST_TIMEOUT",
                    message=f"REQUEST_TIMEOUT值过大（{timeout}秒），建议不超过300秒",
                    severity="warning"
                ))

        # 验证REQUEST_RETRY
        if "REQUEST_RETRY" in config:
            retry = config["REQUEST_RETRY"]
            if not isinstance(retry, int):
                errors.append(ValidationError(
                    field="REQUEST_RETRY",
                    message=f"REQUEST_RETRY必须是整数类型，当前类型: {type(retry)}",
                    severity="error"
                ))
            elif retry < 0:
                errors.append(ValidationError(
                    field="REQUEST_RETRY",
                    message=f"REQUEST_RETRY不能为负数，当前值: {retry}",
                    severity="error"
                ))
            elif retry > 10:
                errors.append(ValidationError(
                    field="REQUEST_RETRY",
                    message=f"REQUEST_RETRY值过大（{retry}次），建议不超过10次",
                    severity="warning"
                ))

        # 验证REQUEST_DELAY
        if "REQUEST_DELAY" in config:
            delay = config["REQUEST_DELAY"]
            if not isinstance(delay, (int, float)):
                errors.append(ValidationError(
                    field="REQUEST_DELAY",
                    message=f"REQUEST_DELAY必须是数字类型，当前类型: {type(delay)}",
                    severity="error"
                ))
            elif delay < 0:
                errors.append(ValidationError(
                    field="REQUEST_DELAY",
                    message=f"REQUEST_DELAY不能为负数，当前值: {delay}",
                    severity="error"
                ))

        # 验证MIN_NODE_LENGTH
        if "MIN_NODE_LENGTH" in config:
            min_length = config["MIN_NODE_LENGTH"]
            if not isinstance(min_length, int):
                errors.append(ValidationError(
                    field="MIN_NODE_LENGTH",
                    message=f"MIN_NODE_LENGTH必须是整数类型，当前类型: {type(min_length)}",
                    severity="error"
                ))
            elif min_length < 10:
                errors.append(ValidationError(
                    field="MIN_NODE_LENGTH",
                    message=f"MIN_NODE_LENGTH值过小（{min_length}），建议至少10个字符",
                    severity="warning"
                ))

        # 验证SUPPORTED_PROTOCOLS
        if "SUPPORTED_PROTOCOLS" in config:
            protocols = config["SUPPORTED_PROTOCOLS"]
            if not isinstance(protocols, list):
                errors.append(ValidationError(
                    field="SUPPORTED_PROTOCOLS",
                    message=f"SUPPORTED_PROTOCOLS必须是列表类型，当前类型: {type(protocols)}",
                    severity="error"
                ))
            else:
                invalid_protocols = [p for p in protocols if p not in cls.VALID_PROTOCOLS]
                if invalid_protocols:
                    errors.append(ValidationError(
                        field="SUPPORTED_PROTOCOLS",
                        message=f"包含无效的协议类型: {invalid_protocols}，有效类型: {cls.VALID_PROTOCOLS}",
                        severity="warning"
                    ))

        return errors

    @classmethod
    def validate_all(cls, websites: Dict[str, Dict[str, Any]], base_config: Dict[str, Any]) -> Dict[str, List[ValidationError]]:
        """
        验证所有配置

        Args:
            websites: 网站配置字典
            base_config: 基础配置字典

        Returns:
            包含所有验证错误的字典，键为配置类型（"websites"或"base"）
        """
        all_errors = {
            "websites": [],
            "base": []
        }

        # 验证网站配置
        for site_key, site_config in websites.items():
            errors = cls.validate_website_config(site_key, site_config)
            if errors:
                for error in errors:
                    error.field = f"{site_key}.{error.field}"
                all_errors["websites"].extend(errors)

        # 验证基础配置
        base_errors = cls.validate_base_config(base_config)
        all_errors["base"].extend(base_errors)

        return all_errors

    @classmethod
    def print_validation_errors(cls, errors: Dict[str, List[ValidationError]]) -> None:
        """
        打印验证错误

        Args:
            errors: 验证错误字典
        """
        total_errors = 0
        total_warnings = 0

        for config_type, error_list in errors.items():
            if not error_list:
                continue

            print(f"\n{'='*60}")
            print(f"{config_type.upper()} 配置验证结果")
            print(f"{'='*60}")

            error_count = sum(1 for e in error_list if e.severity == "error")
            warning_count = sum(1 for e in error_list if e.severity == "warning")

            total_errors += error_count
            total_warnings += warning_count

            for error in error_list:
                if error.severity == "error":
                    print(f"❌ [ERROR] {error.field}: {error.message}")
                elif error.severity == "warning":
                    print(f"⚠️  [WARNING] {error.field}: {error.message}")
                else:
                    print(f"ℹ️  [INFO] {error.field}: {error.message}")

        if total_errors == 0 and total_warnings == 0:
            print("\n✅ 所有配置验证通过！")
        else:
            print(f"\n{'='*60}")
            print(f"总计: {total_errors} 个错误, {total_warnings} 个警告")
            print(f"{'='*60}")

            if total_errors > 0:
                print("\n❌ 配置验证失败，请修复错误后重试")
            else:
                print("\n⚠️  配置验证通过，但存在警告，建议修复")