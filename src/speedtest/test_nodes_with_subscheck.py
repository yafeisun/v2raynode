#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点测速脚本 - 12小时定时运行模式，使用subs-check进行真实的代理测试

优化策略：
1. 每12小时运行一次，避免过度消耗GitHub Actions资源
2. 参考SubsCheck-Win-GUI标准配置，平衡速度与稳定性
3. 两阶段测试：连通性 + 媒体检测
4. 智能超时管理，避免进程卡死
"""

import sys
import os
import subprocess
import time
import re
import yaml
from typing import List, Dict, Any, Tuple

# 添加项目根目录到路径
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.utils.logger import get_logger
from src.speedtest.intelligent_timeout import (
    IntelligentTimeoutManager,
    PerformanceMonitor,
    ConcurrencyController,
)


class SubsCheckTester:
    """使用subs-check进行节点测试"""

    def __init__(self, project_root: str | None = None):
        """初始化测试器"""
        self.logger = get_logger("subscheck_tester")

        # 设置项目根目录
        if project_root is None:
            # 计算项目根目录：从 src/cli/speedtest/test_nodes_with_subscheck.py 向上3级
            self.project_root = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
        else:
            self.project_root = project_root

        # 路径配置
        self.subscheck_dir = os.path.join(self.project_root, "tools", "subscheck")
        self.binary_path = os.path.join(self.subscheck_dir, "bin", "subs-check")
        self.config_file = os.path.join(self.subscheck_dir, "config", "config.yaml")
        self.output_dir = os.path.join(self.project_root, "result", "output")
        self.output_file = os.path.join(self.output_dir, "all.yaml")

        # 进程
        self.process: subprocess.Popen = None  # type: ignore

        # HTTP服务器
        self.http_server = None
        self.http_server_port = 8888
        self.http_server_process = None

        # 智能管理器
        self.timeout_manager = IntelligentTimeoutManager()
        self.performance_monitor = PerformanceMonitor()
        self.concurrency_controller = ConcurrencyController()

    def start_http_server(self) -> bool:
        """启动HTTP服务器"""
        try:
            print(f"🌐 启动HTTP服务器，端口: {self.http_server_port}", flush=True)
            self.logger.info(f"启动HTTP服务器，端口: {self.http_server_port}")

            # 启动HTTP服务器
            print(
                f"🚀 执行命令: python3 -m http.server {self.http_server_port}",
                flush=True,
            )
            self.http_server_process = subprocess.Popen(
                [
                    "python3",
                    "-m",
                    "http.server",
                    str(self.http_server_port),
                    "--directory",
                    self.project_root,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # 等待服务器启动（增加等待时间确保完全启动）
            import time

            print(f"⏳ 等待HTTP服务器启动完成...", flush=True)
            time.sleep(3)  # 减少等待时间，添加进度反馈
            print(f"🔍 检查HTTP服务器状态...", flush=True)
            time.sleep(2)

            # 检查服务器是否成功启动
            if self.http_server_process.poll() is None:
                print(
                    f"✅ HTTP服务器启动成功: http://127.0.0.1:{self.http_server_port}",
                    flush=True,
                )
                self.logger.info(
                    f"HTTP服务器启动成功: http://127.0.0.1:{self.http_server_port}"
                )
                return True
            else:
                self.logger.error("HTTP服务器启动失败")
                return False

        except Exception as e:
            self.logger.error(f"启动HTTP服务器失败: {str(e)}")
            return False

    def stop_http_server(self):
        """停止HTTP服务器"""
        if self.http_server_process:
            try:
                self.http_server_process.terminate()
                self.http_server_process.wait(timeout=5)
                self.logger.info("HTTP服务器已停止")
            except:
                self.http_server_process.kill()
            self.http_server_process = None

        # HTTP服务器
        self.http_server = None
        self.http_server_port = 8888
        self.http_server_process = None

    def install_subscheck(self) -> bool:
        """安装subs-check工具"""
        try:
            self.logger.info("开始安装subs-check工具...")
            print("🔧 开始安装subs-check工具...", flush=True)

            # 创建目录
            bin_dir = os.path.join(self.subscheck_dir, "bin")
            os.makedirs(bin_dir, exist_ok=True)
            os.makedirs(os.path.join(self.subscheck_dir, "config"), exist_ok=True)
            os.makedirs(self.output_dir, exist_ok=True)

            # 检查是否已经存在
            if os.path.exists(self.binary_path):
                print(f"✅ subs-check已存在: {self.binary_path}", flush=True)
                # 测试是否可用
                try:
                    import subprocess

                    result = subprocess.run(
                        [self.binary_path, "--help"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        print("✅ subs-check二进制文件可用", flush=True)
                        return True
                    else:
                        print(f"⚠️  subs-check二进制文件损坏，重新安装", flush=True)
                except Exception as e:
                    print(f"⚠️  subs-check测试失败，重新安装: {e}", flush=True)

            # 检测系统架构
            import platform

            system = platform.system().lower()
            machine = platform.machine().lower()

            print(f"🔍 系统信息: {system} {machine}", flush=True)

            # 确定下载URL
            if system == "linux":
                if machine in ["x86_64", "amd64"]:
                    download_url = "https://github.com/beck-8/subs-check/releases/latest/download/subs-check_Linux_x86_64.tar.gz"
                elif machine in ["aarch64", "arm64"]:
                    download_url = "https://github.com/beck-8/subs-check/releases/latest/download/subs-check_Linux_arm64.tar.gz"
                else:
                    print(f"❌ 不支持的架构: {machine}", flush=True)
                    self.logger.error(f"不支持的架构: {machine}")
                    return False
            else:
                print(f"❌ 不支持的操作系统: {system}", flush=True)
                self.logger.error(f"不支持的操作系统: {system}")
                return False

            print(f"📥 下载URL: {download_url}", flush=True)
            self.logger.info(f"下载URL: {download_url}")

            # 下载文件
            tar_file = os.path.join(bin_dir, "subs-check.tar.gz")

            import requests

            print("🌐 下载subs-check...", flush=True)
            self.logger.info("下载subs-check...")

            try:
                response = requests.get(download_url, stream=True, timeout=60)
                response.raise_for_status()
                print(f"✅ HTTP响应: {response.status_code}", flush=True)
            except Exception as e:
                print(f"❌ 下载失败: {e}", flush=True)
                self.logger.error(f"下载失败: {e}")
                return False

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            print(f"📦 文件大小: {total_size // 1024 // 1024}MB", flush=True)

            with open(tar_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # 每下载10MB显示一次进度
                        if (
                            downloaded % (10 * 1024 * 1024) == 0
                            or downloaded == total_size
                        ):
                            progress = (
                                (downloaded / total_size * 100) if total_size > 0 else 0
                            )
                            print(
                                f"📊 下载进度: {progress:.1f}% ({downloaded // 1024 // 1024}MB)",
                                flush=True,
                            )

            print("✅ 下载完成", flush=True)

            # 解压文件
            print("📂 解压subs-check...", flush=True)
            self.logger.info("解压文件...")

            try:
                import tarfile

                with tarfile.open(tar_file, "r:gz") as tar:
                    members = tar.getmembers()
                    print(f"📋 压缩包包含 {len(members)} 个文件", flush=True)

                    for i, member in enumerate(members):
                        tar.extract(member, bin_dir)
                        # 显示解压进度
                        if i % 5 == 0 or i == len(members) - 1:
                            print(
                                f"📋 解压进度: {i + 1}/{len(members)} 文件", flush=True
                            )

                print("✅ 解压完成", flush=True)
            except Exception as e:
                print(f"❌ 解压失败: {e}", flush=True)
                self.logger.error(f"解压失败: {e}")
                return False

            # 清理下载文件
            try:
                os.remove(tar_file)
                print("🧹 清理下载文件", flush=True)
                self.logger.info("清理下载文件")
            except:
                pass

            # 查找并设置执行权限
            binary_found = False
            extracted_files = os.listdir(bin_dir)
            print(f"📁 解压后的文件: {extracted_files}", flush=True)

            for file in extracted_files:
                if file == "subs-check":
                    binary_path = os.path.join(bin_dir, file)
                    os.chmod(binary_path, 0o755)
                    print(f"🔐 设置执行权限: {binary_path}", flush=True)
                    self.logger.info(f"设置执行权限: {binary_path}")
                    binary_found = True
                    break

            if not binary_found:
                print("❌ 未找到subs-check二进制文件", flush=True)
                self.logger.error("未找到subs-check二进制文件")
                return False

            # 验证安装
            if os.path.exists(self.binary_path):
                print("✅ 二进制文件存在，测试可用性...", flush=True)
                try:
                    import subprocess

                    result = subprocess.run(
                        [self.binary_path, "--help"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        print("✅ subs-check安装成功并可用", flush=True)
                        self.logger.info(f"subs-check安装成功: {self.binary_path}")
                        return True
                    else:
                        print(f"❌ subs-check测试失败: {result.stderr}", flush=True)
                        self.logger.error(f"subs-check测试失败: {result.stderr}")
                        return False
                except Exception as e:
                    print(f"❌ subs-check测试异常: {e}", flush=True)
                    self.logger.error(f"subs-check测试异常: {e}")
                    return False
            else:
                print(
                    f"❌ subs-check安装失败: 二进制文件不存在 {self.binary_path}",
                    flush=True,
                )
                self.logger.error("subs-check安装失败: 二进制文件不存在")
                return False

        except Exception as e:
            print(f"❌ subs-check安装异常: {e}", flush=True)
            self.logger.error(f"subs-check安装失败: {str(e)}")
            return False

    def create_config(
        self, subscription_file: str, concurrent: int | None = None, phase: int = 1
    ) -> bool:
        """创建subs-check配置文件

        Args:
            subscription_file: 订阅文件路径
            concurrent: 并发数
            phase: 测试阶段（1=连通性测试，2=媒体检测）
        """
        try:
            self.logger.info(f"创建subs-check配置文件（阶段{phase}）...")

            # 计算订阅URL
            subscription_url = (
                f"http://127.0.0.1:{self.http_server_port}/{subscription_file}"
            )
            self.logger.info(f"阶段{phase}订阅URL: {subscription_url}")

            # 使用智能管理器计算最优并发数和超时
            # 先读取订阅文件获取节点数量（如果可能）
            node_count = 0
            try:
                subscription_path = os.path.join(self.project_root, subscription_file)
                if os.path.exists(subscription_path):
                    with open(subscription_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if data and "proxies" in data:
                            node_count = len(data["proxies"])
                            self.logger.info(f"检测到{node_count}个节点")
            except:
                pass

            # 计算最优配置
            if concurrent is None:
                concurrent = self.timeout_manager.calculate_optimal_concurrency(
                    node_count, phase
                )

            timeout = self.timeout_manager.calculate_optimal_timeout(phase, node_count)

            # 根据阶段设置不同的配置
            if phase == 1:
                # 阶段1: 快速连通性测试（禁用媒体检测，高并发）
                config = {
                    # 基本配置 - 参考SubsCheck标准优化
                    "print-progress": True,
                    "concurrent": concurrent,  # 智能计算并发数
                    "check-interval": 999999,
                    "timeout": timeout,  # 智能计算超时
                    # 测速配置
                    "alive-test-url": "http://gstatic.com/generate_204",
                    "speed-test-url": "",
                    "min-speed": 0,
                    "download-timeout": 1,
                    "download-mb": 0,
                    "total-speed-limit": 0,
                    # 流媒体检测（禁用）
                    "media-check": False,
                    "media-check-timeout": 0,
                    "platforms": [],
                    # 节点配置
                    "rename-node": True,
                    "node-prefix": "",
                    "success-limit": 0,
                    # 输出配置
                    "output-dir": self.output_dir,
                    "listen-port": "",
                    "save-method": "local",
                    # Web UI
                    "enable-web-ui": False,
                    "api-key": "",
                    # Sub-Store
                    "sub-store-port": "",
                    "sub-store-path": "",
                    # 代理配置
                    "github-proxy": "",
                    "proxy": "",
                    # 其他
                    "keep-success-proxies": False,
                    "sub-urls-retry": 1,  # 大幅减少重试次数，避免卡死
                    "sub-urls-get-ua": "clash.meta (https://github.com/beck-8/subs-check)",
                    # 使用本地文件路径，避免HTTP服务器问题
                    "sub-urls": [subscription_url],
                }
            else:
                # 阶段2: 媒体检测（只检测openai和gemini，低并发）
                config = {
                    # 基本配置 - 参考SubsCheck标准优化
                    "print-progress": True,
                    "concurrent": concurrent,  # 智能计算并发数
                    "check-interval": 999999,
                    "timeout": timeout,  # 智能计算超时
                    # 测速配置
                    "alive-test-url": "http://gstatic.com/generate_204",
                    "speed-test-url": "",
                    "min-speed": 0,
                    "download-timeout": 1,
                    "download-mb": 0,
                    "total-speed-limit": 0,
                    # 流媒体检测（参考SubsCheck标准优化）
                    "media-check": True,
                    "media-check-timeout": 8,  # 8秒超时，快速跳过无响应节点
                    "platforms": ["openai", "gemini"],
                    # 节点配置
                    "rename-node": True,
                    "node-prefix": "",
                    "success-limit": 0,
                    # 输出配置
                    "output-dir": self.output_dir,
                    "listen-port": "",
                    "save-method": "local",
                    # Web UI
                    "enable-web-ui": False,
                    "api-key": "",
                    # Sub-Store
                    "sub-store-port": "",
                    "sub-store-path": "",
                    # 代理配置
                    "github-proxy": "",
                    "proxy": "",
                    # 其他
                    "keep-success-proxies": False,
                    "sub-urls-retry": 1,  # 大幅减少重试次数，避免卡死
                    "sub-urls-get-ua": "clash.meta (https://github.com/beck-8/subs-check)",
                    # 使用本地文件路径，避免HTTP服务器问题
                    "sub-urls": [subscription_url],
                }

            self.logger.info(f"阶段{phase}配置: 并发={concurrent}, 超时={timeout}ms")

            # 保存配置
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

            self.logger.info(f"配置文件创建成功: {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"创建配置文件失败: {str(e)}")
            return False

    def run_test(
        self, node_count: int = 0, timeout: int | None = None
    ) -> Tuple[bool, str]:
        """运行测试（两阶段测试）"""
        try:
            print("\n" + "=" * 60, flush=True)
            print("开始执行两阶段节点测试", flush=True)
            print("=" * 60, flush=True)

            # 启动HTTP服务器
            print("\n[1/6] 启动HTTP服务器...", flush=True)
            if not self.start_http_server():
                return False, "HTTP服务器启动失败"
            print("✓ HTTP服务器启动成功", flush=True)

            # 检查二进制文件
            print("\n[2/6] 检查subs-check工具...", flush=True)
            if not os.path.exists(self.binary_path):
                self.logger.warning("subs-check不存在，开始安装...")
                print("正在安装subs-check...", flush=True)
                if not self.install_subscheck():
                    return False, "subs-check安装失败"
            print("✓ subs-check工具就绪", flush=True)

            # 阶段1: 连通性测试
            print("\n[3/6] 阶段1: 连通性测试（禁用媒体检测，高并发）", flush=True)
            print("=" * 60, flush=True)
            self.logger.info("=" * 60)
            self.logger.info("阶段1: 连通性测试（禁用媒体检测，高并发）")
            self.logger.info("=" * 60)
            phase1_success, phase1_message = self.run_phase1(node_count, timeout)

            if not phase1_success:
                print(f"\n✗ 阶段1失败: {phase1_message}", flush=True)
                self.logger.error(f"阶段1失败: {phase1_message}")
                self.stop_http_server()
                return False, f"阶段1失败: {phase1_message}"

            # 读取阶段1结果
            print("\n[4/6] 读取阶段1结果...", flush=True)
            phase1_nodes = []
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and "proxies" in data:
                    phase1_nodes = [proxy for proxy in data["proxies"]]
                    print(f"✓ 阶段1完成: {len(phase1_nodes)}个节点可用", flush=True)
                    self.logger.info(f"阶段1可用节点数: {len(phase1_nodes)}")
            except Exception as e:
                print(f"✗ 读取阶段1结果失败: {str(e)}", flush=True)
                self.logger.error(f"读取阶段1结果失败: {str(e)}")
                self.stop_http_server()
                return False, f"读取阶段1结果失败: {str(e)}"

            if not phase1_nodes:
                print("\n⚠ 阶段1无可用节点，跳过阶段2", flush=True)
                self.logger.warning("阶段1无可用节点，跳过阶段2")
                self.stop_http_server()
                return True, "阶段1完成，无可用节点"

            # 将阶段1的输出文件转换为Clash格式，供阶段2使用
            print("\n[5/6] 准备阶段2测试...", flush=True)
            phase2_subscription_file = "result/output/clash_subscription.yaml"
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data:
                    # 保存为Clash格式
                    with open(phase2_subscription_file, "w", encoding="utf-8") as f:
                        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
                    print(f"✓ 阶段1结果已转换", flush=True)
                    self.logger.info(
                        f"阶段1结果已转换为Clash格式: {phase2_subscription_file}"
                    )
            except Exception as e:
                print(f"✗ 转换阶段1结果失败: {str(e)}", flush=True)
                self.logger.error(f"转换阶段1结果失败: {str(e)}")
                self.stop_http_server()
                return False, f"转换阶段1结果失败: {str(e)}"

            # 阶段2: 媒体检测
            print(f"\n[6/6] 阶段2: 媒体检测（{len(phase1_nodes)}个节点）", flush=True)
            print("=" * 60, flush=True)
            self.logger.info("=" * 60)
            self.logger.info(f"阶段2: 媒体检测（节点数: {len(phase1_nodes)}）")
            self.logger.info("=" * 60)
            phase2_success, phase2_message = self.run_phase2(
                len(phase1_nodes), timeout, phase2_subscription_file
            )

            # 停止HTTP服务器
            print("\n停止HTTP服务器...", flush=True)
            self.stop_http_server()
            print("✓ HTTP服务器已停止", flush=True)

            if not phase2_success:
                print(f"\n⚠ 阶段2失败: {phase2_message}", flush=True)
                self.logger.warning(f"阶段2失败: {phase2_message}")
                # 阶段2失败不影响整体成功，返回阶段1的结果
                return True, f"阶段1完成，阶段2失败: {phase2_message}"

            print("\n" + "=" * 60, flush=True)
            print("✓ 两阶段测试完成", flush=True)
            print("=" * 60, flush=True)
            return True, "两阶段测试完成"

        except Exception as e:
            print(f"\n✗ 测试失败: {str(e)}", flush=True)
            self.logger.error(f"测试失败: {str(e)}")
            self.stop_http_server()
            return False, f"测试失败: {str(e)}"

    def run_phase1(
        self, node_count: int = 0, timeout: int | None = None
    ) -> Tuple[bool, str]:
        """阶段1: 连通性测试（禁用媒体检测，高并发）"""
        try:
            print(f"\n创建阶段1配置...", flush=True)
            # 创建阶段1配置
            if not self.create_config("result/clash_subscription.yaml", phase=1):
                return False, "创建阶段1配置失败"
            print(f"✓ 阶段1配置已创建", flush=True)

            # 使用智能管理器计算超时时间
            if timeout is None:
                timeout = self.timeout_manager.calculate_optimal_timeout(1, node_count)
                # 转换为秒并添加缓冲
                timeout_seconds = timeout / 1000
                timeout_seconds = timeout_seconds * 2.5  # 2.5倍缓冲
                # 对于大量节点，确保足够的超时时间
                if node_count > 1000:
                    timeout_seconds = max(timeout_seconds, 1800)  # 至少30分钟
                elif node_count > 500:
                    timeout_seconds = max(timeout_seconds, 1200)  # 至少20分钟
                else:
                    timeout_seconds = max(timeout_seconds, 900)  # 至少15分钟

                print(
                    f"智能计算超时: 节点数={node_count}, 预计超时={int(timeout_seconds)}秒 ({int(timeout_seconds / 60)}分钟)",
                    flush=True,
                )
                self.logger.info(
                    f"智能计算阶段1超时: 节点数={node_count}, 超时={int(timeout_seconds)}秒"
                )
                timeout = int(timeout_seconds)

            self.logger.info("开始运行阶段1测试...")
            self.performance_monitor.start_test(node_count)

            # 运行subs-check
            cmd = [self.binary_path, "-f", self.config_file]

            self.logger.info(f"执行命令: {' '.join(cmd)}")

            # 设置环境变量确保无缓冲输出
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.project_root,
                universal_newlines=False,
                bufsize=0,
                env=env,
            )

            # 实时输出日志
            return self._monitor_process(timeout, phase=1, node_count=node_count)

        except Exception as e:
            self.logger.error(f"阶段1测试失败: {str(e)}")
            return False, str(e)

    def run_phase2(
        self,
        node_count: int = 0,
        timeout: int | None = None,
        subscription_file: str | None = None,
    ) -> Tuple[bool, str]:
        """阶段2: 媒体检测（只检测openai和gemini，低并发）

        Args:
            node_count: 节点数量
            timeout: 超时时间
            subscription_file: 订阅文件路径（阶段1的输出文件）
        """
        try:
            # 如果没有指定订阅文件，使用默认值
            if subscription_file is None:
                subscription_file = "result/clash_subscription.yaml"

            print(f"\n创建阶段2配置...", flush=True)
            # 创建阶段2配置
            if not self.create_config(subscription_file, phase=2):
                return False, "创建阶段2配置失败"
            print(f"✓ 阶段2配置已创建", flush=True)

            # 使用智能管理器计算超时时间
            if timeout is None:
                timeout = self.timeout_manager.calculate_optimal_timeout(2, node_count)
                # 转换为秒并添加缓冲
                timeout_seconds = timeout / 1000
                timeout_seconds = timeout_seconds * 3.0  # 媒体检测需要更多缓冲
                timeout_seconds = max(timeout_seconds, 900)  # 最少15分钟

                print(
                    f"智能计算超时: 节点数={node_count}, 预计超时={int(timeout_seconds)}秒 ({int(timeout_seconds / 60)}分钟)",
                    flush=True,
                )
                self.logger.info(
                    f"智能计算阶段2超时: 节点数={node_count}, 超时={int(timeout_seconds)}秒"
                )
                timeout = int(timeout_seconds)

            print(f"\n开始运行阶段2测试...", flush=True)
            self.logger.info("开始运行阶段2测试...")
            self.performance_monitor.start_test(node_count)

            # 测试订阅URL是否可访问
            subscription_url = (
                f"http://127.0.0.1:{self.http_server_port}/{subscription_file}"
            )
            print(f"测试订阅URL: {subscription_url}", flush=True)
            try:
                import requests

                test_response = requests.get(subscription_url, timeout=5)
                print(
                    f"✓ 订阅URL可访问，状态码: {test_response.status_code}", flush=True
                )
                self.logger.info(f"订阅URL可访问，状态码: {test_response.status_code}")
            except Exception as e:
                print(f"✗ 订阅URL不可访问: {str(e)}", flush=True)
                self.logger.error(f"订阅URL不可访问: {str(e)}")

            # 运行subs-check
            cmd = [self.binary_path, "-f", self.config_file]

            print(f"执行命令: {' '.join(cmd)}", flush=True)
            self.logger.info(f"执行命令: {' '.join(cmd)}")

            # 设置环境变量确保无缓冲输出
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.project_root,
                universal_newlines=False,
                bufsize=0,
                env=env,
            )

            # 实时输出日志
            return self._monitor_process(timeout, phase=2, node_count=node_count)

        except Exception as e:
            self.logger.error(f"阶段2测试失败: {str(e)}")
            return False, str(e)

    def _monitor_process(
        self, timeout: int, phase: int = 1, node_count: int = 0
    ) -> Tuple[bool, str]:
        """监控进程输出"""
        try:
            start_time = time.time()
            last_output_time = start_time
            last_line = ""
            line_count = 0
            last_progress_displayed = -1.0  # 记录上一次显示的进度，避免重复打印
            node_test_times = {}  # 记录每个节点的开始测试时间 {node_index: start_time}
            last_tested_index = -1  # 上一个测试的节点索引

            # 添加调试信息
            print(f"[DEBUG] 阶段{phase}监控开始，超时={timeout}秒，节点数={node_count}", flush=True)
            self.logger.info(f"阶段{phase}监控开始，超时={timeout}秒，节点数={node_count}")

            while True:
                # 检查总超时
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    self.logger.error(
                        f"阶段{phase}超过超时时间 {timeout}秒 ({timeout / 60:.1f}分钟)，强制终止"
                    )
                    self.process.terminate()
                    self.process.wait(timeout=10)
                    return False, f"阶段{phase}超时"

                # 解析进度 - 适配 subs-check 多种输出格式
                current_progress = 0
                tested_count = 0
                total_count = node_count if node_count else 0

                # 尝试多种进度格式
                patterns = [
                    r"\[.*?\]\s+(\d+\.?\d*)%\s+\((\d+)/(\d+)\)",  # 格式1: [时间] XX% (X/X)
                    r"进度[:：]\s*(\d+\.?\d*)%\s*\((?:(\d+)/)?(\d+)\)?",  # 格式2: 进度: XX% (X/X)
                    r"(\d+\.?\d*)%\s*\((?:(\d+)/)?(\d+)\)",  # 通用格式: XX% (X/X)
                    r"(\d+\.?\d*)%",  # 简单格式: XX%
                ]

                for pattern in patterns:
                    match = re.search(pattern, last_line)
                    if match:
                        groups = match.groups()
                        current_progress = float(groups[0])
                        if len(groups) >= 3 and groups[1]:
                            tested_count = int(groups[1])
                        elif len(groups) >= 3:
                            tested_count = int(current_progress / 100 * int(groups[2]))
                            total_count = int(groups[2])
                        elif len(groups) == 2 and groups[1]:
                            tested_count = int(groups[1])
                        break

                # 节点数量估算：如果没有解析到进度，根据运行时间估算
                if current_progress == 0 and total_count > 0:
                    elapsed = time.time() - start_time
                    estimated_tested = min(int(elapsed * 5), total_count)
                    if estimated_tested > last_tested_index:
                        tested_count = estimated_tested
                        current_progress = tested_count / total_count * 100

                # 记录新节点的开始测试时间
                if tested_count > last_tested_index and phase == 2:
                    node_test_times[tested_count] = time.time()
                    last_tested_index = tested_count
                    self.performance_monitor.record_node_processed()

                # 检查是否完成
                if current_progress >= 95.0 and tested_count >= total_count * 0.95:
                    self.logger.info(
                        f"检测到阶段{phase}测试完成（进度: {current_progress:.1f}%，测试: {tested_count}/{total_count}），准备终止进程"
                    )
                    break

                if current_progress >= 99.9 or tested_count >= total_count:
                    self.logger.info(
                        f"检测到阶段{phase}测试完成（进度: {current_progress:.1f}%，测试: {tested_count}/{total_count}），准备终止进程"
                    )
                    break

                # 如果没有匹配到进度，但有节点数量信息，尝试从其他输出中提取
                if current_progress == 0:
                    # 尝试解析 "可用节点数量: X" 或 "测试 X/Y" 这样的信息
                    available_match = re.search(r"可用节点数量[:：]\s*(\d+)", last_line)
                    if available_match:
                        tested_count = int(available_match.group(1))
                        current_progress = (
                            (tested_count / total_count * 100) if total_count > 0 else 0
                        )

                # 节点数量估算：如果没有解析到进度，根据运行时间估算
                if current_progress == 0 and total_count > 0:
                    elapsed = time.time() - start_time
                    # 假设每秒可以测试 5-10 个节点
                    estimated_tested = min(int(elapsed * 5), total_count)
                    if estimated_tested > last_tested_index:
                        tested_count = estimated_tested
                        current_progress = tested_count / total_count * 100

                    # 记录新节点的开始测试时间
                    if tested_count > last_tested_index and phase == 2:
                        node_test_times[tested_count] = time.time()
                        last_tested_index = tested_count
                        # 记录到性能监控器
                        self.performance_monitor.record_node_processed()

                    # 当进度达到95%以上且测试数量接近总数时，认为测试完成（提高完成阈值）
                    if current_progress >= 95.0 and tested_count >= total_count * 0.95:
                        self.logger.info(
                            f"检测到阶段{phase}测试完成（进度: {current_progress}%, 测试: {tested_count}/{total_count}），准备终止进程"
                        )
                        break

                    # 如果进度显示100%或者测试数量等于总数，也认为完成
                    if current_progress >= 99.9 or tested_count >= total_count:
                        self.logger.info(
                            f"检测到阶段{phase}测试完成（进度: {current_progress}%, 测试: {tested_count}/{total_count}），准备终止进程"
                        )
                        break

                # 检查静默超时 - 放宽超时时间以适应大量节点测试
                # 阶段1需要更长时间因为节点数量多（1269个节点）
                if phase == 1:
                    # 根据节点数量动态调整静默超时
                    if node_count > 1000:
                        silent_timeout = 300  # 大量节点：5分钟
                    elif node_count > 500:
                        silent_timeout = 240  # 中等数量：4分钟
                    else:
                        silent_timeout = 180  # 少量节点：3分钟
                else:
                    if node_count > 100:
                        silent_timeout = 300  # 阶段2媒体检测更慢
                    else:
                        silent_timeout = 240

                silent_elapsed = time.time() - last_output_time

                # 每分钟输出一次状态信息
                if int(silent_elapsed) % 60 == 0 and int(silent_elapsed) > 0:
                    # 获取性能统计
                    stats = self.performance_monitor.get_current_stats()

                    # 动态调整并发数
                    if avg_latency := stats.get("avg_latency", 0):
                        new_concurrency = (
                            self.concurrency_controller.adjust_concurrency(
                                current_progress,
                                avg_latency,
                                stats.get("error_count", 0) / max(tested_count, 1),
                            )
                        )
                        self.logger.info(f"动态调整并发数: {new_concurrency}")

                    # 检查进程状态
                    process_status = (
                        "运行中"
                        if self.process and self.process.poll() is None
                        else f"已退出(返回码:{self.process.poll()})"
                    )
                    self.logger.info(
                        f"阶段{phase}测试中... 已运行{int(elapsed)}秒，{int(silent_elapsed)}秒无输出，当前进度: {current_progress:.1f}%，进程状态: {process_status}"
                    )

                # 阶段1：60秒无输出时输出警告，阶段2：120秒无输出时输出警告
                warning_time = 60 if phase == 1 else 120
                if int(silent_elapsed) == warning_time:
                    process_status = (
                        "运行中"
                        if self.process.poll() is None
                        else f"已退出(返回码:{self.process.poll()})"
                    )
                    self.logger.warning(
                        f"⚠ 阶段{phase}已{warning_time}秒无输出，进程状态: {process_status}，最后输出: {last_line.strip() if last_line else '(空)'}"
                    )

                if silent_elapsed > silent_timeout:
                    # 使用智能管理器判断是否应该继续等待
                    remaining_nodes = (
                        total_count - tested_count
                        if tested_count and total_count
                        else 0
                    )

                    # 强制硬超时保护：如果总运行时间超过 25 分钟，强制终止
                    total_elapsed = time.time() - start_time
                    hard_timeout = 1500  # 25分钟硬超时
                    if total_elapsed > hard_timeout:
                        self.logger.warning(
                            f"阶段{phase}达到硬超时限制({hard_timeout}秒/{hard_timeout / 60:.0f}分钟)，强制终止"
                        )
                        if self.process and self.process.poll() is None:
                            self.process.terminate()
                            try:
                                self.process.wait(timeout=10)
                            except:
                                self.process.kill()
                        break

                    self.logger.info(
                        f"检测到{silent_timeout}秒（{silent_timeout / 60:.0f}分钟）无新输出（当前进度: {current_progress:.1f}%）"
                    )
                    self.logger.info(
                        f"最后收到的输出: {last_line.strip() if last_line else '(空)'}"
                    )
                    self.logger.info(f"已接收总行数: {line_count}")

                    # 检查进程状态
                    if self.process and self.process.poll() is None:
                        self.logger.warning("进程仍在运行但无输出，尝试终止进程...")
                        self.process.terminate()
                        try:
                            self.process.wait(timeout=10)  # 增加等待时间
                            self.logger.info("进程已终止")
                        except subprocess.TimeoutExpired:
                            self.logger.error("进程无法终止，强制kill")
                            if self.process:
                                self.process.kill()
                    else:
                        if self.process:
                            self.logger.info(
                                f"进程已自然退出，返回码: {self.process.poll()}"
                            )

                    break

                # 使用select检查是否有可读数据
                                    import select
                
                                    try:
                                        byte = None
                                        char = ""  # 初始化char变量
                                        if self.process and self.process.stdout:
                                            ready, _, _ = select.select([self.process.stdout], [], [], 0.5)
                                            if ready:
                                                # 读取数据
                                                byte = self.process.stdout.read(1)
                                                if byte:
                                                    last_output_time = time.time()
                                                    char = (
                                                        byte.decode("utf-8", errors="ignore")
                                                        if byte
                                                        else ""
                                                    )
                
                                                    # 添加调试输出：每100个字符显示一次
                                                    if line_count % 100 == 0:
                                                        print(f"[DEBUG] 已读取{line_count}行，当前字符: {repr(char[:50])}", flush=True)                            byte = self.process.stdout.read(1)
                            if byte:
                                last_output_time = time.time()
                                char = (
                                    byte.decode("utf-8", errors="ignore")
                                    if byte
                                    else ""
                                )
                                if char == "\n":
                                    if last_line.strip():
                                        # 阶段2：显示所有输出行（调试用）
                                        if phase == 2:
                                            print(
                                                f"[P2-DEBUG] {last_line.strip()}",
                                                flush=True,
                                            )
                                            # 解析节点测试结果（阶段2才显示节点状态）
                                            node_result = self._parse_node_result(
                                                last_line
                                            )
                                            if node_result:
                                                node_name = node_result["name"]
                                                # 计算单个节点的测试耗时
                                                test_duration = 0
                                                if tested_count in node_test_times:
                                                    test_duration = (
                                                        time.time()
                                                        - node_test_times[tested_count]
                                                    )
                                                current_time = time.strftime(
                                                    "%H:%M:%S", time.localtime()
                                                )
                                                # 构建测试状态字符串，动态显示所有测试项
                                                status_parts = []
                                                if node_result["gpt"]:
                                                    status_parts.append("GPT:✓")
                                                if node_result["gemini"]:
                                                    status_parts.append("GM:✓")
                                                if node_result["youtube"]:
                                                    status_parts.append("YT:✓")
                                                # 如果没有任何测试项通过，显示失败状态
                                                if not status_parts:
                                                    if node_result["gpt"]:
                                                        status_parts.append("GPT:✗")
                                                    if node_result["gemini"]:
                                                        status_parts.append("GM:✗")
                                                    if node_result["youtube"]:
                                                        status_parts.append("YT:✗")
                                                status_str = " ".join(status_parts)
                                                # 新格式：时间点 节点进度 节点名称 测试项状态 测试耗时
                                                progress_str = (
                                                    f"{current_progress:.1f}% ({tested_count}/{total_count})"
                                                    if current_progress > 0
                                                    else "N/A"
                                                )
                                                duration_str = (
                                                    f"{test_duration:.1f}s"
                                                    if test_duration > 0
                                                    else "N/A"
                                                )
                                                print(
                                                    f"{current_time} {progress_str} {node_name} {status_str} {duration_str}",
                                                    flush=True,
                                                )
                                            elif (
                                                current_progress > 0
                                                and current_progress
                                                != last_progress_displayed
                                            ):
                                                # 简洁的进度显示：P2: 38.2% (570/1493)，只在进度变化时显示
                                                current_time = time.strftime(
                                                    "%H:%M:%S", time.localtime()
                                                )
                                                print(
                                                    f"[{current_time}] P{phase}: {current_progress:.1f}% ({tested_count}/{total_count})",
                                                    flush=True,
                                                )
                                                last_progress_displayed = (
                                                    current_progress
                                                )
                                            else:
                                                # 其他信息正常显示
                                                print(
                                                    f"[P{phase}] {last_line.strip()}",
                                                    flush=True,
                                                )
                                        else:
                                            # 阶段1：显示所有输出行（调试用）
                                            print(
                                                f"[P1-DEBUG] {last_line.strip()}",
                                                flush=True,
                                            )
                                            # 阶段1只显示进度，只在进度变化时显示
                                            if (
                                                current_progress > 0
                                                and current_progress
                                                != last_progress_displayed
                                            ):
                                                # 简洁的进度显示：P1: 38.2% (570/1493)
                                                current_time = time.strftime(
                                                    "%H:%M:%S", time.localtime()
                                                )
                                                print(
                                                    f"[{current_time}] P{phase}: {current_progress:.1f}% ({tested_count}/{total_count})",
                                                    flush=True,
                                                )
                                                last_progress_displayed = (
                                                    current_progress
                                                )
                                            else:
                                                # 其他信息正常显示
                                                print(
                                                    f"[P{phase}] {last_line.strip()}",
                                                    flush=True,
                                                )
                                        line_count += 1
                                    last_line = ""
                            elif char and char == "\r":
                                # 只在阶段2且遇到节点结果时才处理
                                if phase == 2:
                                    node_result = self._parse_node_result(last_line)
                                    if node_result:
                                        node_name = node_result["name"]
                                        # 计算单个节点的测试耗时
                                        test_duration = 0
                                        if tested_count in node_test_times:
                                            test_duration = (
                                                time.time()
                                                - node_test_times[tested_count]
                                            )
                                        current_time = time.strftime(
                                            "%H:%M:%S", time.localtime()
                                        )
                                        # 构建测试状态字符串，动态显示所有测试项
                                        status_parts = []
                                        if node_result["gpt"]:
                                            status_parts.append("GPT:✓")
                                        if node_result["gemini"]:
                                            status_parts.append("GM:✓")
                                        if node_result["youtube"]:
                                            status_parts.append("YT:✓")
                                        # 如果没有任何测试项通过，显示失败状态
                                        if not status_parts:
                                            if node_result["gpt"]:
                                                status_parts.append("GPT:✗")
                                            if node_result["gemini"]:
                                                status_parts.append("GM:✗")
                                            if node_result["youtube"]:
                                                status_parts.append("YT:✗")
                                        status_str = " ".join(status_parts)
                                        # 新格式：时间点 节点进度 节点名称 测试项状态 测试耗时
                                        progress_str = (
                                            f"{current_progress:.1f}% ({tested_count}/{total_count})"
                                            if current_progress > 0
                                            else "N/A"
                                        )
                                        duration_str = (
                                            f"{test_duration:.1f}s"
                                            if test_duration > 0
                                            else "N/A"
                                        )
                                        print(
                                            f"{current_time} {progress_str} {node_name} {status_str} {duration_str}",
                                            flush=True,
                                        )
                                    # 不在 \r 时打印进度，避免重复
                                last_line = ""
                            else:
                                if char:
                                    last_line += char
                                    if len(last_line) >= 100:
                                        print(
                                            f"[P{phase}] {last_line}",
                                            end="",
                                            flush=True,
                                        )
                                        last_line = ""
                        else:
                            break
                except (OSError, ValueError):
                    break

                # 检查进程是否结束
                if self.process and self.process.poll() is not None:
                    self.logger.info(
                        f"阶段{phase}进程已自然结束，返回码: {self.process.poll()}"
                    )
                    break

                # 检查是否收到测试完成的标志信息
                if self._is_test_completed(last_line, phase):
                    self.logger.info(
                        f"检测到阶段{phase}测试完成标志: {last_line.strip()}"
                    )
                    break

                time.sleep(0.01)

            # 等待进程结束 - 增加等待时间以适应subs-check的清理过程
            self.logger.info(f"等待阶段{phase}进程结束...")

            # 智能等待：定期检查输出文件，如果文件已更新则认为任务完成
            max_wait_time = max(timeout * 2, 300)  # 至少等待5分钟或超时时间的2倍
            check_interval = 10
            elapsed = 0

            initial_file_size = 0
            if os.path.exists(self.output_file):
                try:
                    initial_file_size = os.path.getsize(self.output_file)
                except:
                    initial_file_size = 0

            while elapsed < max_wait_time:
                if self.process.poll() is not None:
                    # 进程已结束
                    return_code = self.process.returncode
                    self.logger.info(
                        f"✅ 阶段{phase}进程自然结束，返回码: {return_code}"
                    )
                    break

                # 检查输出文件是否有更新（表示任务可能已完成）
                if os.path.exists(self.output_file):
                    try:
                        current_file_size = os.path.getsize(self.output_file)
                        if (
                            current_file_size > initial_file_size
                            and current_file_size > 1024
                        ):  # 文件有更新且大于1KB
                            self.logger.info(
                                f"📊 检测到输出文件已更新，任务可能已完成，等待进程自然退出..."
                            )
                            # 给进程更多时间自然退出
                            if self.process.wait(timeout=30):
                                return_code = self.process.returncode
                                self.logger.info(
                                    f"✅ 阶段{phase}进程在文件更新后自然退出，返回码: {return_code}"
                                )
                                break
                    except:
                        pass

                time.sleep(check_interval)
                elapsed += check_interval
                self.logger.debug(f"等待阶段{phase}进程，已等待{elapsed}秒...")
            else:
                # 超时，强制终止
                self.logger.warning(
                    f"⚠️ 阶段{phase}进程未在{max_wait_time}秒内退出，尝试终止..."
                )
                self.process.terminate()
                try:
                    return_code = self.process.wait(timeout=30)  # 增加终止等待时间
                    self.logger.info(f"✅ 阶段{phase}进程已终止，返回码: {return_code}")
                except subprocess.TimeoutExpired:
                    self.logger.error(f"❌ 阶段{phase}进程无法终止，强制kill")
                    self.process.kill()
                    try:
                        return_code = self.process.wait(timeout=5)  # 等待kill完成
                        self.logger.info(
                            f"✅ 阶段{phase}进程已强制终止，返回码: {return_code}"
                        )
                    except subprocess.TimeoutExpired:
                        self.logger.error(f"❌ 阶段{phase}进程强制终止也失败")
                        return_code = -1

            # 检查输出文件
            tested_node_count = 0
            if os.path.exists(self.output_file):
                try:
                    with open(self.output_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    if data and "proxies" in data:
                        tested_node_count = len(data["proxies"])
                        self.logger.info(
                            f"阶段{phase}输出文件有效，包含 {tested_node_count} 个节点"
                        )
                except Exception as e:
                    self.logger.warning(f"检查阶段{phase}输出文件失败: {str(e)}")

            # 更新性能管理器的指标
            stats = self.performance_monitor.get_current_stats()
            # 从监控的输出中推断总节点数
            total_nodes = max(tested_count, tested_node_count, total_count)
            self.timeout_manager.update_performance_metrics(
                total_nodes,
                stats.get("avg_latency", 200.0),
                (tested_node_count / max(total_nodes, 1)) if total_nodes > 0 else 0.0,
                stats.get("duration", 0.0),
            )

            # 判断是否成功
            if tested_node_count > 0:
                return True, f"阶段{phase}完成，测试了{tested_node_count}个节点"
            else:
                return False, f"阶段{phase}完成，但无有效节点"

        except Exception as e:
            self.logger.error(f"监控阶段{phase}进程失败: {str(e)}")
            return False, str(e)

    def parse_results(self) -> List[str]:
        """解析测试结果并重命名节点"""
        try:
            if not os.path.exists(self.output_file):
                self.logger.warning("输出文件不存在")
                return []

            self.logger.info(f"解析输出文件: {self.output_file}")

            with open(self.output_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # 提取节点并重命名
            renamed_nodes = []
            total_count = 0
            media_filtered_count = 0
            gpt_count = 0
            gemini_count = 0

            # 地区计数器，确保每个地区按自然数编号
            region_counters = {}

            if data and "proxies" in data:
                for proxy in data["proxies"]:
                    total_count += 1

                    # 提取地区信息
                    region = self._extract_region(proxy)

                    # 初始化地区计数器
                    if region not in region_counters:
                        region_counters[region] = 0

                    # 地区编号递增（自然数编号）
                    region_counters[region] += 1
                    region_number = region_counters[region]

                    # 提取测试结果
                    media_info = self._extract_media_info(proxy)

                    # 统计GPT和Gemini可用节点
                    if media_info["gpt"]:
                        gpt_count += 1
                    if media_info["gemini"]:
                        gemini_count += 1

                    # 2选1规则：GPT或Gemini至少通过1个才能保留
                    if not (media_info["gpt"] or media_info["gemini"]):
                        media_filtered_count += 1
                        continue

                    # 生成新名称
                    new_name = self._generate_node_name(
                        region, region_number, media_info
                    )

                    # 将Clash节点转换回V2Ray URI格式
                    v2ray_uri = self._convert_proxy_to_uri(proxy, new_name)
                    if v2ray_uri:
                        renamed_nodes.append(v2ray_uri)

            # 显示详细的统计信息
            gpt_status = "✓" if gpt_count > 0 else "✗"
            gemini_status = "✓" if gemini_count > 0 else "✗"
            print(
                f"\n测试完成: {total_count}个节点 | 有效: {len(renamed_nodes)} | GPT: {gpt_status} ({gpt_count}) | Gemini: {gemini_status} ({gemini_count})",
                flush=True,
            )

            self.logger.info(
                f"节点统计: 总数{total_count}, 媒体过滤{media_filtered_count}, 有效{len(renamed_nodes)}"
            )
            self.logger.info(f"GPT可用: {gpt_count}, Gemini可用: {gemini_count}")
            self.logger.info(
                f"从测试结果中提取并重命名 {len(renamed_nodes)} 个有效节点"
            )
            return renamed_nodes

        except Exception as e:
            self.logger.error(f"解析测试结果失败: {str(e)}")
            return []

    def _is_test_completed(self, line: str, phase: int) -> bool:
        """检测测试是否完成"""
        try:
            import re

            # 检查常见的测试完成标志
            completion_patterns = [
                r".*test.*completed.*",
                r".*all.*nodes.*tested.*",
                r".*testing.*finished.*",
                r".*结果.*保存.*",
                r".*output.*saved.*",
                r".*test.*finished.*",
                r".*done.*",
                r".*completed.*",
            ]

            line_lower = line.lower()
            for pattern in completion_patterns:
                if re.search(pattern, line_lower):
                    return True

            # 检查是否包含最终统计信息
            if re.search(r".*\d+.*nodes.*\d+.*success.*", line_lower):
                return True

            # 检查是否包含保存文件的信息
            if "saved" in line_lower and (
                "yaml" in line_lower or "output" in line_lower
            ):
                return True

            return False

        except Exception:
            return False

    def _extract_delay_from_name(self, name: str) -> int:
        """从节点名称中提取延迟（毫秒）"""
        import re

        # 节点名称格式：FlagRegion_Number|AI|YT
        # 例如：🇺🇸US_5|GPT|YT → 延迟5ms
        match = re.search(r"[🇦-🇿]{2}[A-Z]{2}_(\d+)\|", name)
        if match:
            try:
                return int(match.group(1))
            except:
                return 0
        return 0

    def _extract_region(self, proxy: dict) -> str:
        """从节点中提取地区信息"""
        import re

        name = proxy.get("name", "")
        server = proxy.get("server", "")

        # 首先尝试从subs-check的节点名称中提取地区代码（格式：FlagRegion_Number）
        match = re.search(r"[🇦-🇿]{2}([A-Z]{2})_\d+", name)
        if match:
            return match.group(1)

        # 检查名称中是否包含地区标识
        region_keywords = {
            "HK": "HK",
            "香港": "HK",
            "Hong Kong": "HK",
            "US": "US",
            "美国": "US",
            "USA": "US",
            "JP": "JP",
            "日本": "JP",
            "Japan": "JP",
            "SG": "SG",
            "新加坡": "SG",
            "Singapore": "SG",
            "TW": "TW",
            "台湾": "TW",
            "Taiwan": "TW",
            "KR": "KR",
            "韩国": "KR",
            "Korea": "KR",
            "DE": "DE",
            "德国": "DE",
            "Germany": "DE",
            "GB": "GB",
            "英国": "GB",
            "UK": "GB",
            "FR": "FR",
            "法国": "FR",
            "France": "FR",
            "CA": "CA",
            "加拿大": "CA",
            "Canada": "CA",
        }

        for keyword, region in region_keywords.items():
            if keyword in name:
                return region

        # 默认返回US
        return "US"

    def _extract_region_number(self, proxy: dict) -> int:
        """从节点中提取地区编号"""
        import re

        name = proxy.get("name", "")

        # 从subs-check的节点名称中提取地区编号（格式：FlagRegion_Number）
        match = re.search(r"[🇦-🇿]{2}[A-Z]{2}_(\d+)", name)
        if match:
            return int(match.group(1))

        return 1

    def _parse_node_result(self, line: str) -> dict | None:
        """解析subs-check输出中的节点测试结果

        Args:
            line: subs-check的输出行

        Returns:
            dict: 包含节点名称和测试结果的字典
        """
        try:
            import re

            # subs-check输出格式示例：
            # : [====>] 99.9% (1492/1493) : 46
            # 或者其他包含节点信息的行

            # 尝试匹配节点名称和媒体测试结果
            # 节点名称格式可能包含：FlagRegion_Number|AI|YT 或类似格式
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 2:
                    node_name = parts[0].strip().split()[-1]  # 提取节点名称

                    # 解析媒体测试结果
                    media_info = {"gpt": False, "gemini": False, "youtube": False}

                    # 检查GPT标记
                    if "AI" in parts[1] or "GPT" in parts[1]:
                        media_info["gpt"] = True

                    # 检查Gemini标记
                    if "GM" in parts[1] or "Gemini" in parts[1]:
                        media_info["gemini"] = True

                    # 检查YouTube标记
                    if len(parts) >= 3 and ("YT" in parts[2] or "YouTube" in parts[2]):
                        media_info["youtube"] = True

                    return {
                        "name": node_name,
                        "gpt": media_info["gpt"],
                        "gemini": media_info["gemini"],
                        "youtube": media_info["youtube"],
                    }

            return None

        except Exception as e:
            return None

    def _extract_media_info(self, proxy: dict) -> dict:
        """从节点中提取媒体测试结果"""
        media_info = {"gpt": False, "gemini": False, "youtube": False}

        # subs-check会在节点名称中添加媒体解锁标记
        name = proxy.get("name", "")

        # 检查GPT标记（subs-check使用GPT⁺表示ChatGPT可用）
        if "GPT⁺" in name:
            media_info["gpt"] = True

        # 检查Gemini标记（subs-check使用GM表示Gemini可用）
        if "GM" in name:
            media_info["gemini"] = True

        # 检查YouTube标记（subs-check使用YT-{地区代码}格式）
        if "|YT-" in name:
            media_info["youtube"] = True

        return media_info

    def _generate_node_name(self, region: str, number: int, media_info: dict) -> str:
        """生成节点名称 - 测速后使用复杂格式"""
        # 国旗映射
        flags = {
            "HK": "🇭🇰",
            "US": "🇺🇸",
            "JP": "🇯🇵",
            "SG": "🇸🇬",
            "TW": "🇨🇳",
            "KR": "🇰🇷",
            "DE": "🇩🇪",
            "GB": "🇬🇧",
            "FR": "🇫🇷",
            "CA": "🇨🇦",
            "NL": "🇳🇱",
            "RU": "🇷🇺",
            "IN": "🇮🇳",
            "BR": "🇧🇷",
            "AU": "🇦🇺",
        }

        flag = flags.get(region, "")

        # 生成AI标记
        ai_tag = ""
        if media_info["gpt"] and media_info["gemini"]:
            ai_tag = "GPT|GM"
        elif media_info["gpt"]:
            ai_tag = "GPT"
        elif media_info["gemini"]:
            ai_tag = "GM"

        # 生成YouTube标记
        if media_info["youtube"]:
            if ai_tag:
                # 如果有AI标记，使用|YT
                yt_tag = "|YT"
            else:
                # 如果没有AI标记，直接使用YT
                yt_tag = "YT"
        else:
            yt_tag = ""

        # 组合复杂名称（测速后格式）
        return f"{flag}{region}_{number}|{ai_tag}{yt_tag}"

    def _convert_proxy_to_uri(self, proxy: dict, new_name: str) -> str:
        """将Clash节点转换回V2Ray URI格式"""
        try:
            proxy_type = proxy.get("type", "")

            if proxy_type == "ss":
                # Shadowsocks节点
                cipher = proxy.get("cipher", "aes-256-gcm")
                password = proxy.get("password", "")
                server = proxy.get("server", "")
                port = proxy.get("port", 443)
                return f"ss://{cipher}:{password}@{server}:{port}#{new_name}"

            elif proxy_type == "vmess":
                # VMess节点
                return f"vmess://{new_name}"

            elif proxy_type == "vless":
                # VLESS节点
                uuid = proxy.get("uuid", "")
                server = proxy.get("server", "")
                port = proxy.get("port", 443)
                security = proxy.get("tls", False)
                sni = proxy.get("servername", "")
                network = proxy.get("network", "tcp")

                # 构建VLESS URI
                params = []
                params.append(f"encryption=none")
                if security:
                    params.append(f"security=tls")
                    if sni:
                        params.append(f"sni={sni}")
                params.append(f"type={network}")

                if network == "ws":
                    ws_opts = proxy.get("ws-opts", {})
                    if ws_opts:
                        if "headers" in ws_opts and "Host" in ws_opts["headers"]:
                            params.append(f"host={ws_opts['headers']['Host']}")
                        if "path" in ws_opts:
                            path = ws_opts["path"]
                            # 移除path中包含的旧名称（#后面的内容）
                            if "#" in path:
                                path = path.split("#")[0]
                            # URL编码path中的#符号，避免URI格式错误
                            if "#" in path:
                                import urllib.parse

                                path = urllib.parse.quote(path, safe="")
                            params.append(f"path={path}")

                uri = f"vless://{uuid}@{server}:{port}?{'&'.join(params)}#{new_name}"
                return uri

            elif proxy_type == "trojan":
                # Trojan节点
                password = proxy.get("password", "")
                server = proxy.get("server", "")
                port = proxy.get("port", 443)
                sni = proxy.get("sni", "")

                params = []
                params.append(f"security=tls")
                if sni:
                    params.append(f"sni={sni}")

                uri = (
                    f"trojan://{password}@{server}:{port}?{'&'.join(params)}#{new_name}"
                )
                return uri

            elif proxy_type == "hysteria2":
                # Hysteria2节点
                password = proxy.get("password", "")
                server = proxy.get("server", "")
                port = proxy.get("port", 443)

                uri = f"hysteria2://{password}@{server}:{port}?insecure=1#{new_name}"
                return uri

            else:
                self.logger.warning(f"不支持的节点类型: {proxy_type}")
                return ""

        except Exception as e:
            self.logger.error(f"转换节点失败: {str(e)}")
            return ""


def convert_nodes_to_vless_yaml(clash_file: str, output_file: str) -> bool:
    """
    将Clash节点转换为VLESS订阅格式

    Args:
        clash_file: Clash配置文件路径
        output_file: 输出文件路径
    """
    logger = get_logger("converter")
    try:
        with open(clash_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        proxies = data.get("proxies", [])
        nodes = []

        for proxy in proxies:
            # 根据类型转换节点
            if proxy.get("type") == "ss":
                # Shadowsocks节点
                node = f"ss://{proxy.get('cipher')}:{proxy.get('password')}@{proxy.get('server')}:{proxy.get('port')}#{proxy.get('name', 'SS')}"
                nodes.append(node)
            elif proxy.get("type") == "vmess":
                # VMess节点
                node = f"vmess://{proxy.get('name', 'VMess')}"
                nodes.append(node)
            elif proxy.get("type") == "vless":
                # VLESS节点
                node = f"vless://{proxy.get('uuid')}@{proxy.get('server')}:{proxy.get('port')}?encryption=none&security=tls&type=ws&host={proxy.get('ws-opts', {}).get('headers', {}).get('Host', '')}&path={proxy.get('ws-opts', {}).get('path', '')}#{proxy.get('name', 'VLESS')}"
                nodes.append(node)
            elif proxy.get("type") == "trojan":
                # Trojan节点
                node = f"trojan://{proxy.get('password')}@{proxy.get('server')}:{proxy.get('port')}?security=tls&sni={proxy.get('sni', '')}#{proxy.get('name', 'Trojan')}"
                nodes.append(node)
            elif proxy.get("type") == "hysteria2":
                # Hysteria2节点
                node = f"hysteria2://{proxy.get('password')}@{proxy.get('server')}:{proxy.get('port')}?insecure=1#{proxy.get('name', 'Hysteria2')}"
                nodes.append(node)

        # 保存节点
        with open(output_file, "w", encoding="utf-8") as f:
            for node in nodes:
                f.write(f"{node}\n")

        logger.info(f"成功转换 {len(nodes)} 个节点到: {output_file}")
        return True

    except Exception as e:
        logger.error(f"转换节点失败: {str(e)}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="节点测速脚本 - 使用subs-check")
    parser.add_argument("--input", default="result/nodetotal.txt", help="输入节点文件")
    parser.add_argument("--output", default="result/nodelist.txt", help="输出节点文件")

    args = parser.parse_args()

    logger = get_logger("main")
    print(f"\n{'=' * 60}", flush=True)
    print("节点测速工具 - subs-check", flush=True)
    print(f"{'=' * 60}", flush=True)
    print(f"输入文件: {args.input}", flush=True)
    print(f"输出文件: {args.output}", flush=True)

    # 检查输入文件
    print(f"\n检查输入文件...", flush=True)
    if not os.path.exists(args.input):
        print(f"✗ 输入文件不存在: {args.input}", flush=True)
        logger.error(f"输入文件不存在: {args.input}")
        sys.exit(1)

    # 读取节点
    print(f"读取节点文件: {args.input}", flush=True)
    logger.info(f"读取节点文件: {args.input}")
    import time

    read_start = time.time()

    with open(args.input, "r", encoding="utf-8") as f:
        nodes = [line.strip() for line in f if line.strip()]

    read_elapsed = time.time() - read_start
    print(f"✅ 读取到 {len(nodes)} 个节点 (耗时: {read_elapsed:.2f}秒)", flush=True)
    logger.info(f"读取到 {len(nodes)} 个节点")

    # 限制节点数量，避免测试时间过长
    MAX_TEST_NODES = 500  # GitHub Actions 4核心机器建议最多500个节点
    if len(nodes) > MAX_TEST_NODES:
        print(
            f"⚠️  节点数量({len(nodes)})超过限制({MAX_TEST_NODES})，只测试前 {MAX_TEST_NODES} 个节点",
            flush=True,
        )
        logger.warning(f"节点数量超过限制，截断到 {MAX_TEST_NODES} 个")
        nodes = nodes[:MAX_TEST_NODES]

    # 转换为Clash格式
    print(f"\n转换为Clash订阅格式...", flush=True)
    logger.info("转换为Clash订阅格式...")
    subscription_file = os.path.join(
        os.path.dirname(args.output), "clash_subscription.yaml"
    )

    # 导入转换函数
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from src.utils import convert_nodes_to_subscription

    print(f"🔄 开始转换 {len(nodes)} 个节点为Clash格式...", flush=True)
    print(f"📋 转换进度: 0/0 开始...", flush=True)
    import time

    start_time = time.time()

    # 添加进度反馈
    print(f"🔄 正在调用转换函数处理 {len(nodes)} 个节点...", flush=True)
    logger.info(f"开始转换 {len(nodes)} 个节点")

    clash_config = convert_nodes_to_subscription.convert_nodes_to_clash(nodes)

    print(f"📋 转换进度: {len(nodes)}/{len(nodes)} 完成", flush=True)

    elapsed = time.time() - start_time
    print(f"⚡ Clash格式转换完成，耗时: {elapsed:.1f}秒", flush=True)

    # 保存Clash配置
    os.makedirs(os.path.dirname(subscription_file), exist_ok=True)
    with open(subscription_file, "w", encoding="utf-8") as f:
        yaml.dump(clash_config, f, allow_unicode=True, default_flow_style=False)

    print(f"✓ Clash订阅文件已保存: {subscription_file}", flush=True)
    logger.info(f"Clash订阅文件已保存: {subscription_file}")

    # 运行subs-check测试
    print(f"\n初始化测试器...", flush=True)
    tester = SubsCheckTester()

    # 计算并发数（根据CPU核心数）
    cpu_count = os.cpu_count() or 2
    concurrent = max(5, min(cpu_count * 5, 15))
    print(f"系统CPU核心数: {cpu_count}, 动态设置并发数: {concurrent}", flush=True)
    logger.info(f"系统CPU核心数: {cpu_count}, 动态设置并发数: {concurrent}")

    # 运行测试（配置将在run_phase1和run_phase2中创建）
    print(f"\n开始测试...", flush=True)
    success, message = tester.run_test(node_count=len(nodes))

    if not success:
        print(f"\n✗ 测试失败: {message}", flush=True)
        logger.error(f"测试失败: {message}")
        sys.exit(1)

    # 解析结果
    print(f"\n解析测试结果...", flush=True)
    logger.info("解析测试结果...")

    # 使用parse_results方法解析结果并重命名节点
    renamed_nodes = tester.parse_results()

    if renamed_nodes:
        # 保存重命名后的节点
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            for node in renamed_nodes:
                f.write(f"{node}\n")
        print(f"✓ 有效节点已保存到: {args.output} ({len(renamed_nodes)}个)", flush=True)
        logger.info(f"有效节点已保存到: {args.output}")
    else:
        print("⚠ 未找到有效节点", flush=True)
        logger.warning("未找到有效节点")
        # 保留原始Clash输出
        if os.path.exists(tester.output_file):
            import shutil

            shutil.copy(tester.output_file, args.output)
            logger.info(f"使用Clash格式输出: {args.output}")

    print(f"\n{'=' * 60}", flush=True)
    print("✓ 测试完成", flush=True)
    print(f"{'=' * 60}\n", flush=True)
    logger.info("✓ 测试完成")
    sys.exit(0)


if __name__ == "__main__":
    main()
