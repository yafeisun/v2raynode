#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序入口 - 插件化架构
本地测试和调试用，支持自动发现和加载所有网站收集器
GitHub更新功能请在GitHub Actions中使用
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.collector_manager import CollectorManager
from src.utils.logger import get_logger


def main():
    """主函数 - 命令行接口和任务调度（两阶段收集流程）"""
    import argparse

    parser = argparse.ArgumentParser(description="插件化免费V2Ray节点收集器")
    parser.add_argument("--sites", nargs="+", help="指定要收集的网站")
    parser.add_argument("--list-sites", action="store_true", help="列出所有可用网站")
    parser.add_argument("--plugin-info", action="store_true", help="显示插件信息")
    parser.add_argument(
        "--update-github",
        action="store_true",
        help="⚠️  警告: 这将在本地提交代码到GitHub! 仅在CI环境或明确需要时使用",
    )

    args = parser.parse_args()

    logger = get_logger("main")

    try:
        # 创建收集器管理器
        collector_manager = CollectorManager()

        # 列出可用网站
        if args.list_sites:
            available_sites = collector_manager.get_available_sites()
            print("可用网站:")
            for site in available_sites:
                print(f"  - {site}")
            return

        # 显示插件信息
        if args.plugin_info:
            info = collector_manager.get_plugin_info()
            print("插件信息:")
            for site, data in info.items():
                print(f"  {site}:")
                print(f"    类名: {data['collector_class']}")
                print(f"    模块: {data['module']}")
                print(f"    描述: {data['description']}")
                print(f"    启用: {data['enabled']}")
            return

        # 执行节点收集（两阶段流程）
        logger.info("开始执行节点收集任务（两阶段流程）...")
        results = collector_manager.collect_all_sites(args.sites)

        if not results:
            logger.error("收集失败，没有获取到任何结果")
            return

        # 保存结果到本地文件
        from src.core.result_manager import ResultManager

        result_manager = ResultManager()
        success = result_manager.save_results(results)

        if success:
            logger.info("节点收集任务完成，结果已保存到本地")
        else:
            logger.error("结果保存失败")

        # GitHub更新（仅在明确指定时执行）
        if args.update_github:
            logger.warning("⚠️  正在执行GitHub更新操作...")
            logger.warning("⚠️  这将在本地提交代码到GitHub仓库!")
            logger.warning("⚠️  请确保你知道自己在做什么!")

            if result_manager.update_github():
                logger.info("✅ GitHub更新完成")
            else:
                logger.error("❌ GitHub更新失败")

    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
