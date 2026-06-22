import json
import os
import glob
import subprocess

# ==========================================
# 🌟 首页说明书模板 (已排版为 Markdown 表格)
# ==========================================
README_TEMPLATE = """# 🚀 Sing-box 规则集订阅直链

这里是所有自动生成的 `.srs` 规则文件下载链接。**建议使用 CDN 加速链接**以获得更好的国内访问体验。每天北京时间上午 10 点自动同步上游最新规则。

---

## 📖 规则说明
对支持 `no-resolve` 参数的代理工具规则，默认会携带 `no-resolve` 参数，而文件名以 `-resolve` 结尾的规则集会去掉 `no-resolve` 参数。

| 规则名称 | 规则描述 |
| :--- | :--- |
| `abema` | abema 视频流媒体平台 |
| `adrules` | 广告屏蔽规则 + httpdns |
| `ai` | AI 规则集合 (包含 OpenAI, Gemini, Copilot, Claude 等) |
| `apns` | Apple Push Notification Service 苹果推送服务 |
| `apple-cn` | Apple 在中国大陆备案的规则列表 |
| `apple-proxy`| Apple 在中国大陆需要代理的规则列表 |
| `apple-tv` | Apple TV 流媒体平台 |
| `apple` | Apple 服务 |
| `bahamut` | 巴哈姆特动漫 |
| `bilibili` | 哔哩哔哩动漫 |
| `cdn` | 常见静态资源 CDN 及软件更新、操作系统等大文件下载规则 |
| `cn` | 中国大陆域名 |
| `cncidr` | 中国大陆 IP 地址 |
| `cncidr-resolve` | 中国大陆 IP 地址去除 no-resolve 参数 |
| `crypto` | 加密货币相关规则 (包含 Binance, OKX, Bybit 等) |
| `dazn` | DAZN 体育流媒体平台 |
| `disney` | 迪士尼 视频流媒体平台 |
| `dmca` | DMCA 敏感域名 (包含机场审计、PT、迅雷等) |
| `dmm` | DMM 在线内容提供商 |
| `douyin` | 抖音短视频平台 |
| `ecommerce` | 电子商务平台 (包含 Amazon, eBay, Shopee 等) |
| `fake-ip-filter`| fake-ip 过滤黑名单 |
| `forum` | 国外常见论坛平台 (Reddit, V2EX, Quora 等) |
| `games-cn` | 游戏平台、游戏下载在中国大陆可直连的规则列表 |
| `games` | 游戏平台、游戏下载规则列表 |
| `gfw` | 被 GFW 屏蔽的域名列表 |
| `gits` | Git仓库规则集合 (GitHub, GitLab, Gitee 等) |
| `google` | Google 谷歌服务 |
| `googlefcm` | Google Firebase Cloud Messaging 谷歌推送服务 |
| `hbo` | HBO 视频流媒体平台 |
| `httpdns` | 需要屏蔽的 HTTPDNS 列表 |
| `hulu` | Hulu 视频流媒体平台 |
| `microsoft-cn`| Microsoft 微软在中国大陆可直连的规则列表 |
| `microsoft` | Microsoft 微软服务 |
| `mytvsuper` | MyTV SUPER 在线视频点播服务平台 |
| `netflix` | Netflix 视频流媒体平台 |
| `niconico` | Niconico 视频网站 |
| `onedrive` | OneDrive 网盘 |
| `paypal` | PayPal 在线支付与转账平台 |
| `primevideo`| PrimeVideo 视频流媒体平台 |
| `private` | 私有网络地址 |
| `proxy` | 国外需要代理的域名 |
| `socialmedia-cn`| 国内社交媒体规则集合 (NGA, 微博, 豆瓣, 酷安等) |
| `socialmedia` | 国外社交媒体规则集合 (Discord, TG, Twitter, IG 等) |
| `speedtest` | Ookla SpeedTest 服务器 |
| `spotify` | Spotify 音乐流媒体平台 |
| `talkatone` | Talkatone 互联网语音通话和短信服务 |
| `tiktok` | TikTok 短视频平台 |
| `tld-proxy` | 国外需要代理的顶级域名 |
| `twitch` | Twitch 直播平台 |
| `youtube` | YouTube 视频网站 |

### ⚠️ 特殊规则：修改IP归属地规则
> **Important**: 针对部分国内软件显示的 IP 归属地进行修改，无法保证规则的可用性，甚至可能会触发账号风控，不推荐使用。

| 规则名称 | 规则描述 |
| :--- | :--- |
| `httpdns` | 需要屏蔽的 HTTPDNS 列表，需要修改国内软件 IP 归属地时建议使用 |
| `iplocation-direct`| 修改国内软件 IP 归属地的直连规则，须放置在代理规则之前 |
| `iplocation-proxy`| 修改国内软件 IP 归属地的代理规则，不建议直接使用 |

---

## 🔗 规则直链列表
"""

# ==========================================
# 下方为核心转换逻辑
# ==========================================

# 1. 目录定义
upstream_dir = "upstream_repo/meta/domain"
output_json_dir = "json"
output_srs_dir = "srs"

os.makedirs(output_json_dir, exist_ok=True)
os.makedirs(output_srs_dir, exist_ok=True)

# 2. 自动获取你的 GitHub 仓库信息
github_repo = os.environ.get('GITHUB_REPOSITORY', '你的用户名/你的仓库名')
cdn_base_url = f"https://cdn.jsdelivr.net/gh/{github_repo}@main/srs"
github_base_url = f"https://raw.githubusercontent.com/{github_repo}/main/srs"

# 3. 抓取并排序文件
files = []
for ext in ('*.yaml', '*.yml', '*.srm', '*.list', '*.txt'):
    files.extend(glob.glob(f"{upstream_dir}/**/{ext}", recursive=True))

if not files:
    print(f"❌ 在 {upstream_dir} 下没有找到任何规则文件！")
    exit(0)

files.sort(key=lambda x: os.path.basename(x).lower())

rule_set_configs = []
links_md_lines = []

# 4. 解析与编译循环
for filepath in files:
    filename = os.path.basename(filepath)
    name = os.path.splitext(filename)[0]
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    domain_suffix, domain, domain_keyword = [], [], []
    in_yaml_payload = False
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'): continue
        if line == 'payload:':
            in_yaml_payload = True
            continue
            
        item = line[2:].strip("'\" ") if line.startswith('- ') else line.strip("'\" ")
        if not item: continue
            
        if item.startswith('+.'): domain_suffix.append(item[2:])
        elif item.startswith('DOMAIN-SUFFIX,'): domain_suffix.append(item.split(',')[1])
        elif item.startswith('DOMAIN,'): domain.append(item.split(',')[1])
        elif item.startswith('DOMAIN-KEYWORD,'): domain_keyword.append(item.split(',')[1])
        elif ',' not in item and not in_yaml_payload: domain_suffix.append(item)
        elif in_yaml_payload and ',' not in item: domain_suffix.append(item)
                
    rules = []
    if domain: rules.append({"domain": domain})
    if domain_suffix: rules.append({"domain_suffix": domain_suffix})
    if domain_keyword: rules.append({"domain_keyword": domain_keyword})
    if not rules: continue

    singbox_rule = {"version": 1, "rules": rules}
    json_path = os.path.join(output_json_dir, f"{name}.json")
    srs_path = os.path.join(output_srs_dir, f"{name}.srs")
    
    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(singbox_rule, f, indent=2)
        
    subprocess.run(["sing-box", "rule-set", "compile", json_path, "-o", srs_path])
    
    rule_set_configs.append({
        "type": "remote", "tag": f"{name}", "format": "binary",
        "url": f"{cdn_base_url}/{name}.srs", "download_detour": "direct"
    })
    
    # 将每个规则的链接追加到列表
    links_md_lines.append(f"### 📦 `{name}`")
    links_md_lines.append(f"- **CDN 加速链接**: `{cdn_base_url}/{name}.srs`")
    links_md_lines.append(f"- **GitHub 原生链接**: `{github_base_url}/{name}.srs`\n")

# 5. 保存批量配置文件
batch_config_path = os.path.join(output_srs_dir, "batch_config.json")
with open(batch_config_path, "w", encoding='utf-8') as f:
    json.dump({"rule_set": rule_set_configs}, f, indent=2, ensure_ascii=False)

# 6. 拼接模板并生成带说明书的首页 README.md
with open("README.md", "w", encoding='utf-8') as f:
    f.write(README_TEMPLATE + "\n".join(links_md_lines))

print(f"🎉 转换完成！带表格说明书的首页 README.md 已成功更新！")
