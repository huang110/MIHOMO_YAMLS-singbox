import json
import os
import glob
import subprocess

# 目录定义
upstream_dir = "upstream_repo/meta/domain"
output_json_dir = "json"
output_srs_dir = "srs"

os.makedirs(output_json_dir, exist_ok=True)
os.makedirs(output_srs_dir, exist_ok=True)

# 自动获取你的 GitHub 仓库信息，用于拼接直链
github_repo = os.environ.get('GITHUB_REPOSITORY', '你的用户名/你的仓库名')
cdn_base_url = f"https://cdn.jsdelivr.net/gh/{github_repo}@main/srs"
github_base_url = f"https://raw.githubusercontent.com/{github_repo}/main/srs"

files = []
for ext in ('*.yaml', '*.yml', '*.srm', '*.list', '*.txt'):
    files.extend(glob.glob(f"{upstream_dir}/**/{ext}", recursive=True))

if not files:
    print(f"❌ 在 {upstream_dir} 下没有找到任何规则文件！")
    exit(0)

rule_set_configs = []
links_text_lines = [] # 🌟 用于收集纯文本链接列表

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

    singbox_rule = {
        "version": 1,
        "rules": rules
    }
    
    json_path = os.path.join(output_json_dir, f"{name}.json")
    srs_path = os.path.join(output_srs_dir, f"{name}.srs")
    
    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(singbox_rule, f, indent=2)
        
    subprocess.run(["sing-box", "rule-set", "compile", json_path, "-o", srs_path])
    
    # 收集批量 JSON 配置
    rule_set_configs.append({
        "type": "remote",
        "tag": f"{name}",
        "format": "binary",
        "url": f"{cdn_base_url}/{name}.srs",
        "download_detour": "direct"
    })
    
    # 🌟 收集纯文本链接列表（包含两种格式）
    links_text_lines.append(f"【规则名称】：{name}")
    links_text_lines.append(f"👉 CDN加速链接 (国内推荐): {cdn_base_url}/{name}.srs")
    links_text_lines.append(f"👉 GitHub原生链接: {github_base_url}/{name}.srs")
    links_text_lines.append("-" * 60)

# 保存批量 JSON 文件
batch_config = {"rule_set": rule_set_configs}
batch_config_path = os.path.join(output_srs_dir, "batch_config.json")
with open(batch_config_path, "w", encoding='utf-8') as f:
    json.dump(batch_config, f, indent=2, ensure_ascii=False)

# 🌟 保存纯文本链接列表文件 links.txt
links_txt_path = os.path.join(output_srs_dir, "links.txt")
with open(links_txt_path, "w", encoding='utf-8') as f:
    f.write("\n".join(links_text_lines))

print(f"🎉 链接列表已成功生成: {links_txt_path}")
