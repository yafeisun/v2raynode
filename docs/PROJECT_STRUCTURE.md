# 项目结构说明

## 📁 目录结构总览

```
v2raynode/
├── src/                          # 源代码
│   ├── core/                     # ⭐ 核心模块
│   │   ├── base_collector.py     # 基础收集器类
│   │   ├── subscription_parser.py # 统一订阅解析器
│   │   ├── collector_manager.py  # 收集器管理器
│   │   └── ...                   # 其他核心模块
│   ├── collectors/               # ⭐ 收集功能 - 各网站收集器
│   │   ├── mibei77.py           # 米贝77
│   │   ├── freeclashnode.py     # FreeClashNode
│   │   ├── cfmem.py             # CFMem
│   │   └── ...                  # 其他10个网站
│   ├── utils/                   # 通用工具
│   ├── cli/                     # 命令行工具
│   └── main.py                  # 主入口
├── config/                      # 配置文件
├── result/                      # 输出结果
└── docs/                        # 文档
```

## 🎯 功能模块划分

### 1. 节点收集 (Primary Function)
**位置**: `src/collectors/` + `src/core/`
**职责**:
- 各网站收集器：解析特定网站的文章和订阅链接
- 核心模块：统一的基础收集器和订阅解析逻辑

## 🚀 GitHub Actions

### Action 1: 节点收集
```yaml
- name: 收集节点
  run: python3 src/main.py
```

## 📋 设计原则

1. **模块化**：核心功能集中，网站特定逻辑分离
2. **可扩展**：易于添加新的收集器
3. **统一接口**：所有收集器使用相同的基类和解析器

## 🔧 使用说明

### 收集节点
```bash
python3 src/main.py --sites mibei77 cfmem
```