#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果管理器
负责保存收集结果和更新GitHub仓库
"""

import os
import re
import time
from datetime import datetime
from typing import Dict, List, Any

from src.utils.logger import get_logger
from src.utils.file_handler import FileHandler
from src.config.settings import *


class ResultManager:
    """结果管理器 - 处理结果保存和GitHub更新"""

    def __init__(self):
        self.logger = get_logger("result_manager")
        self.file_handler = FileHandler()

    def _clean_node_name(self, node: str) -> str:
        """
        清理节点名称中的广告信息

        Args:
            node: 节点字符串

        Returns:
            清理后的节点字符串
        """
        # 分离节点协议和名称部分
        if '#' in node:
            protocol_part, name_part = node.rsplit('#', 1)
            # URL解码名称部分
            from urllib.parse import unquote
            decoded_name = unquote(name_part)
            
            # 清理广告信息
            # 1. 移除括号内的内容（包括括号）
            cleaned_name = re.sub(r'\([^)]*\)', '', decoded_name)
            
            # 2. 移除 | 后面的内容
            cleaned_name = re.sub(r'\|.*', '', cleaned_name)
            
            # 3. 移除常见的广告关键词和网站名称
            ad_patterns = [
                r'\s*free-nodes',
                r'\s*free\.nodes',
                r'\s*v2clash\.blog',
                r'\s*mibei77\.com',
                r'\s*clashnode\.cc',
                r'\s*clashnodev2ray',
                r'\s*freeclashnode',
                r'\s*freev2raynode',
                r'\s*持续更新',
                r'\s*202\d-\d{1,2}-\d{1,2}',
                r'\s*@[\w.-]+',
                # 移除通用的网站域名广告（包括中文描述前的整个广告文本）
                r'[^：|]+：\s*[\w-]+\.(com|net|org|cn|io|top|xyz|cc|me|tv|us|uk|jp|kr|sg|hk|tw|de|fr|ru|ca|au|in|br|es|it|nl|se|no|fi|dk|pl|cz|hu|ro|bg|gr|pt|ie|at|ch|be|lu|cy|mt|si|sk|hr|ba|mk|al|rs|me|ad|li|mc|sm|va|is|fo|gl|ax|ee|lv|lt|by|ua|md|ge|am|az|kz|uz|tj|kg|tm|mn|af|pk|in|np|bt|bd|lk|mm|th|kh|la|vn|my|sg|id|ph|bn|tw|hk|mo|jp|kr|cn|kp)',
            ]
            
            for pattern in ad_patterns:
                cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE)
            
            # 4. 清理多余空格和特殊符号
            cleaned_name = re.sub(r'\s+', ' ', cleaned_name)
            cleaned_name = cleaned_name.strip(' -|')
            
            # 如果清理后名称为空或太短，使用默认名称
            if len(cleaned_name) < 2:
                cleaned_name = "Node"
            
            # 重新编码名称部分
            from urllib.parse import quote
            encoded_name = quote(cleaned_name)
            
            return f"{protocol_part}#{encoded_name}"
        
        return node

    def save_results(self, results: Dict[str, Any]) -> bool:
        """
        保存收集结果

        Args:
            results: 收集结果字典

        Returns:
            保存是否成功
        """
        try:
            self.logger.info("开始保存收集结果...")

            # 获取日期字符串
            date_str = datetime.now().strftime("%Y%m%d")

            # 创建结果目录
            result_dir = os.path.join("result", date_str)
            os.makedirs(result_dir, exist_ok=True)

            # 保存各个网站的info文件
            all_nodes = []
            for site_key, site_results in results.items():
                if not site_results or not site_results.get("nodes"):
                    continue

                # 保存网站info文件
                self._save_site_info(result_dir, site_key, site_results)

                # 收集所有节点
                all_nodes.extend(site_results["nodes"])

            # 去重并保存总节点文件
            if all_nodes:
                unique_nodes = list(set(all_nodes))

                # 清理节点名称中的广告信息
                cleaned_nodes = [self._clean_node_name(node) for node in unique_nodes]

                # 保存到日期目录
                total_file = os.path.join(result_dir, "nodetotal.txt")
                with open(total_file, "w", encoding="utf-8") as f:
                    for node in cleaned_nodes:
                        f.write(f"{node}\n")

                # 同时保存到根目录的result文件夹
                root_result_dir = "result"
                os.makedirs(root_result_dir, exist_ok=True)
                root_total_file = os.path.join(root_result_dir, "nodetotal.txt")

                with open(root_total_file, "w", encoding="utf-8") as f:
                    for node in cleaned_nodes:
                        f.write(f"{node}\n")

                self.logger.info(
                    f"保存了 {len(cleaned_nodes)} 个去重节点到 {total_file}"
                )
                self.logger.info(f"同时同步保存到 {root_total_file}")
                return True
            else:
                self.logger.warning("没有节点需要保存")
                return False

        except Exception as e:
            self.logger.error(f"保存结果失败: {str(e)}")
            return False

    def _save_site_info(
        self, result_dir: str, site_key: str, site_results: Dict[str, Any]
    ) -> None:
        """保存单个网站的info文件"""
        try:
            info_file = os.path.join(result_dir, f"{site_key}_info.txt")

            with open(info_file, "w", encoding="utf-8") as f:
                f.write(f"# {site_results.get('name', site_key)} 文章和订阅链接\n")
                f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 60 + "\n")
                f.write("\n")

                # 文章链接
                f.write("## 文章链接\n")
                article_url = site_results.get("article_url", "")
                if article_url:
                    f.write(f"{article_url}\n")
                else:
                    f.write("未找到文章链接\n")
                f.write("\n")

                # 订阅链接
                f.write("## 订阅链接\n")
                subscription_links = site_results.get("subscription_links", [])
                if subscription_links:
                    for link in subscription_links:
                        f.write(f"{link}\n")
                else:
                    f.write("未找到订阅链接\n")

            self.logger.debug(f"保存了 {site_key} 的info文件: {info_file}")

        except Exception as e:
            self.logger.error(f"保存 {site_key} 的info文件失败: {str(e)}")

    def update_github(self) -> bool:
        """
        更新GitHub仓库

        Returns:
            更新是否成功
        """
        try:
            self.logger.info("开始更新GitHub仓库...")

            # 检查git是否可用
            try:
                import git
            except ImportError:
                self.logger.warning("git模块不可用，跳过GitHub更新")
                return False

            # 使用当前工作目录作为项目根目录（适用于GitHub Actions）
            project_root = os.getcwd()

            # 初始化git仓库
            repo = git.Repo(project_root)

            # 配置git用户信息
            with repo.config_writer() as cw:
                cw.set_value("user", "email", GIT_EMAIL)
                cw.set_value("user", "name", GIT_NAME)

            # 检查是否有文件需要提交
            if not repo.is_dirty(untracked_files=True):
                self.logger.info("没有文件需要提交")
                return True

            # 添加结果文件
            date_str = datetime.now().strftime("%Y%m%d")
            result_files = [f"result/{date_str}/nodetotal.txt", f"result/{date_str}/"]

            for file_path in result_files:
                if os.path.exists(file_path):
                    repo.index.add([file_path])

            # 创建提交信息
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"更新节点列表 - {update_time}"

            # 提交更改
            repo.index.commit(commit_message)
            self.logger.info(f"提交成功: {commit_message}")

            # 推送到远程仓库
            try:
                origin = repo.remote(name="origin")
                origin.push()
                self.logger.info("推送到远程仓库成功")
            except Exception as e:
                self.logger.warning(f"推送失败: {str(e)}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"GitHub更新失败: {str(e)}")
            return False
