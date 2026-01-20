#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2RaySE网站节点收集器
使用Playwright进行浏览器自动化，收集v2rayse.com的免费节点
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path

# Check and install playwright if not available
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Installing playwright...")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--break-system-packages",
            "playwright",
        ]
    )
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.async_api import async_playwright

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger


class V2RaySECollector:
    """V2RaySE网站收集器"""

    def __init__(self):
        self.logger = get_logger("v2rayse_collector")
        self.url = "https://www.v2rayse.com/free-node"
        self.result_dir = project_root / "result"
        self.result_file = self.result_dir / "v2rayse.txt"
        self.debug_dir = project_root / "data" / "debug"
        self.debug_dir.mkdir(exist_ok=True)

    async def collect_nodes(self):
        """收集节点的主函数"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Set user agent to avoid blocking
                await page.set_extra_http_headers(
                    {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                )

                self.logger.info(f"访问网站: {self.url}")
                try:
                    await page.goto(
                        self.url, wait_until="domcontentloaded", timeout=60000
                    )
                except:
                    self.logger.warning("networkidle超时，使用domcontentloaded")
                    await page.goto(
                        self.url, wait_until="domcontentloaded", timeout=60000
                    )

                # 保存初始页面截图用于调试
                await page.screenshot(path=str(self.debug_dir / "debug_initial.png"))
                self.logger.info("保存初始页面截图: debug_initial.png")

                # 处理可能的广告弹窗
                try:
                    # Wait for popups to load then try to close them
                    await page.wait_for_timeout(2000)

                    # Try to close various popup types
                    popup_selectors = [
                        ".popup-close",
                        ".modal-close",
                        ".ad-close",
                        '[data-dismiss="modal"]',
                        ".close-button",
                        "#popup-close",
                    ]

                    for selector in popup_selectors:
                        try:
                            close_button = page.locator(selector).first
                            if await close_button.is_visible():
                                await close_button.click()
                                self.logger.info(f"关闭弹窗: {selector}")
                                break
                        except:
                            continue

                except Exception as e:
                    self.logger.warning(f"处理弹窗时出错: {e}")

                # 等待页面加载
                self.logger.info("等待页面加载...")
                await page.wait_for_timeout(10000)  # 直接等待10秒让页面加载

                # 尝试触发任何可能的按钮来加载节点
                try:
                    # 查找可能的加载按钮
                    load_buttons = page.locator(
                        'button:has-text("加载"), button:has-text("刷新"), button:has-text("获取"), button:has-text("开始")'
                    )
                    count = await load_buttons.count()
                    if count > 0:
                        await load_buttons.first.click()
                        self.logger.info("点击了加载按钮")
                        await page.wait_for_timeout(5000)

                except Exception as e:
                    self.logger.warning(f"尝试点击加载按钮失败: {e}")

                # 等待15秒让节点加载
                self.logger.info("等待15秒让节点加载...")
                await page.wait_for_timeout(15000)

                # 保存等待后的页面截图
                await page.screenshot(path=str(self.debug_dir / "debug_after_wait.png"))
                self.logger.info("保存等待后页面截图: debug_after_wait.png")

                # 保存页面HTML内容用于分析
                page_html = await page.content()
                with open(self.debug_dir / "debug_page.html", "w", encoding="utf-8") as f:
                    f.write(page_html)
                self.logger.info("保存页面HTML: debug_page.html")

                # 也保存页面文本内容
                page_text = await page.inner_text("body")
                with open(self.debug_dir / "debug_page_text.txt", "w", encoding="utf-8") as f:
                    f.write(page_text)
                self.logger.info("保存页面文本: debug_page_text.txt")

                # 查找表头的全选复选框
                try:
                    # 表头的全选复选框通常在th元素中
                    # 注意：V2RaySE使用的是自定义复选框（button[role="checkbox"]），不是标准的input[type="checkbox"]
                    select_all_selectors = [
                        'th button[role="checkbox"]',
                        'thead button[role="checkbox"]',
                        '.table-header button[role="checkbox"]',
                        '#table-header button[role="checkbox"]',
                        'button[role="checkbox"][aria-label*="全选"]',
                        'button[role="checkbox"][aria-label*="select"]',
                    ]

                    select_all_clicked = False
                    for selector in select_all_selectors:
                        try:
                            element = page.locator(selector).first
                            if await element.is_visible():
                                await element.click()
                                self.logger.info(f"点击表头全选复选框: {selector}")
                                select_all_clicked = True
                                await page.wait_for_timeout(1000)  # 等待选择完成
                                break
                        except Exception as e:
                            self.logger.debug(f"尝试 {selector} 失败: {e}")
                            continue

                    if not select_all_clicked:
                        # 如果没找到表头复选框，尝试查找页面中的所有复选框并全部勾选
                        all_checkboxes = page.locator('button[role="checkbox"]')
                        count = await all_checkboxes.count()
                        if count > 0:
                            self.logger.info(f"找到 {count} 个自定义复选框，尝试全部勾选")
                            try:
                                # 勾选所有复选框
                                checked_count = 0
                                for i in range(count):
                                    try:
                                        checkbox = all_checkboxes.nth(i)
                                        # 检查是否已勾选，避免重复点击
                                        aria_checked = await checkbox.get_attribute("aria-checked")
                                        if aria_checked == "false":
                                            await checkbox.click()
                                            checked_count += 1
                                            self.logger.debug(f"勾选第 {i} 个复选框")
                                    except Exception as e:
                                        self.logger.debug(f"勾选第 {i} 个复选框失败: {e}")
                                        continue
                                select_all_clicked = True
                                self.logger.info(f"成功勾选 {checked_count} 个复选框（共{count}个）")
                                
                                # 保存勾选后的截图
                                await page.screenshot(path=str(self.debug_dir / "debug_after_check.png"))
                                self.logger.info("保存勾选后页面截图: debug_after_check.png")
                            except Exception as e:
                                self.logger.warning(f"勾选复选框失败: {e}")
                        else:
                            self.logger.warning("未找到任何复选框")

                except Exception as e:
                    self.logger.error(f"选择节点时出错: {e}")

                # 在勾选所有复选框后，点击节点操作按钮
                try:
                    # 点击"节点操作"按钮
                    node_operation_btn = page.locator('button:has-text("节点操作")').first
                    if await node_operation_btn.is_visible():
                        await node_operation_btn.click()
                        self.logger.info("点击节点操作按钮")
                        await page.wait_for_timeout(1000)  # 等待菜单显示
                        
                        # 查找并点击复制按钮
                        copy_selectors = [
                            'button:has-text("复制")',
                            'button:has-text("复制选中")',
                            'a:has-text("复制")',
                            'a:has-text("复制选中")',
                            '[data-action="copy"]',
                            '[data-action="copy-selected"]',
                        ]
                        
                        copy_found = False
                        for selector in copy_selectors:
                            try:
                                copy_btn = page.locator(selector).first
                                if await copy_btn.is_visible():
                                    await copy_btn.click()
                                    self.logger.info(f"点击复制按钮: {selector}")
                                    copy_found = True
                                    await page.wait_for_timeout(2000)  # 等待复制完成
                                    break
                            except Exception as e:
                                self.logger.debug(f"尝试 {selector} 失败: {e}")
                                continue
                        
                        if copy_found:
                            self.logger.info("已成功点击复制按钮")
                            # 保存点击后的截图
                            await page.screenshot(path=str(self.debug_dir / "debug_after_copy.png"))
                            self.logger.info("保存复制后页面截图: debug_after_copy.png")
                        else:
                            self.logger.warning("未找到复制按钮")
                    else:
                        self.logger.warning("未找到节点操作按钮")

                except Exception as e:
                    self.logger.warning(f"查找节点操作按钮时出错: {e}")

                # 等待复制完成
                await page.wait_for_timeout(3000)

                # 提取V2RAY节点数据
                v2ray_content = ""

                try:
                    # 首先尝试从文本区域或结果区域提取
                    content_selectors = [
                        "textarea",
                        "#result",
                        ".result",
                        "#v2ray-content",
                        ".v2ray-content",
                        "pre",
                        ".node-content",
                        "#node-content",
                    ]

                    for selector in content_selectors:
                        try:
                            content_element = page.locator(selector).first
                            if await content_element.is_visible():
                                v2ray_content = await content_element.text_content()
                                if v2ray_content:
                                    self.logger.info(
                                        f"从 {selector} 提取到内容: '{v2ray_content[:100]}...'"
                                    )
                                    if v2ray_content.strip():
                                        break
                                else:
                                    self.logger.info(f"从 {selector} 提取到空内容")
                        except:
                            continue

                    if not v2ray_content:
                        # 如果没找到特定区域，尝试从页面源码中提取节点配置
                        page_content = await page.content()
                        self.logger.info("从页面源码提取节点配置")

                        # 查找可能的节点配置模式
                        import re

                        # 提取各种类型的节点链接
                        node_patterns = [
                            r'vmess://[^\s"<]+',
                            r'vless://[^\s"<]+',
                            r'trojan://[^\s"<]+',
                            r'ss://[^\s"<]+',
                            r'ssr://[^\s"<]+',
                            r'hysteria://[^\s"<]+',
                        ]

                        all_links = []
                        for pattern in node_patterns:
                            links = re.findall(pattern, page_content)
                            all_links.extend(links)

                        if all_links:
                            v2ray_content = "\n".join(all_links)
                            self.logger.info(
                                f"从源码提取到 {len(all_links)} 个节点链接"
                            )
                        else:
                            # 如果还是没找到，尝试解析表格数据生成配置
                            self.logger.info("尝试解析表格数据生成节点配置")

                            # 从页面文本中提取节点信息
                            page_text = await page.inner_text("body")

                            # 解析节点表格 - 改进的解析逻辑
                            # 从页面文本中提取节点信息
                            lines = [
                                line.strip()
                                for line in page_text.split("\n")
                                if line.strip()
                            ]

                            # 查找节点数据的模式
                            # 典型的格式：🇺🇸_US_美国 vless v2.dabache.top 443 操作
                            nodes = []
                            i = 0
                            while i < len(lines):
                                line = lines[i]

                                # 查找以国旗开头的行（节点名称）
                                if (
                                    line.startswith("🇺🇸")
                                    or line.startswith("🇩🇪")
                                    or line.startswith("🇬🇧")
                                    or line.startswith("🇷🇺")
                                    or line.startswith("🇮🇹")
                                    or line.startswith("🇮🇶")
                                    or line.startswith("🇳🇱")
                                    or line.startswith("🇪🇸")
                                    or line.startswith("🇨🇦")
                                    or line.startswith("🇩🇰")
                                    or line.startswith("🇯🇵")
                                    or line.startswith("🇰🇷")
                                    or line.startswith("🇦🇺")
                                    or line.startswith("🇸🇬")
                                    or line.startswith("🇭🇰")
                                ):
                                    # 这是一个节点名称，接下来应该有类型、服务器、端口
                                    node_name = line

                                    # 查找下一行
                                    if i + 1 < len(lines):
                                        next_line = lines[i + 1]
                                        if next_line in [
                                            "vless",
                                            "vmess",
                                            "trojan",
                                            "ss",
                                            "ssr",
                                            "hysteria",
                                        ]:
                                            node_type = next_line

                                            # 查找服务器（通常是下一行）
                                            if i + 2 < len(lines):
                                                server_line = lines[i + 2]
                                                if (
                                                    "." in server_line
                                                    or ":" in server_line
                                                ):
                                                    server = server_line

                                                    # 查找端口（通常是下一行）
                                                    if i + 3 < len(lines):
                                                        port_line = lines[i + 3]
                                                        if port_line.isdigit():
                                                            port = port_line

                                                            nodes.append(
                                                                {
                                                                    "name": node_name,
                                                                    "type": node_type,
                                                                    "server": server,
                                                                    "port": port,
                                                                }
                                                            )

                                                            self.logger.info(
                                                                f"解析到节点: {node_name} {node_type} {server}:{port}"
                                                            )
                                                            i += 4  # 跳过已处理的行
                                                            continue

                                i += 1

                            # 生成V2RAY格式配置
                            if nodes:
                                v2ray_configs = []
                                for node in nodes:
                                    if (
                                        node.get("type")
                                        and node.get("server")
                                        and node.get("port")
                                    ):
                                        if node["type"] == "vless":
                                            config = f"vless://{node['server']}:{node['port']}?type=tcp&security=none#{node.get('name', 'Unknown')}"
                                        elif node["type"] == "vmess":
                                            # vmess需要更多参数，这里简化
                                            config = f"vmess://{node['server']}:{node['port']}#{node.get('name', 'Unknown')}"
                                        elif node["type"] == "ss":
                                            config = f"ss://{node['server']}:{node['port']}#{node.get('name', 'Unknown')}"
                                        else:
                                            config = f"{node['type']}://{node['server']}:{node['port']}#{node.get('name', 'Unknown')}"

                                        v2ray_configs.append(config)

                                if v2ray_configs:
                                    v2ray_content = "\n".join(v2ray_configs)
                                    self.logger.info(
                                        f"从表格解析生成 {len(v2ray_configs)} 个节点配置"
                                    )

                except Exception as e:
                    self.logger.error(f"提取内容时出错: {e}")

                # 关闭浏览器
                await browser.close()

                if v2ray_content:
                    # 确保结果目录存在
                    self.result_dir.mkdir(exist_ok=True)

                    # 保存到文件
                    with open(self.result_file, "w", encoding="utf-8") as f:
                        f.write(v2ray_content.strip())

                    self.logger.info(
                        f"成功保存 {len(v2ray_content.splitlines())} 个节点到 {self.result_file}"
                    )
                    return True
                else:
                    self.logger.error("未获取到任何节点内容")
                    return False

        except Exception as e:
            self.logger.error(f"收集过程出错: {e}")
            import traceback

            traceback.print_exc()
            return False


async def main():
    """主函数"""
    collector = V2RaySECollector()
    success = await collector.collect_nodes()

    if success:
        print("✅ V2RaySE节点收集完成")
        sys.exit(0)
    else:
        print("❌ V2RaySE节点收集失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
