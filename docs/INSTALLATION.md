# 📦 安装指南

本文档提供详细的安装步骤，帮助你快速部署V2Ray节点收集器。

---

## 📋 目录

- [系统要求](#系统要求)
- [快速安装](#快速安装)
- [详细安装](#详细安装)
- [Docker安装](#docker安装)
- [验证安装](#验证安装)
- [常见安装问题](#常见安装问题)
- [卸载](#卸载)

---

## 💻 系统要求

### 最低要求
- **Python**: 3.8 或更高版本
- **磁盘空间**: 至少 500MB
- **内存**: 至少 512MB
- **网络**: 稳定的互联网连接

### 推荐配置
- **Python**: 3.10 或更高版本
- **磁盘空间**: 1GB
- **内存**: 1GB
- **网络**: 宽带连接

### 支持的操作系统
- ✅ Linux (Ubuntu, Debian, CentOS, Fedora, Arch)
- ✅ macOS (10.15+)
- ✅ Windows (10+)
- ✅ Windows Server (2016+)

---

## 🚀 快速安装

### Linux / macOS

```bash
# 1. 克隆仓库
git clone https://github.com/yafeisun/v2raynode.git
cd v2raynode

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行收集器
python3 run.py --collect
```

### Windows

```powershell
# 1. 克隆仓库
git clone https://github.com/yafeisun/v2raynode.git
cd v2raynode

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行收集器
python run.py --collect
```

---

## 📖 详细安装

### 步骤1: 安装Python

#### Ubuntu / Debian

**检查Python版本**:
```bash
python3 --version
```

**如果版本低于3.8**:
```bash
# 添加Python 3.10 PPA
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# 安装Python 3.10
sudo apt install python3.10 python3.10-venv python3.10-dev

# 设置为默认（可选）
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
```

**安装pip**:
```bash
sudo apt install python3-pip
pip3 install --upgrade pip
```

#### CentOS / RHEL / Fedora

```bash
# CentOS/RHEL 7/8
sudo yum install python3 python3-pip

# Fedora
sudo dnf install python3 python3-pip
```

#### macOS

**使用Homebrew**:
```bash
# 安装Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Python
brew install python@3.10

# 验证安装
python3.10 --version
```

#### Windows

**方法1: 官方安装包**
1. 访问 [python.org](https://www.python.org/downloads/)
2. 下载Python 3.10或更高版本
3. 运行安装程序
4. ⚠️ **重要**: 勾选"Add Python to PATH"
5. 完成安装

**方法2: 使用Chocolatey**
```powershell
# 安装Chocolatey（如果没有）
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装Python
choco install python
```

**验证安装**:
```powershell
python --version
pip --version
```

---

### 步骤2: 安装Git

#### Linux
```bash
# Ubuntu/Debian
sudo apt install git

# CentOS/RHEL/Fedora
sudo yum install git

# Arch
sudo pacman -S git
```

#### macOS
```bash
# 使用Homebrew
brew install git

# 或使用Xcode命令行工具
xcode-select --install
```

#### Windows

**方法1: 下载安装包**
1. 访问 [git-scm.com](https://git-scm.com/downloads)
2. 下载Windows版Git
3. 运行安装程序
4. 使用默认设置

**方法2: 使用Chocolatey**
```powershell
choco install git
```

---

### 步骤3: 克隆仓库

```bash
# 克隆主仓库
git clone https://github.com/yafeisun/v2raynode.git

# 进入项目目录
cd v2raynode

# 查看项目结构
ls -la
```

**使用SSH克隆（如果配置了SSH密钥）**:
```bash
git clone git@github.com:yafeisun/v2raynode.git
```

**使用镜像站点（如果GitHub访问慢）**:
```bash
git clone https://gitee.com/mirrors/v2raynode.git
```

---

### 步骤4: 安装Python依赖

#### 方法1: 使用pip安装（推荐）

```bash
# 升级pip
pip install --upgrade pip

# 安装所有依赖
pip install -r requirements.txt
```

**使用国内镜像源（如果下载慢）**:
```bash
# 清华镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 阿里云镜像
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 豆瓣镜像
pip install -r requirements.txt -i https://pypi.douban.com/simple/
```

#### 方法2: 使用虚拟环境（推荐）

**创建虚拟环境**:
```bash
# Linux/macOS
python3 -m venv venv

# Windows
python -m venv venv
```

**激活虚拟环境**:
```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**安装依赖**:
```bash
pip install -r requirements.txt
```

**退出虚拟环境**:
```bash
deactivate
```

#### 方法3: 逐个安装依赖

```bash
# 核心依赖
pip install requests beautifulsoup4 lxml urllib3

# 数据处理
pip install numpy pandas

# 异步HTTP
pip install aiohttp async-timeout

# Telegram API
pip install telethon python-telegram-bot

# 加密
pip install pycryptodome

# 配置
pip install python-dotenv

# 日志
pip install colorlog

# Git操作
pip install GitPython

# 调度
pip install APScheduler

# Web框架
pip install Flask FastAPI websockets
```

---

### 步骤5: 配置项目

#### 基本配置

**编辑配置文件**:
```bash
# 全局配置
nano config/settings.py

# 网站配置
nano config/websites.py
```

**常用配置项**:
```python
# config/settings.py

# 连接超时
CONNECTION_TIMEOUT = 10

# 最大并发数
MAX_WORKERS = 10

# 请求超时
REQUEST_TIMEOUT = 30

# 调试模式
DEBUG = True

# 日志级别
LOG_LEVEL = "INFO"
```

#### 代理配置（如果需要）

**临时设置**:
```bash
export http_proxy=http://127.0.0.1:10808/
export https_proxy=http://127.0.0.1:10808/
```

**永久设置**:
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export http_proxy=http://127.0.0.1:10808/' >> ~/.bashrc
echo 'export https_proxy=http://127.0.0.1:10808/' >> ~/.bashrc
source ~/.bashrc
```

**配置文件方式**:
```bash
# 创建环境变量文件
cat > .env << EOF
HTTP_PROXY=http://127.0.0.1:10808/
HTTPS_PROXY=http://127.0.0.1:10808/
EOF

# 在代码中加载
from dotenv import load_dotenv
load_dotenv()
```

---

## 🐳 Docker安装

### 使用Docker运行（推荐）

**创建Dockerfile**:
```dockerfile
FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 克隆项目
RUN git clone https://github.com/yafeisun/v2raynode.git /app
WORKDIR /app

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建数据目录
RUN mkdir -p /app/data /app/result

# 设置工作目录
WORKDIR /app

# 默认命令
CMD ["python3", "run.py", "--collect"]
```

**构建镜像**:
```bash
docker build -t v2ray-node-collector .
```

**运行容器**:
```bash
# 运行收集器
docker run --rm v2ray-node-collector

# 挂载卷保存结果
docker run --rm -v $(pwd)/result:/app/result v2ray-node-collector

# 使用环境变量配置
docker run --rm -e HTTP_PROXY=http://127.0.0.1:10808 v2ray-node-collector
```

**使用Docker Compose**:

创建 `docker-compose.yml`:
```yaml
version: '3.8'

services:
  v2ray-collector:
    build: .
    container_name: v2ray-collector
    volumes:
      - ./result:/app/result
      - ./data:/app/data
    environment:
      - HTTP_PROXY=${HTTP_PROXY}
      - HTTPS_PROXY=${HTTPS_PROXY}
      - DEBUG=false
    restart: unless-stopped
```

**启动服务**:
```bash
# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

---

## ✅ 验证安装

### 1. 验证Python环境

```bash
# 检查Python版本
python3 --version
# 输出: Python 3.8+

# 检查pip
pip3 --version

# 测试导入关键模块
python3 -c "import requests, bs4, asyncio; print('✅ Python环境正常')"
```

### 2. 验证项目结构

```bash
# 查看项目文件
ls -la

# 检查关键文件
ls -l config/
ls -l src/
ls -l src/collectors/
```

### 3. 验证依赖安装

```bash
# 列出已安装的包
pip list

# 检查关键依赖
pip show requests
pip show beautifulsoup4
pip show aiohttp
```

### 4. 运行测试

```bash
# 运行基本测试
python3 -m pytest tests/test_basic.py -v

# 如果没有pytest，先安装
pip install pytest
```

### 5. 测试收集器

```bash
# 测试单个网站
python3 src/main.py --sites telegeam

# 查看输出
ls -lh result/

# 查看日志
tail -20 data/logs/collector_$(date +%Y%m%d).log
```

### 6. 完整验证

```bash
# 运行完整收集
python3 run.py --collect

# 检查结果
python3 run.py --status

# 如果成功，应该看到:
# ✅ 收集完成
# 📊 统计信息...
```

---

## 🛠️ 常见安装问题

### 问题1: Python版本不兼容

**错误**:
```
ERROR: Python 3.7.0 is not supported. Please use Python 3.8+
```

**解决方案**:

**Ubuntu/Debian**:
```bash
sudo apt install python3.10
python3.10 --version
```

**macOS**:
```bash
brew install python@3.10
python3.10 --version
```

**Windows**:
从 [python.org](https://www.python.org/downloads/) 下载Python 3.10+

---

### 问题2: pip安装失败

**错误**:
```
ERROR: Could not find a version that satisfies the requirement xxx
```

**解决方案**:

**方案1: 升级pip**
```bash
pip install --upgrade pip
```

**方案2: 使用镜像源**
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**方案3: 使用虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 问题3: Git克隆失败

**错误**:
```
fatal: unable to access 'https://github.com/...': Failed to connect
```

**解决方案**:

**方案1: 使用代理**
```bash
git config --global http.proxy http://127.0.0.1:10808
git config --global https.proxy http://127.0.0.1:10808
```

**方案2: 使用SSH**
```bash
git clone git@github.com:yafeisun/v2raynode.git
```

**方案3: 使用镜像站点**
```bash
git clone https://gitee.com/mirrors/v2raynode.git
```

---

### 问题4: 权限问题

**错误**:
```
Permission denied: '/usr/local/lib/python3.x/...'
```

**解决方案**:

**方案1: 使用虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**方案2: 使用用户安装**
```bash
pip install --user -r requirements.txt
```

**方案3: 使用sudo（不推荐）**
```bash
sudo pip install -r requirements.txt
```

---

### 问题5: 依赖冲突

**错误**:
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed
```

**解决方案**:

**方案1: 创建新虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**方案2: 更新所有包**
```bash
pip install --upgrade --force-reinstall -r requirements.txt
```

**方案3: 单独安装冲突的包**
```bash
pip install package_name --force-reinstall
```

---

## 🗑️ 卸载

### Linux / macOS

```bash
# 1. 删除项目目录
cd ~
rm -rf v2raynode

# 2. 删除虚拟环境（如果使用）
rm -rf ~/venv

# 3. 卸载依赖包（可选）
pip uninstall -y -r v2raynode/requirements.txt

# 4. 清理缓存（可选）
pip cache purge
```

### Windows

```powershell
# 1. 删除项目目录
Remove-Item -Recurse -Force v2raynode

# 2. 删除虚拟环境（如果使用）
Remove-Item -Recurse -Force venv

# 3. 卸载依赖包（可选）
pip uninstall -y -r v2raynode\requirements.txt
```

### Docker

```bash
# 删除镜像
docker rmi v2ray-node-collector

# 删除容器
docker rm v2ray-collector

# 清理未使用的资源
docker system prune -a
```

---

## 📚 下一步

安装完成后，请查看:

- 🚀 [快速开始指南](QUICK_START.md) - 快速上手
- 📖 [使用说明](USAGE.md) - 详细的使用教程
- ❓ [常见问题](FAQ.md) - 解决常见问题
- 🏗️ [项目架构](ARCHITECTURE.md) - 了解项目架构

---

## 🆘 获取帮助

如果遇到安装问题:

1. 查看 [常见问题](FAQ.md)
2. 查看 [故障排除](PROXY_TROUBLESHOOTING.md)
3. 在GitHub提交Issue: https://github.com/yafeisun/v2raynode/issues

---

**安装完成！🎉 现在可以开始使用V2Ray节点收集器了！**
