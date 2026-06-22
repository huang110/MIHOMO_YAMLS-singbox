import json
import os
import glob
import subprocess

# 1. 目录定义
upstream_dir = "upstream_repo/meta/domain"
output_json_dir = "json"
output_srs_dir = "srs"

os.makedirs(output_json_dir, exist_ok=True)
os.makedirs(output_srs_dir, exist_ok=True)

# 2. 自动获取你的 GitHub 仓库信息，用于拼接直链
github_repo = os.environ.get('GITHUB_REPOSITORY', '你的用户名/你的仓库名')
cdn_base_url = f"https://cdn.jsdelivr.net/gh/{github_repo}@main/srs"
github_base_url = f"https://raw.githubusercontent.com/{github_repo}/main/srs"

# 3. 抓取所有支持的规则文件格式
files = []
for ext in ('*.yaml', '*.yml', '*.srm', '*.list', '*.txt'):
    files.extend(glob.glob(f"{upstream_dir}/**/{ext}", recursive=True))

if not files:
    print(f"❌ 在 {upstream_dir} 下没有找到任何规则文件！")
    exit(0)

# 4. 初始化数据容器
rule_set_configs = []
links_md_lines = [
    "# 🚀 Sing-box 规则集订阅直链\n",
    "这里是所有自动生成的 `.srs` 规则文件下载链接。**建议使用 CDN 加速链接**以获得更好的国内访问体验。每天北京时间上午 10 点自动同步上游最新规则。\n",
    "---\n"
]

# 5. 核心解析与转换循环
for filepath in files:
    filename = os.path.basename(filepath)
    name = os.path.splitext(filename)[0]
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    domain_suffix = []
    domain = []
    domain_keyword = []
    
    in_yaml_payload = False
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if line == 'payload:':
            in_yaml_payload = True
            continue
            
        item = ""
        if line.startswith('- '):
            item = line[2:].strip("'\" ")
        else:
            item = line.strip("'\" ")
            
        if not item: continue
            
        if item.startswith('+.'):
            domain_suffix.append(item[2:])
        elif item.startswith('DOMAIN-SUFFIX,'):
            domain_suffix.append(item.split(',')[1])
        elif item.startswith('DOMAIN,'):
            domain.append(item.split(',')[1])
        elif item.startswith('DOMAIN-KEYWORD,'):
            domain_keyword.append(item.split(',')[1])
        elif ',' not in item and not in_yaml_payload:
            domain_suffix.append(item)
        elif in_yaml_payload and ',' not in item:
            domain_suffix.append(item)
                
    rules = []
    if domain: rules.append({"domain": domain})
    if domain_suffix: rules.append({"domain_suffix": domain_suffix})
    if domain_keyword: rules.append({"domain_keyword": domain_keyword})
    
    if not rules:
        continue

    # 封装并保存为中间 JSON
    singbox_rule = {
        "version": 1,
        "rules": rules
    }
    json_path = os.path.join(output_json_dir, f"{name}.json")
    srs_path = os.path.join(output_srs_dir, f"{name}.srs")
    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(singbox_rule, f, indent=2)
        
    # 调用 Sing-box 核心编译
    subprocess.run(["sing-box", "rule-set", "compile", json_path, "-o", srs_path])
    
    # 收集批量导入配置
    rule_set_configs.append({
        "type": "remote",
        "tag": f"{name}",
        "format": "binary",
        "url": f"{cdn_base_url}/{name}.srs",
        "download_detour": "direct"
    })
    
    # 收集首页 Markdown 列表展示
    links_md_lines.append(f"### 📦 规则：`{name}`")
    links_md_lines.append(f"- **CDN 加速链接**: `{cdn_base_url}/{name}.srs`")
    links_md_lines.append(f"- **GitHub 原生链接**: `{github_base_url}/{name}.srs`")
    links_md_lines.append("")

# 6. 保存所有衍生文件
# 生成用于 Sing-box 客户端直接批量导入的 json 代码
batch_config = {"rule_set": rule_set_configs}
batch_config_path = os.path.join(output_srs_dir, "batch_config.json")
with open(batch_config_path, "w", encoding='utf-8') as f:
    json.dump(batch_config, f, indent=2, ensure_ascii=False)

# 生成仓库首页的 README.md (覆盖保存)
readme_path = "README.md"
with open(readme_path, "w", encoding='utf-8') as f:
    f.write("\n".join(links_md_lines))

print(f"🎉 转换完成！首页 README.md 已成功更新！")
