# 📁 项目架构说明

## 🎯 项目概述

这是一个自动化的V2Ray节点收集和测试系统，每日从多个免费节点网站收集最新的V2Ray节点。项目采用模块化架构，支持13个主流免费V2Ray节点网站，具备自动文章链接收集、订阅链接提取、连通性测试和GitHub自动化部署功能。

### 主要特性
- 🌐 **多网站支持**: 支持13个主流免费V2Ray节点网站
- 📰 **文章链接收集**: 自动获取每个网站最新发布的文章链接
- 🔗 **订阅链接提取**: 自动提取V2Ray订阅链接，支持Base64解码
- 🧪 **连通性测试**: 自动测试节点可用性，丢弃超时节点
- 🌍 **多地区节点**: 包含香港、美国、欧洲等多个地区的节点
- 📁 **统一保存**: 所有有效节点统一保存到nodelist.txt文件
- ⚡ **独立脚本**: 每个网站都有独立的收集脚本
- 🤖 **自动化**: 支持GitHub Actions自动部署

### 技术栈
- **语言**: Python 3.8+
- **网络请求**: requests库
- **HTML解析**: BeautifulSoup4 + lxml
- **版本控制**: Git + GitHub Actions
- **日志系统**: Python logging
- **数据处理**: 正则表达式 + Base64编码

## 目录结构

```
v2raynode/
├── 📄 README.md                 # 项目主文档
├── 📄 LICENSE                   # MIT许可证
├── 📄 requirements.txt          # Python依赖
├── 📄 .gitignore               # Git忽略文件
├── 📄 main.py                  # 主程序入口
│
├── 📂 src/                      # 核心源代码
│   ├── 📂 collectors/           # 节点收集器
│   ├── 📂 core/                 # 核心模块
│   ├── 📂 utils/                # 工具函数
│   └── 📂 cli/                  # 命令行工具
│
├── 📂 config/                   # 配置文件
│   ├── settings.py              # 主配置
│   └── websites.py              # 网站配置
│
├── 📂 tests/                    # 测试文件
│
├── 📂 docs/                     # 文档
│   ├── README_ORIGINAL.md       # 原始README
│   ├── CHANGELOG.md             # 更新日志
│   ├── DOCUMENTATION_ANALYSIS_REPORT.md  # 文档分析
│   ├── HARD_REQUIREMENTS.md     # 需求文档
│   ├── IFLOW.md                 # 流程文档
│   └── ARCHITECTURE.md         # 架构说明
│
├── 📂 data/                     # 数据存储
│   └── 📂 logs/                  # 日志文件
│
├── 📂 result/                   # 结果输出
│   ├── 📂 {date}/               # 按日期归档
│   ├── nodetotal.txt           # 所有节点
│   └── nodelist.txt            # 测速后节点
│
├── 📂 .github/                  # GitHub配置
│   └── 📂 workflows/            # Actions工作流
│       ├── update_nodes.yml     # 节点收集
│       └── test_nodes.yml       # 节点测速
│
├── 📂 .iflow/                   # iflow配置
└── 📂 .specify/                 # specify配置
```

## 核心组件说明

### 🎯 主要模块

- **main.py**: 主程序入口，协调收集流程
- **src/collectors/**: 13个网站的节点收集器
- **src/cli/speedtest/**: 节点测速和媒体检测
- **src/utils/**: 通用工具函数（日志、文件处理等）

### 🔄 工作流程

1. **节点收集阶段** (`main.py`):
   - 遍历13个网站收集文章链接和订阅链接
   - 通过订阅链接获取节点
   - 去重并保存到 `result/{date}/nodetotal.txt`

### 📁 数据流向

```
网站 → 订阅链接 → 节点 → 去重 → nodetotal.txt → 测速 → nodelist.txt
```

### 🔌 可插拔架构

本项目采用可插拔架构，支持动态加载收集器插件。新增网站时只需要添加配置和收集器类，无需修改其他文件。

#### 架构优势
1. **零代码添加新网站**
   - 只需创建收集器类和配置文件
   - 无需修改主程序或导入文件
   - 自动发现和加载新插件

2. **配置驱动**
   - 通过配置文件控制网站启用/禁用
   - 配置文件指定收集器插件
   - 支持灵活的参数配置

3. **统一入口**
   - 所有网站使用统一的脚本入口
   - 标准化的收集器接口
   - 统一的错误处理和日志记录

### 🛠️ 外部依赖

- **Cloudflare WARP**: 代理服务（GitHub Actions）
- **BeautifulSoup4**: HTML解析
- **requests**: HTTP请求

## 开发和维护

### 🚀 快速开始

```bash
# 本地运行
python3 -m src.main --collect

# 查看帮助
python3 -m src.main --help
```

### 📊 监控

- GitHub Actions自动运行
- 日志保存在 `data/logs/`
- 结果保存在 `result/` 目录

### 🧹 清理

- 文档统一在 `docs/` 目录
- 自动清理7天前的日志

## 注意事项

1. **不要直接编辑** `src/collectors/base_collector.py` 中的逻辑
2. **添加新网站** 需要更新 `config/websites.py`
3. **修改工作流** 需要更新 `.github/workflows/` 中的yml文件
4. **测试新功能** 请在 `tests/` 目录添加测试用例

---

*此文档描述了项目的整体架构，便于新开发者快速理解项目结构。*