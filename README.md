# 🌐 Free V2Ray Daily Node Collector

> 每日自动收集、测试和更新免费V2Ray节点的开源工具

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-passing-brightgreen.svg)](.github/workflows)
[![Last Update](https://img.shields.io/badge/last%20update-daily-orange.svg)](https://github.com/yafeisun/v2raynode)

---

## 📱 订阅链接

直接使用以下订阅链接导入到V2Ray客户端，无需本地运行。

### 所有节点订阅链接

包含从所有支持的网站收集的所有节点，每日自动更新。

```
https://raw.githubusercontent.com/yafeisun/v2raynode/refs/heads/main/result/nodetotal.txt
```

### V2RaySE节点订阅链接

V2RaySE网站使用浏览器自动化收集的节点，4h更新一次。

```
https://raw.githubusercontent.com/yafeisun/v2raynode/refs/heads/main/result/v2rayse.txt
```

### Karing延迟测试订阅链接

经过延迟测试（<3000ms）筛选的有效节点，按延迟排序。

```
https://raw.githubusercontent.com/yafeisun/v2raynode/refs/heads/main/result/karing.txt
```

### 导入到V2Ray客户端

**V2RayN / V2RayNG**:
1. 打开客户端
2. 复制上述订阅链接
3. 在"订阅"选项中点击"从剪贴板导入"
4. 更新订阅即可

**Clash / ClashX**:
1. 打开客户端
2. 进入"Profiles"或"配置"页面
3. 点击"Download"或"New"
4. 粘贴订阅链接
5. 下载并应用配置

---

## 🎯 项目简介

**Free V2Ray Daily Node Collector** 是一个自动化工具，用于每日收集、测试和更新免费V2Ray节点。项目采用插件化架构，支持并发收集、节点验证、速度测试和自动部署到GitHub。

### 应用场景

- 🌍 **网络访问**: 获取稳定的代理节点用于访问全球网络
- 🚀 **性能测试**: 测试不同地区的网络质量和延迟
- 🔬 **技术研究**: 学习V2Ray协议和节点收集技术
- 📊 **数据分析**: 分析免费节点的可用性和稳定性

---

## ✨ 核心特点

### 🚀 高效收集
- **多源并发**: 同时从多个网站收集节点
- **智能去重**: 自动去除重复节点
- **格式修复**: 修复错误编码的节点链接
- **Base64解码**: 支持Base64编码的节点提取

### ✅ 节点验证
- **连通性测试**: TCP连接测试验证节点可用性
- **智能筛选**: 基于速度和可靠性的自动筛选

### 🏗️ 插件化架构
- **零代码添加**: 新增网站只需2个文件
- **动态加载**: 自动发现和注册收集器
- **配置驱动**: 通过配置文件控制一切
- **易于扩展**: 清晰的接口设计

### 🤖 自动化部署
- **GitHub Actions**: 每日自动收集和更新
- **自动提交**: 自动提交测试结果到仓库
- **状态监控**: 实时监控收集状态

### 📋 核心工作流程

**两阶段节点收集流程**：

**阶段1：链接收集**
1. 查找今日文章链接 → 提取订阅链接 → 记录到内存
2. 所有网站并行处理，避免相互影响

**阶段2：统一解析**
1. 对所有收集的订阅链接进行统一解析
2. 去重机制：订阅链接去重 + 节点server:port去重
3. 双重保存：`result/{date}/nodetotal.txt` + `result/nodetotal.txt`

**Karing延迟测试流程**：
1. 使用Karing延迟测试工具测试节点延迟
2. 过滤标准：延迟 < 3000ms
3. 按延迟排序 → 保存到 `result/karing.txt`

---

## 📊 性能指标

| 指标 | 数值 |
|-----|------|
| 🔄 更新频率 | 每日自动更新 |
| 🎯 支持协议 | vmess, vless, trojan, ss, ssr, hysteria |

---

## 🛠️ 配置说明

### 支持的网站

项目支持以下免费节点源（自动按顺序收集）:

| 序号 | 网站名称 | 网站地址 | 特点 |
|-----|---------|---------|------|
| 1 | FreeClashNode | https://www.freeclashnode.com/free-node/ | Clash节点 |
| 2 | 米贝节点 | https://www.mibei77.com/ | 中文节点 |
| 3 | ClashNodeV2Ray | https://clashnodev2ray.github.io/ | GitHub源 |
| 4 | ProxyQueen | https://www.proxyqueen.top/ | 代理节点 |
| 5 | 玩转迷 | https://wanzhuanmi.com/ | 综合节点 |
| 6 | CFMem | https://www.cfmem.com/ | Cloudflare节点 |
| 7 | ClashNodeCC | https://clashnode.cc/ | Clash节点 |
| 8 | Datiya | https://free.datiya.com/ | 免费节点 |
| 9 | Telegeam | https://telegeam.github.io/clashv2rayshare/ | Telegram分享 |
| 10 | ClashGithub | https://clashgithub.com/ | GitHub节点 |
| 11 | OneClash | https://oneclash.cc/freenode | Clash节点 |
| 12 | FreeV2rayNode | https://www.freev2raynode.com/ | V2Ray专用 |
| 13 | 85LA | https://www.85la.com/internet-access/free-network-nodes | 综合资源 |
| 14 | Xinye | https://www.xinye.eu.org/ | GitHub raw 源 |
| 15 | StairNode | https://www.stairnode.com/freenode | 免费节点 |

详细的网站配置请查看: [config/websites.py](config/websites.py)

## 📚 文档导航

### 用户指南
- [快速开始指南](docs/QUICK_START.md) - 详细的快速上手教程
- [安装指南](docs/INSTALLATION.md) - 完整的安装步骤

### 开发者指南
- [项目架构](docs/ARCHITECTURE.md) - 架构设计说明
- [需求文档](REQUIREMENT.MD) - 项目需求说明

### 技术报告
- [更新日志](CHANGELOG.md) - 版本更新记录

---

## 📜 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

```
MIT License

Copyright (c) 2026 yafeisun

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## ⚖️ 免责声明

本项目仅供**学习交流和技术研究**使用，请遵守当地法律法规。使用本项目的任何功能所产生的一切后果由使用者自行承担，项目作者不承担任何责任。

- 🔒 请勿用于任何非法用途
- 🌐 尊重网络服务提供商的使用条款
- 📚 建议仅用于技术学习和个人使用
- ⚠️ 本项目不保证节点的稳定性和可用性

</div>
