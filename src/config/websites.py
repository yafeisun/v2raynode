#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网站配置文件
"""

# 目标网站列表 - 配置驱动的插件架构
WEBSITES = {
    "freeclashnode": {
        "name": "FreeClashNode",
        "url": "https://www.freeclashnode.com/free-node/",
        "enabled": True,
        "collector_key": "freeclashnode",  # 对应收集器插件的关键字
        "selectors": [".post-title a", "h2 a", ".entry-title a", "article h2 a"],
        "patterns": [
            r"node\.freeclashnode\.com/uploads/\d{4}/\d{2}/[^\\s\\<]*\.(?:txt|yaml|json)"
        ],
    },
    "mibei77": {
        "name": "米贝节点",
        "url": "https://www.mibei77.com/",
        "enabled": True,
        "collector_key": "mibei77",  # 对应收集器插件的关键字
        "selectors": [
            ".post h2 a",
            ".entry-title a",
            "h1 a",
            ".post-title a",
            'a[href*="/2025"]',
            'a[href*="/2025/12"]',
        ],
        "patterns": [
            r'https?://[^\s\'"]*?/sub[^\s\'"]*?',
            r'https?://[^\s\'"]*?/subscribe[^\s\'"]*?',
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
        ],
    },
    "clashnodev2ray": {
        "name": "ClashNodeV2Ray",
        "url": "https://clashnodev2ray.github.io/",
        "enabled": False,  # 网站已停止更新（2025年后无新内容）
        "collector_key": "clashnodev2ray",  # 对应收集器插件的关键字
        "selectors": [
            "h1 a",
            ".post-title a",
            "article h1 a",
            "h2 a",
            'a[href*="/2025"]',
            'a[href*="/2025/12"]',
        ],
        "patterns": [
            r"vmess://[^\s\n\r]+",
            r"vless://[^\s\n\r]+",
            r"trojan://[^\s\n\r]+",
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
        ],
    },
    "proxyqueen": {
        "name": "ProxyQueen",
        "url": "https://www.proxyqueen.top/",
        "enabled": True,
        "collector_key": "proxyqueen",  # 对应收集器插件的关键字
        "selectors": [".post-title a", "h2 a", ".entry-header a", "article h2 a"],
        "patterns": [
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*?(?:vmess|vless|trojan|hysteria|ss)[^\s\'"]*',
        ],
    },
    "wanzhuanmi": {
        "name": "玩转迷",
        "url": "https://wanzhuanmi.com/",
        "enabled": False,  # 网站已停止更新（2025年后无新内容）
        "collector_key": "wanzhuanmi",  # 对应收集器插件的关键字
        "selectors": [
            'a[href*="/archives/"]',
            ".post-title a",
            "h2 a",
            ".entry-title a",
            "article h2 a",
        ],
        "patterns": [
            r'https?://[^\s\'"]*?\.(?:top|com|org|net|io|gg|tk|ml)[^\s\'"]*(?:/sub|/api|/link)[^\s\'"]*'
        ],
    },
    "cfmem": {
        "name": "CFMem",
        "url": "https://www.cfmem.com/",
        "enabled": True,
        "collector_key": "cfmem",  # 对应收集器插件的关键字
        "selectors": [
            ".post-title a",
            "h2 a",
            ".entry-title a",
            "article h2 a",
            ".content h2 a",
        ],
        "patterns": [
            r'https?://[^\s\'"]*?\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*?/sub[^\s\'"]*',
            r'https?://[^\s\'"]*?/subscribe[^\s\'"]*',
        ],
    },
    "clashnodecc": {
        "name": "ClashNodeCC",
        "url": "https://clashnode.cc/",
        "enabled": True,
        "collector_key": "clashnodecc",  # 对应收集器插件的关键字
        "selectors": [
            "article:first-child a",
            ".post:first-child a",
            ".entry-title:first-child a",
            "h1 a",
            "h2 a",
            ".post-title a",
            ".entry-title a",
            "article h2 a",
            ".content h2 a",
            ".latest-post a",
            'a[href*="/archives/"]',
            'a[href*="/post/"]',
            'a[href*="/node/"]',
        ],
        "patterns": [
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*(?:sub|subscribe|link|api|node)[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*(?:github\.com|gitlab\.com|raw\.githubusercontent\.com)[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*/[^\s\'"]*(?:sub|subscribe|link)[^\s\'"]*',
            r'https?://[^\s\'"]*\.txt',
        ],
    },
    "datiya": {
        "name": "Datiya",
        "url": "https://free.datiya.com/",
        "enabled": False,  # 网站已失效（无法访问）
        "collector_key": "datiya",  # 对应收集器插件的关键字
        "selectors": [
            "article a",
            ".post a",
            'a[href*="/post/"]',
            'a[href*="/2026"]',
            "h1 a",
            "h2 a",
            ".entry-title a",
        ],
        "patterns": [
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*(?:sub|subscribe|link|api|node)[^\s\'"]*',
            r"vmess://[^\s\n\r]+",
            r"vless://[^\s\n\r]+",
            r"trojan://[^\s\n\r]+",
        ],
    },
    "telegeam": {
        "name": "Telegeam",
        "url": "https://telegeam.github.io/clashv2rayshare/",
        "enabled": False,  # 订阅链接域名已失效（sfdr.zaixianyouxi.dpdns.org 返回404）
        "collector_key": "telegeam",  # 对应收集器插件的关键字
        "selectors": [
            "h1 a",
            ".post-title a",
            "article h1 a",
            "h2 a",
            'a[href*="/202"]',
            'a[href*="/2025/12"]',
        ],
        "patterns": [
            r"vmess://[^\s\n\r]+",
            r"vless://[^\s\n\r]+",
            r"trojan://[^\s\n\r]+",
            r"hysteria://[^\s\n\r]+",
            r"ss://[^\s\n\r]+",
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
        ],
    },
    "clashgithub": {
        "name": "ClashGithub",
        "url": "https://clashgithub.com/",
        "enabled": True,
        "collector_key": "clashgithub",  # 对应收集器插件的关键字
        "selectors": [
            "h3 a",
            ".post-title a",
            "article h3 a",
            "h2 a",
            "h1 a",
            'a[href*="/202"]',
            'a[href*="/2025"]',
        ],
        "patterns": [
            r"vmess://[^\s\n\r]+",
            r"vless://[^\s\n\r]+",
            r"trojan://[^\s\n\r]+",
            r"hysteria://[^\s\n\r]+",
            r"hysteria2://[^\s\n\r]+",
            r"ss://[^\s\n\r]+",
            r"ssr://[^\s\n\r]+",
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*(?:sub|subscribe|link|api|node)[^\s\'"]*\.txt[^\s\'"]*',
        ],
    },
    "oneclash": {
        "name": "OneClash",
        "url": "https://oneclash.cc/freenode",
        "enabled": True,
        "collector_key": "oneclash",  # 对应收集器插件的关键字
        "selectors": [
            ".post-title a",
            "h2 a",
            ".entry-title a",
            "article h2 a",
            'a[href*="/a/"]',
            'a[href*="/2026"]',
        ],
        "patterns": [
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*(?:sub|subscribe|link|api|node)[^\s\'"]*',
            r"vmess://[^\s\n\r]+",
            r"vless://[^\s\n\r]+",
            r"trojan://[^\s\n\r]+",
        ],
    },
    "freev2raynode": {
        "name": "FreeV2rayNode",
        "url": "https://www.freev2raynode.com/",
        "enabled": True,
        "collector_key": "freev2raynode",  # 对应收集器插件的关键字
        "selectors": [
            ".post-title a",
            "h2 a",
            ".entry-title a",
            "article h2 a",
            'a[href*="/free-node/"]',
            'a[href*="/2026"]',
        ],
        "patterns": [
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*(?:sub|subscribe|link|api|node)[^\s\'"]*',
            r"vmess://[^\s\n\r]+",
            r"vless://[^\s\n\r]+",
            r"trojan://[^\s\n\r]+",
        ],
    },
    "85la": {
        "name": "85LA",
        "url": "https://www.85la.com/internet-access/free-network-nodes",
        "enabled": True,
        "collector_key": "la",  # 对应收集器插件的关键字
        "selectors": [
            ".post-title a",
            "h2 a",
            ".entry-title a",
            "article h2 a",
            'a[href*="/202"]',
            'a[href*="/2025"]',
        ],
        "patterns": [
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            r'https?://[^\s\'"]*(?:sub|subscribe|link|api|node)[^\s\'"]*',
            r"vmess://[^\s\n\r]+",
            r"vless://[^\s\n\r]+",
            r"trojan://[^\s\n\r]+",
        ],
    },
    "xinye": {
        "name": "Xinye",
        "url": "https://www.xinye.eu.org/",
        "enabled": True,
        "collector_key": "xinye",  # 对应收集器插件的关键字
        "selectors": [
            ".post-title a",
            "h2 a",
            ".entry-title a",
            "article h2 a",
            'a[href*="/202"]',
            'a[href*="/2025"]',
            'a[href*="/2026"]',
        ],
        "patterns": [
            r'https?://raw\.githubusercontent\.com/[^\s\'"]+\.txt',
            r'https?://[^\s\'"]*\.txt[^\s\'"]*',
            r"vmess://[^\s\n\r]+",
            r"vless://[^\s\n\r]+",
            r"trojan://[^\s\n\r]+",
        ],
    },
}

# 通用选择器（当特定网站选择器失败时使用）
UNIVERSAL_SELECTORS = [
    "article:first-child a",
    ".post:first-child a",
    ".entry-title:first-child a",
    "h1 a",
    "h2:first-child a",
    ".latest-post a",
    'a[href*="/post/"]',
    'a[href*="/article/"]',
    'a[href*="/node/"]',
    'a[href*="/free/"]',
]

# 时间选择器（用于查找最新文章）
TIME_SELECTORS = ["time", ".post-date", ".entry-date", ".published", "[datetime]"]

# 订阅链接关键词
SUBSCRIPTION_KEYWORDS = [
    "订阅",
    "subscription",
    "sub",
    "link",
    "节点",
    "nodes",
    "配置",
    "config",
]

# 订阅链接模式
SUBSCRIPTION_PATTERNS = [
    r'https?://[^\s\'"\.]*\.?[^\s\'"]*(?:/sub|/subscribe|/link|/api|/node|/v2)[^\s\'"]*',
    r'["\']((?:https?://[^\s\'"]*?/sub[^\s\'"]*?))["\']',
    r'["\']((?:https?://[^\s\'"]*?/subscribe[^\s\'"]*?))["\']',
    r'["\']((?:https?://[^\s\'"]*?/link[^\s\'"]*?))["\']',
    r'["\']((?:https?://[^\s\'"]*?/api[^\s\'"]*?))["\']',
    r'["\']((?:https?://[^\s\'"]*?\.txt))["\']',  # 通用.txt文件模式
    r'https?://[^\s\'"\)]*\.txt',  # 独立的.txt文件模式
]

# 非节点订阅链接排除模式（排除明显不是V2Ray节点的链接）
EXCLUDED_SUBSCRIPTION_PATTERNS = [
    # 排除Clash相关订阅（只排除路径中包含clash的文件，不影响域名）
    r"https?://[^/]+/[^/]*(?:clash|Clash|CLASH)[^/]*\.txt",
    r".*(?:sing-?box|singbox|Sing-?Box|SINGBOX).*\.txt",
    r".*(?:yaml|yml).*\.txt",
    r".*(?:config|Config).*\.txt",
    # 排除明显的内容聚合网站
    r".*(?:parsing|Parsing|PAESING).*\.txt",
    r".*(?:convert|Convert|CONVERT).*\.txt",
    r".*(?:transform|Transform|TRANSFORM).*\.txt",
    # 排除特定的非节点网站
    r".*(?:subconverter|subx|sub\.xeton).*",
    r".*(?:api\.v1\.mk|v1\.mk).*",
    r".*(?:raw\.git).*",
    # 排除包含特定关键词的链接
    r".*(?:免费机场|机场推荐|vpn推荐|科学上网).*",
    r".*(?:广告|推广|aff).*",
    r".*(?:破解|crack|hack).*",
    # 排除明显的测试链接
    r".*(?:test|Test|TEST).*\.txt",
    r".*(?:demo|Demo|DEMO).*\.txt",
    r".*(?:example|Example|EXAMPLE).*\.txt",
    # 排除过长的路径（通常不是节点订阅，超过6层）
    r"https?://[^/]+/[^/]+/[^/]+/[^/]+/[^/]+/[^/]+/",
]

# 节点协议模式
NODE_PATTERNS = [
    r"(vmess://[^\s\n\r]+)",
    r"(vless://[^\s\n\r]+)",
    r"(trojan://[^\s\n\r]+)",
    r"(hysteria2://[^\s\n\r]+)",
    r"(hysteria://[^\s\n\r]+)",
    r"(ss://[^\s\n\r]+)",
    r"(ssr://[^\s\n\r]+)",
]

# 代码块选择器
CODE_BLOCK_SELECTORS = [
    r"<(?:code|pre)[^>]*>(.*?)</(?:code|pre)>",
    r'<div[^>]*class="[^"]*(?:node|config|subscription)[^"]*"[^>]*>(.*?)</div>',
    r"<textarea[^>]*>(.*?)</textarea>",
    r'<input[^>]*value="([^"]*(?:vmess|vless|trojan|hysteria|ss://)[^"]*)"',
]

# Base64模式
BASE64_PATTERNS = [
    r"([A-Za-z0-9+/]{50,}={0,2})",
]

# 需要使用浏览器访问且禁用代理的网站列表
# 这些网站通过代理无法正常访问，需要使用浏览器直连访问
# 当前配置：
# - 浏览器直连：freeclashnode, mibei77, clashnodev2ray, wanzhuanmi, cfmem, telegeam, clashnodecc, clashgithub, oneclash, eighty_five_la
# - 代理访问：proxyqueen, datiya, freev2raynode
BROWSER_ONLY_SITES = [
    "freeclashnode",
    "mibei77",
    "clashnodev2ray",
    "wanzhuanmi",
    "cfmem",
    "telegeam",
    "clashnodecc",  # 文章页面需要浏览器直连访问
    "clashgithub",  # 固定文章链接需要浏览器直连访问
    "oneclash",  # 代理访问无法获取完整内容
    "la",  # Cloudflare 保护，需要浏览器绕过（使用 collector_key "la"）
    "xinye",  # Blogger 平台，需要浏览器直连访问
]
