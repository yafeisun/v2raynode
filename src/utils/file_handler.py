#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理工具
"""

import os
import json
from datetime import datetime
from src.utils.logger import get_logger
from src.config.settings import (
    NODELIST_FILE, 
    NODELIST_HK_FILE, 
    WEBPAGE_LINKS_FILE, 
    SUBSCRIPTION_FILE,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR
)

class FileHandler:
    """文件处理工具类"""
    
    def __init__(self):
        self.logger = get_logger("file_handler")
        
        # 确保目录存在
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    def save_nodes(self, nodes, filepath, date_suffix=None):
        """保存节点到文件"""
        try:
            # 确定文件路径
            if date_suffix:
                # 按日期创建子目录: result/20251223/
                date_dir = f"result/{date_suffix}"
                os.makedirs(date_dir, exist_ok=True)
                # 区分不同类型的节点文件
                if 'nodelist' in filepath:
                    filepath = os.path.join(date_dir, "nodelist.txt")
                elif 'nodetotal' in filepath:
                    filepath = os.path.join(date_dir, "nodetotal.txt")
                else:
                    # 其他文件保持原有逻辑
                    filepath = filepath.replace('.txt', f'_{date_suffix}.txt')
            else:
                # 保存到根目录，确保result目录存在
                result_dir = "result"
                os.makedirs(result_dir, exist_ok=True)
                # 如果是节点文件，确保使用正确的文件名
                if 'nodelist' in filepath:
                    filepath = os.path.join(result_dir, "nodelist.txt")
                elif 'nodetotal' in filepath:
                    filepath = os.path.join(result_dir, "nodetotal.txt")
                # 其他文件保持原路径
                
            with open(filepath, 'w', encoding='utf-8') as f:
                for node in nodes:
                    f.write(f"{node}\n")
            
            self.logger.info(f"节点已保存到 {filepath}，共 {len(nodes)} 个节点")
            return True
            
        except Exception as e:
            self.logger.error(f"保存节点失败: {str(e)}")
            return False

    def save_nodes_classified(self, nodes):
        """按地区分类保存节点到不同文件"""
        try:
            from .region_detector import RegionDetector
            detector = RegionDetector()
            
            # 分类节点
            classified_nodes = detector.classify_nodes(nodes)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(NODELIST_FILE), exist_ok=True)
            
            # 保存其他节点
            other_nodes = classified_nodes['OTHER']
            with open(NODELIST_FILE, 'w', encoding='utf-8') as f:
                for node in other_nodes:
                    f.write(node + '\n')
            
            # 保存香港节点
            hk_nodes = classified_nodes['HK']
            with open(NODELIST_HK_FILE, 'w', encoding='utf-8') as f:
                for node in hk_nodes:
                    f.write(node + '\n')
            
            self.logger.info(f"节点分类保存完成:")
            self.logger.info(f"  - 其他节点: {len(other_nodes)} 个 -> {NODELIST_FILE}")
            self.logger.info(f"  - 香港节点: {len(hk_nodes)} 个 -> {NODELIST_HK_FILE}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"分类保存节点失败: {str(e)}")
            return False    
    def load_nodes_from_file(self, filename=None, date_suffix=None):
        """从文件加载节点"""
        try:
            if filename is None:
                filename = NODELIST_FILE
            
            # 如果指定了日期后缀，使用新的目录结构
            if date_suffix:
                if 'nodelist' in filename:
                    filename = f"result/{date_suffix}/nodelist.txt"
                elif 'nodetotal' in filename:
                    filename = f"result/{date_suffix}/nodetotal.txt"
                else:
                    filename = filename.replace('.txt', f'_{date_suffix}.txt')
            
            if not os.path.exists(filename):
                self.logger.warning(f"文件不存在: {filename}")
                return []
            
            nodes = []
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    node = line.strip()
                    if node:
                        nodes.append(node)
            
            self.logger.info(f"从 {filename} 加载了 {len(nodes)} 个节点")
            return nodes
            
        except Exception as e:
            self.logger.error(f"加载节点失败: {str(e)}")
            return []
    
    def save_nodes_with_metadata(self, nodes, source_info=None):
        """保存节点及元数据"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            metadata_file = os.path.join(PROCESSED_DATA_DIR, f"nodes_{timestamp}.json")
            
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "total_nodes": len(nodes),
                "sources": source_info or {},
                "nodes": nodes
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"节点元数据已保存到 {metadata_file}")
            return metadata_file
            
        except Exception as e:
            self.logger.error(f"保存节点元数据失败: {str(e)}")
            return None
    
    def backup_nodes(self, nodes):
        """备份节点"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(PROCESSED_DATA_DIR, f"backup_{timestamp}.txt")
            
            return self.save_nodes_to_file(nodes, backup_file)
            
        except Exception as e:
            self.logger.error(f"备份节点失败: {str(e)}")
            return False
    
    def clean_old_backups(self, days=7):
        """清理旧备份文件"""
        try:
            import time
            
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 3600)
            
            removed_count = 0
            for filename in os.listdir(PROCESSED_DATA_DIR):
                if filename.startswith("backup_") and filename.endswith(".txt"):
                    filepath = os.path.join(PROCESSED_DATA_DIR, filename)
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
                        removed_count += 1
                        self.logger.info(f"删除旧备份: {filename}")
            
            if removed_count > 0:
                self.logger.info(f"清理了 {removed_count} 个旧备份文件")
            
        except Exception as e:
            self.logger.error(f"清理旧备份失败: {str(e)}")
    
    def get_file_stats(self, filename=None):
        """获取文件统计信息"""
        try:
            if filename is None:
                filename = NODELIST_FILE
            
            if not os.path.exists(filename):
                return None
            
            stat = os.stat(filename)
            
            with open(filename, 'r', encoding='utf-8') as f:
                lines = sum(1 for _ in f)
            
            return {
                "file": filename,
                "size": stat.st_size,
                "lines": lines,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"获取文件统计失败: {str(e)}")
            return None
    
    def save_webpage_links(self, articles_with_source, date_suffix=None):
        """保存文章链接到文件"""
        try:
            # 只按日期保存，不再保存到根目录
            if date_suffix:
                # 按日期创建子目录: result/20251223/webpage.txt
                date_dir = f"result/{date_suffix}"
                os.makedirs(date_dir, exist_ok=True)
                filepath = os.path.join(date_dir, "webpage.txt")
            else:
                # 如果没有日期后缀，不保存到根目录
                self.logger.info("未指定日期后缀，跳过保存文章链接到根目录")
                return True
                
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# 各网站最新文章链接\n")
                f.write(f"# 收集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                if date_suffix:
                    f.write(f"# 目标日期: {date_suffix}\n")
                f.write(f"# 总网站数: {len(articles_with_source)}\n")
                f.write("=" * 80 + "\n\n")
                
                for article in articles_with_source:
                    f.write(f"# {article['website_name']}\n")
                    f.write(f"{article['article_url']}\n")
                    f.write("-" * 60 + "\n")
            
            self.logger.info(f"文章链接已保存到 {filepath}，共 {len(articles_with_source)} 个网站")
            return True
            
        except Exception as e:
            self.logger.error(f"保存文章链接失败: {str(e)}")
            return False
    
    def load_existing_articles(self, date_suffix=None):
        """加载现有的文章链接缓存"""
        try:
            # 确定文件路径
            if date_suffix:
                # 按日期查找: result/20251223/webpage.txt
                filepath = f"result/{date_suffix}/webpage.txt"
            else:
                # 默认路径
                filepath = WEBPAGE_LINKS_FILE
            
            if not os.path.exists(filepath):
                self.logger.debug(f"文章缓存文件不存在: {filepath}")
                return {}
            
            articles = {}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            sections = content.split('------------------------------------------------------------')
            for section in sections:
                lines = section.strip().split('\n')
                website_name = None
                article_url = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('# ') and not line.startswith('===') and not line.startswith('各网站'):
                        website_name = line.replace('#', '').strip()
                    elif line.startswith('https://') and not line.startswith('#') and website_name:
                        article_url = line.strip()
                        if website_name and article_url:
                            articles[website_name] = article_url
                            
            self.logger.info(f"从缓存加载了 {len(articles)} 个文章链接")
            return articles
            
        except Exception as e:
            self.logger.error(f"加载文章缓存失败: {str(e)}")
            return {}
    
    def load_existing_subscriptions(self, date_suffix=None):
        """加载现有的订阅链接缓存"""
        try:
            # 确定文件路径
            if date_suffix:
                # 按日期查找: result/20251223/subscription.txt
                filepath = f"result/{date_suffix}/subscription.txt"
            else:
                # 默认路径
                filepath = SUBSCRIPTION_FILE
            
            if not os.path.exists(filepath):
                self.logger.debug(f"订阅缓存文件不存在: {filepath}")
                return {}
            
            subscriptions = {}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            sections = content.split('------------------------------------------------------------')
            for section in sections:
                lines = section.strip().split('\n')
                website_name = None
                article_url = None
                links = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('# ') and not line.startswith('===') and '文章链接:' not in line and '链接数:' not in line:
                        website_name = line.replace('#', '').strip()
                    elif line.startswith('# 文章链接:'):
                        if '文章链接: None' not in line:
                            article_url = line.split('文章链接:')[1].strip()
                    elif line.startswith('https://') and not line.startswith('#'):
                        links.append(line)
                
                if website_name and article_url and links:
                    key = f"{website_name}_{article_url}"
                    subscriptions[key] = links
                    
            self.logger.info(f"从缓存加载了 {len(subscriptions)} 个订阅链接组")
            return subscriptions
            
        except Exception as e:
            self.logger.error(f"加载订阅缓存失败: {str(e)}")
            return {}
    
    def save_subscription_links(self, v2ray_links_with_source, date_suffix=None):
        """保存V2Ray订阅链接到文件"""
        try:
            # 只按日期保存，不再保存到根目录
            if date_suffix:
                # 按日期创建子目录: result/20251223/subscription.txt
                date_dir = f"result/{date_suffix}"
                os.makedirs(date_dir, exist_ok=True)
                filepath = os.path.join(date_dir, "subscription.txt")
            else:
                # 如果没有日期后缀，不保存到根目录
                self.logger.info("未指定日期后缀，跳过保存订阅链接到根目录")
                return True
                
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# V2Ray订阅链接收集结果\n")
                f.write(f"# 收集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                if date_suffix:
                    f.write(f"# 目标日期: {date_suffix}\n")
                f.write(f"# 总链接数: {len(v2ray_links_with_source)}\n")
                f.write("=" * 80 + "\n\n")
                
                # 按网站分组
                website_links = {}
                for link_info in v2ray_links_with_source:
                    source = link_info['source']
                    if source not in website_links:
                        website_links[source] = []
                    website_links[source].append(link_info)
                
                for website, links in website_links.items():
                    f.write(f"# {website}\n")
                    f.write(f"# 文章链接: {links[0]['source_url']}\n")
                    f.write(f"# 链接数: {len(links)}\n")
                    
                    # 检查是否有有效链接
                    valid_links = [link['url'] for link in links if link['url'] != '# 无V2Ray订阅链接']
                    
                    if valid_links:
                        for link in valid_links:
                            f.write(f"{link}\n")
                    else:
                        f.write("# 无V2Ray订阅链接\n")
                    
                    f.write("-" * 60 + "\n")
            
            self.logger.info(f"V2Ray订阅链接已保存到 {filepath}，共 {len(v2ray_links_with_source)} 个记录")
            return True
            
        except Exception as e:
            self.logger.error(f"保存V2Ray订阅链接失败: {str(e)}")
            return False
    
    def load_v2ray_links(self, filename=None):
        """从文件加载V2Ray订阅链接"""
        try:
            if filename is None:
                filename = SUBSCRIPTION_FILE
            
            if not os.path.exists(filename):
                self.logger.warning(f"V2Ray订阅链接文件不存在: {filename}")
                return []
            
            links = []
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    link = line.strip()
                    if link and not link.startswith('#') and link.startswith('https://'):
                        links.append(link)
            
            self.logger.info(f"从 {filename} 加载了 {len(links)} 个V2Ray订阅链接")
            return links
            
        except Exception as e:
            self.logger.error(f"加载V2Ray订阅链接失败: {str(e)}")
            return []
    
    def sync_latest_to_root(self, date_suffix):
        """同步最新一天的节点数据到根目录"""
        try:
            # 确保result目录存在
            result_dir = "result"
            os.makedirs(result_dir, exist_ok=True)
            
            # 同步测速前节点 (nodetotal.txt)
            nodetotal_src = f"result/{date_suffix}/nodetotal.txt"
            nodetotal_dst = f"result/nodetotal.txt"
            
            if os.path.exists(nodetotal_src):
                import shutil
                shutil.copy2(nodetotal_src, nodetotal_dst)
                self.logger.info(f"已同步测速前节点: {nodetotal_src} -> {nodetotal_dst}")
            else:
                self.logger.warning(f"测速前节点文件不存在: {nodetotal_src}")
            
            # 同步测速后节点 (nodelist.txt)
            nodelist_src = f"result/{date_suffix}/nodelist.txt"
            nodelist_dst = f"result/nodelist.txt"
            
            if os.path.exists(nodelist_src):
                import shutil
                shutil.copy2(nodelist_src, nodelist_dst)
                self.logger.info(f"已同步测速后节点: {nodelist_src} -> {nodelist_dst}")
            else:
                self.logger.warning(f"测速后节点文件不存在: {nodelist_src}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"同步最新数据到根目录失败: {str(e)}")
            return False
    
    def clean_root_temp_files(self):
        """清理根目录下的临时文件和中间结果"""
        try:
            files_to_remove = [
                "result/webpage.txt",
                "result/subscription.txt"
            ]
            
            removed_count = 0
            for filepath in files_to_remove:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    self.logger.info(f"已删除临时文件: {filepath}")
                    removed_count += 1
            
            # 清理旧的测试文件
            result_dir = "result"
            if os.path.exists(result_dir):
                for filename in os.listdir(result_dir):
                    filepath = os.path.join(result_dir, filename)
                    if (os.path.isfile(filepath) and 
                        (filename.endswith('_test.txt') or 
                         filename.endswith('_temp.txt') or
                         filename.endswith('_backup.txt') or
                         filename.startswith('test_') or
                         'temp_' in filename)):
                        os.remove(filepath)
                        self.logger.info(f"已删除测试文件: {filepath}")
                        removed_count += 1
            
            self.logger.info(f"清理完成，共删除 {removed_count} 个临时文件")
            return True
            
        except Exception as e:
            self.logger.error(f"清理临时文件失败: {str(e)}")
            return False