# 🎯 V2Ray节点收集器需求文档

## 📋 项目概述

**目标**：构建一个13个网站的V2Ray节点收集系统，每个网站独立实现，基于基础收集器架构。

## 🏗️ 架构设计

### 1. 入口文件
- **主入口**：`src/main.py`（唯一的入口文件）
- **配置**：`config/websites.py`（13个网站配置）
- **工具**：`utils/`（日志、文件处理等）

### 2. 收集器架构
```
src/collectors/
├── base_collector.py          # 基础收集器（抽象基类）
├── __init__.py              # 收集器模块初始化
├── freeclashnode.py        # FreeClashNode网站收集器
├── mibei77.py             # 米贝77网站收集器
├── clashnodev2ray.py       # ClashNodeV2Ray网站收集器
├── proxyqueen.py            # ProxyQueen网站收集器
├── wanzhuanmi.py          # 玩转迷网站收集器
├── cfmem.py               # CFMem网站收集器
├── clashnodecc.py          # ClashNodeCC网站收集器
├── datiya.py              # Datiya网站收集器
├── telegeam.py            # Telegeam网站收集器
├── clashgithub.py          # ClashGithub网站收集器
├── oneclash.py            # OneClash网站收集器
├── freev2raynode.py        # FreeV2RayNode网站收集器
└── eighty_five_la.py       # 85la网站收集器
```

### 3. 基础收集器（BaseCollector）

提供所有网站收集器的通用功能：
- HTTP请求管理
- HTML解析
- 节点提取（支持多种格式）
- 错误处理和日志
- 配置管理

## 🎯 核心功能需求

### 1. 网站收集器实现

每个网站的py文件必须继承BaseCollector并实现：

#### 必需方法
```python
class SiteCollector(BaseCollector):
    def _get_latest_article_url(self):
        """获取最新文章URL - 实现抽象方法"""
        # 实现网站特定的文章URL获取逻辑
        
    def get_latest_article_url(self, target_date=None):
        """获取文章URL，支持指定日期"""
        # 调用基类的get_latest_article_url(target_date)方法
```

#### 可选方法
```python
    def _get_links_from_article(self, article_url):
        """从文章中提取订阅链接（可选，使用基类默认方法）"""
        # 重写以实现网站特定的链接提取逻辑
        
    def _get_nodes_from_subscription(self, subscription_url):
        """从订阅链接获取节点（可选，使用基类默认方法）"""
        # 重写以实现网站特定的节点获取逻辑
```

### 2. 主流程控制（src/main.py）

负责协调调整个收集流程：

#### 主要职责
```python
def main():
    """主流程控制"""
    # 1. 初始化13个网站收集器
    # 2. 依次收集每个网站
    # 3. 为每个网站生成 YYYYMMDD_info.txt 文件
    # 4. 汇总所有节点到 nodetotal.txt
    # 5. 日志记录和错误处理
```

#### 信息文件生成
每個网站生成：
```
result/YYYYMMDD/{sitename}_info.txt
```

#### 详细工作流程

**两阶段执行流程：**

### 阶段1：链接收集阶段
对所有网站并行执行链接发现：

```
1. 网站初始化
    - 加载网站配置
    - 初始化收集器实例
    - 设置日志记录器

2. 获取文章URL
    - 访问网站主页
    - 查找最新文章链接（支持指定日期）
    - 记录文章URL到内存

3. 解析文章页面
    - 访问文章URL
    - 提取页面内容
    - 使用选择器查找订阅链接
    - 记录所有找到的订阅链接
    - 每个文章链接如果是正确的话，里面肯定有订阅链接，如果没找到，就要反思一下，看看是否是因为文章链接错误导致的，还是订阅地址的解析规则有问题

4. 生成信息文件
    - 创建日期目录
    - 写入网站信息文件
    - 格式：文章URL + 订阅链接列表
```

### 阶段2：统一节点解析阶段
对阶段1收集的所有订阅链接进行统一解析：

```
5. 批量收集节点
    - 对所有订阅链接发起请求（可并行）
    - 如果响应内容为空，要记录一下；非空的话如果找到的节点数量为0，就要反思一下，看看是否是因为订阅链接错误导致的，还是节点的解析规则有问题
    - 根据内容类型选择解析策略：
      a. 检测Base64编码 → 解码
      b. 检测JSON/YAML → 结构化解析
      c. 检测直接节点 → 文本提取
    - 清理和验证节点格式
    - 记录收集到的节点数量

6. 汇总去重
    - 汇总所有网站节点
    - 使用字符串哈希去重
    - 验证节点长度（≥20字符）
    - 双重保存nodetotal.txt文件：
      - 保存到日期目录：result/YYYYMMDD/nodetotal.txt
      - 同步保存到根目录：result/nodetotal.txt

7. 错误处理
    - 单个订阅链接失败不影响其他链接
    - 记录详细错误信息
    - 继续处理下一个网站
```

#### 文件格式要求
每个网站生成info文件，包含以下内容：

```text
# {网站名称} 文章和订阅链接
# 更新时间: YYYY-MM-DD HH:MM:SS
------------------------------------------------------------

## 文章链接
{article_url}

## 订阅链接
{subscription_link_1}
{subscription_link_2}
...
{subscription_link_N}
```

#### nodetotal.txt格式
```text
{节点1}
{节点2}
{节点3}
...
{节点N}
```
result/YYYYMMDD/{sitename}_info.txt
```

格式：
```text
# {网站名称} 文章和订阅链接
# 更新时间: YYYY-MM-DD HH:MM:SS
------------------------------------------------------------

## 文章链接
{article_url}

## 订阅链接
{subscription_link_1}
{subscription_link_2}
...
{subscription_link_N}
```

## 🎯 网站配置要求

### 1. config/websites.py

13个网站的配置信息：
```python
WEBSITES = {
    "freeclashnode": {
        "name": "FreeClashNode",
        "url": "https://www.freeclashnode.com/",
        "enabled": True,
        "selectors": [...],
    },
    "mibei77": {
        "name": "米贝77",
        "url": "https://www.mibei77.com/",
        "enabled": True,
        "selectors": [...],
    },
    # ... 其他11个网站
}
```

### 2. 支持的网站列表

1. freeclashnode
2. mibei77
3. clashnodev2ray
4. proxyqueen
5. wanzhuanmi
6. cfmem
7. clashnodecc
8. datiya
9. telegeam
10. clashgithub
11. oneclash
12. freev2raynode
13. eighty_five_la

## 🎯 输出文件要求

### 1. 目录结构
```
result/
├── YYYYMMDD/
│   ├── freeclashnode_info.txt
│   ├── mibei77_info.txt
│   ├── clashnodev2ray_info.txt
│   ├── proxyqueen_info.txt
│   ├── wanzhuanmi_info.txt
│   ├── cfmem_info.txt
│   ├── clashnodecc_info.txt
│   ├── datiya_info.txt
│   ├── telegeam_info.txt
│   ├── clashgithub_info.txt
│   ├── oneclash_info.txt
│   ├── freev2raynode_info.txt
│   ├── eighty_five_la_info.txt
│   └── nodetotal.txt               # 当日所有节点汇总（日期文件夹内）
├── nodetotal.txt                    # 所有节点汇总（根目录同步副本）
├── v2rayse.txt                     # V2RaySE网站收集的节点（独立文件）
└── karing.txt                      # Karing延迟测试后的有效节点（独立文件）
```

### 2. V2RaySE节点获取

**说明**：V2RaySE网站使用Playwright进行浏览器自动化收集，独立于13个网站的收集流程。

**工具**：`src/v2rayse_collector.py`

**输出文件**：`result/v2rayse.txt`

**订阅链接**：
```
https://raw.githubusercontent.com/yafeisun/v2raynode/refs/heads/main/result/v2rayse.txt
```

**特点**：
- 使用浏览器自动化技术，能够获取动态加载的节点
- 独立运行，不依赖13个网站收集器
- 每日自动更新，节点质量较高

### 3. Karing延迟测试

**说明**：对收集的节点进行延迟测试，筛选出延迟小于3000ms的有效节点。

**工具**：`src/speedtest/karing_latency_test.py`

**输入文件**：`result/nodetotal.txt`（或其他节点文件）

**输出文件**：`result/karing.txt`

**订阅链接**：
```
https://raw.githubusercontent.com/yafeisun/v2raynode/refs/heads/main/result/karing.txt
```

**测试标准**：
- 延迟测试：测试Google、Cloudflare等多个网站的访问延迟
- 过滤标准：延迟 < 3000ms
- 排序规则：按延迟从低到高排序
- 并发测试：最多同时测试10个节点

**使用方法**：
```bash
python3 src/speedtest/karing_latency_test.py result/nodetotal.txt result/karing.txt
```

**特点**：
- 基于真实的HTTP请求测试延迟
- 支持多种协议（vmess、vless、ss等）
- 自动过滤无效节点
- 提供详细的测试统计信息

### 2. 文件内容格式

#### info文件格式
```text
# {网站名称} 文章和订阅链接
# 更新时间: YYYY-MM-DD HH:MM:SS
------------------------------------------------------------

## 文章链接
{article_url}

## 订阅链接
{找到的订阅链接列表}
```

#### nodetotal.txt格式
```text
{节点1}
{节点2}
{节点3}
...
{节点N}
```

## 🎯 节点解析要求

### 1. 支持的格式
- **V2Ray协议**：vmess, vless, trojan, ss, ssr, hysteria, hysteria2
- **Base64编码**：自动检测和解码
- **JSON/YAML**：支持Clash配置格式
- **纯文本**：直接的节点链接

### 2. 解析流程
1. 从文章页面提取订阅链接
2. 从订阅链接获取节点内容
3. 根据内容类型选择解析策略
4. 清理和验证节点格式
5. 去重处理

### 3. 去重机制

- 每个网站收集的节点独立去重
- 所有网站汇总时再次去重
- 使用字符串哈希快速去重
- 节点长度验证（最小20字符）

## 🎯 错误处理要求

### 1. 单个网站失败
- 记录详细错误信息
- 继续处理下一个网站
- 不中断整个收集流程

### 2. 日志记录
- 使用统一的日志系统
- 记录收集过程中的关键信息
- 支持调试模式
- 日志级别：INFO（正常）、WARNING（警告）、ERROR（错误）
- 支持调试模式（DEBUG模式输出详细信息）

#### 2.1 日志格式规范
- **时间格式**：YYYY-MM-DD HH:MM:SS
- **日志内容格式**：`{收集器名称} - {日志级别} - {消息内容}`
- **日志分类**：
  - **访问日志**：网站访问、文章页面访问
  - **解析日志**：链接提取、内容解析、节点转换
  - **错误日志**：网络错误、解析错误、格式错误
  - **结果日志**：收集节点数量、成功率统计

#### 2.2 调试模式
- **启用方式**：环境变量 `DEBUG=true` 或配置文件设置
- **调试信息包括**：
  - 详细的HTTP请求信息（URL、状态码、响应时间）
  - 解析过程中的中间结果（正则匹配、DOM选择器结果）
  - 每个方法的执行流程和返回值
  - Base64解码过程的详细信息
  - 每次尝试的重试和延迟信息
- **生产环境**：不记录DEBUG信息，只记录INFO及以上级别

#### 2.3 日志输出示例
```
# 正常访问日志
2026-01-18 14:30:45,123 - FreeClashNode - INFO - 访问网站: https://www.freeclashnode.com/

# 解析日志
2026-01-18 14:30:46,234 - FreeClashNode - INFO - 从文章中找到 5 个订阅链接
2026-01-18 14:30:47,123 - FreeClashNode - INFO - 从订阅链接解析出 202 个节点

# 错误日志
2026-01-18 14:30:50,123 - FreeClashNode - ERROR - 获取订阅内容失败: https://node.freeclashnode.com/uploads/2026/01/1-20260118.txt - Connection timeout

# 调试模式日志（DEBUG=true）
2026-01-18 14:30:45,124 - FreeClashNode - DEBUG - 正在请求: https://www.freeclashnode.com/ (尝试 1/3)
2026-01-18 14:30:45,456 - FreeClashNode - DEBUG - 请求成功: 状态码 200 (耗时 1.23s)
2026-01-18 14:30:45,467 - FreeClashNode - DEBUG - 正则匹配到订阅链接: 5 个
2026-01-18 14:30:47,123 - FreeClashNode - INFO - 从订阅链接解析出 202 个节点
```

#### 2.4 日志文件管理
- **日志文件位置**：`data/logs/collector_YYYYMMDD.log`
- **日志文件命名**：按日期自动轮转，保留最近7天
- **日志级别设置**：`utils/logger.py` 中的 `LOG_LEVEL` 常量
- **日志文件大小限制**：单个日志文件不超过50MB，超过后自动创建新文件

#### 2.5 重要提示
- 日志文件不包含敏感信息（密码、密钥等）
- 所有网络请求都记录（成功和失败）
- 每个收集器独立记录，避免日志交叉
- 在生产环境中，只记录INFO及以上级别，避免日志过多

### 3. 错误类型分类

#### 3.1 网络错误
- **连接超时**（requests.exceptions.Timeout）
- **连接失败**（requests.exceptions.ConnectionError）
- **HTTP错误**（404, 500, 503等状态码）
- **SSL错误**（requests.exceptions.SSLError）

#### 3.2 解析错误
- **HTML解析失败**（找不到选择器、DOM结构异常）
- **JSON/YAML解析失败**（格式错误、缺少必要字段）
- **Base64解码失败**（解码异常、格式错误）
- **节点转换失败**（字段缺失、格式不匹配）

#### 3.3 文件错误
- **文件写入失败**（磁盘空间、权限问题）
- **目录创建失败**（路径错误）

### 4. 错误处理策略

#### 4.1 网络错误处理
- **超时自动重试**（最多3次，每次间隔2秒递增）
- **代理失败后尝试直连**
- **404错误立即返回，不重试**
- **500错误等待后重试**

#### 4.2 解析错误处理
- **使用try-except包裹关键解析逻辑**
- **记录具体的异常信息和堆栈（仅在DEBUG模式）**
- **提供友好的错误消息**（"无法获取文章内容"而不是"Error"）
- **单个节点解析失败不影响其他节点**

#### 4.3 文件操作错误处理
- **使用os.makedirs(..., exist_ok=True)避免重复创建**
- **文件写入失败后记录错误，但不抛出异常**

### 5. 错误恢复策略
- **自动恢复**：失败的操作自动重试（网络请求、文件写入）
- **优雅降级**：某功能失败时使用备用方案
- **手动标记**：对于持续失败的资源，在配置中标记为禁用
- **部分成功处理**：即使部分失败，也要记录成功收集到的节点

### 6. 错误信息格式
```
# 网络错误示例
2026-01-18 14:30:50,123 - FreeClashNode - ERROR - 获取订阅内容失败: https://node.freeclashnode.com/uploads/2026/01/1-20260118.txt - Connection timeout (重试3次后放弃)

# 解析错误示例
2026-01-18 14:30:47,234 - FreeClashNode - WARNING - YAML解析失败: 代理缺少必要字段 server - 跳过该节点 (共3个类似错误)
2026-01-18 14:30:47,456 - FreeClashNode - ERROR - Base64解码失败: 字符串长度不是4的倍数 (错误格式，尝试其他解析方式)

# 文件操作错误示例
2026-01-18 14:30:50,123 - main - ERROR - 写入节点文件失败: result/20260118/nodetotal.txt - [Errno 28] No space left on device
```

### 7. 错误报告要求
- **错误统计**：记录每种错误类型的次数和占比
- **错误聚合**：相同错误只记录一次（如连续10次404）
- **错误趋势**：跟踪最近24小时的错误变化趋势
- **告警阈值**：错误率超过30%时触发警告

## 🎯 性能要求

### 1. 请求控制
- 遵守robots.txt
- 实现合理的请求延迟
- 支持代理配置
- 超时和重试机制

### 2. 并发处理
- 每个网站独立处理，避免相互影响
- 合理的并发控制

## 🎯 兼容性要求

### 1. Python版本
- 支持Python 3.8+
- 避免使用过时的语法

### 2. 依赖管理
- 在requirements.txt中明确所有依赖
- 保持依赖版本兼容性

## 🎯 部署要求

### 1. GitHub Actions
- 自动化每日收集
- 提交收集结果到仓库
- 错误通知机制

### 2. 本地运行
- 支持命令行参数
- 灵活的配置选项
- 友好的用户界面

## 🎯 质量要求

### 1. 代码规范
- 遵循PEP 8编码规范
- 添加必要的注释和文档
- 统一的错误处理模式
- 代码块不应很长，保持每个函数的功能独立性，提高代码复用性
- 文件新增或修改时，要检查新增必要性，检查是否有重复代码或冗余逻辑
- 及时删除不再需要的临时代码或注释
- push pull操作可以无视result目录下的文件

### 2. 测试覆盖
- 每个网站收集器独立测试
- 基础功能的单元测试
- 集成测试流程

## 🎯 文档要求

### 1. 代码文档
- 清晰的方法注释
- 复杂逻辑的说明
- 使用示例和模板

### 2. 用户文档
- 安装和配置指南
- 使用说明和FAQ
- 故障排除指南

---

**说明**：本文档整合了所有临时报告和需求，作为项目开发的权威参考。所有后续开发应严格按照本文档执行。

## 🔧 修复规范

### 修复原则
- 只修复功能性错误，不重构代码
- 保持现有代码风格，不添加新功能
- 简化复杂逻辑，保持代码清晰
- 移除重复代码，提高可读性
- 所有修复必须向后兼容

### 修复流程
1. 识别问题源：LSP错误、导入错误、运行时错误
2. 定位根本原因：方法名不匹配、属性不存在、逻辑错误
3. 最小化修改：只修复必要部分，避免连带修改
4. 测试验证：修复后必须可以正常导入和运行
5. 记录修复内容：提交记录到LOG中说明修复原因和范围

### 禁止行为
- **禁止的修复操作**：
  - ❌ 不要大规模重构：禁止为了"修复"而重写整个收集器
  - ❌ 不要添加新功能：修复期间不添加新特性
  - ❌ 不要更改架构：保持现有的简化架构
  - ❌ 不要添加临时文件：不允许创建中间修复文件
  - ❌ 不要删除原始文件：保留原始复杂版本作为备份

### 修复范围限制
- **允许的修复内容**：
  - ✅ 修复抽象方法实现：修复`_get_latest_article_url`方法不匹配问题
  - ✅ 修复方法调用错误：修复调用不存在的基类方法
  - ✅ 修复属性访问错误：修复访问不存在的实例属性
  - ✅ 修复导入路径问题：确保所有模块可以正常导入
  - ✅ 修复语法错误：修复明显的语法和类型错误
  - ✅ 修复逻辑错误：修复简单的逻辑判断和处理问题

- **需要记录的修复内容**：
  - 修复的具体问题：LSP错误、运行时错误、导入问题
  - 修复的具体代码：修改的文件、行数、修复方法
  - 修复的原因：根本原因分析、解决方案选择
  - 修复的结果：是否成功、测试结果

## 🔧 AI协作要求

**AI必须遵守的修复规范**：
1. 问题分析：在修复前必须深入分析现有代码，理解问题根源和影响范围
2. 方案设计：提出最小化修复方案，避免不必要的连带修改，修改必要性要跟用户解释清楚
3. 逐个验证：每个修复完成后必须立即测试验证
4. 客观记录：所有修复决策和结果都要客观记录在LOG中
5. 不冒失修复：严格按照规范要求，避免过度修改

**修复工作流示例**：
1. 问题：`_get_latest_article_url`方法返回类型不匹配
   - 修复：调整返回类型为`None`，保持与基类一致
2. 问题：模块导入路径错误
   - 修复：添加正确的sys.path配置，避免硬编码
3. 问题：访问不存在的基类方法
   - 修复：检查基类可用方法，只调用已存在的方法

## 🎯 实现优先级

### 高优先级
- [x] 基础收集器完善
- [x] 13个网站收集器实现
- [x] 主流程控制逻辑
- [x] 错误处理和日志

### 中优先级
- [ ] 性能优化
- [ ] 单元测试
- [ ] 部署自动化
- [ ] 文档完善

### 低优先级
- [ ] 监控和统计
- [ ] 用户界面优化
- [ ] 扩展性设计
---
