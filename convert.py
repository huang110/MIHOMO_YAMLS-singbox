import json
import os
import glob
import subprocess

# 目录定义 (已修复为精确读取 meta/domain 文件夹)
upstream_dir = "upstream_repo/meta/domain"
output_json_dir = "json"
output_srs_dir = "srs"

os.makedirs(output_json_dir, exist_ok=True)
os.makedirs(output_srs_dir, exist_ok=True)

# 动态获取上游仓库的所有 yaml 文件
yaml_files = glob.glob(f"{upstream_dir}/**/*.yaml", recursive=True)

for filepath in yaml_files:
    filename = os.path.basename(filepath)
    name = filename.replace(".yaml", "")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    domain_suffix = []
    domain = []
    domain_keyword = []
    
    in_payload = False
    for line in lines:
        line = line.strip()
        if line == 'payload:':
            in_payload = True
            continue
        if in_payload and line.startswith('- '):
            item = line[2:].strip("'\" ")
            # 兼容不同写法的域名规则
            if item.startswith('+.'):
                domain_suffix.append(item[2:])
            elif item.startswith('DOMAIN-SUFFIX,'):
                domain_suffix.append(item.split(',')[1])
            elif item.startswith('DOMAIN,'):
                domain.append(item.split(',')[1])
            elif item.startswith('DOMAIN-KEYWORD,'):
                domain_keyword.append(item.split(',')[1])
            else:
                # 默认回退为 suffix 匹配
                domain_suffix.append(item)
                
    rules = []
    if domain: rules.append({"domain": domain})
    if domain_suffix: rules.append({"domain_suffix": domain_suffix})
    if domain_keyword: rules.append({"domain_keyword": domain_keyword})
    
    # 采用 version: 1 确保良好的向下兼容性
    singbox_rule = {
        "version": 1,
        "rules": rules
    }
    
    json_path = os.path.join(output_json_dir, f"{name}.json")
    srs_path = os.path.join(output_srs_dir, f"{name}.srs")
    
    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(singbox_rule, f, indent=2)
        
    # 调用 sing-box 核心编译
    subprocess.run(["sing-box", "rule-set", "compile", json_path, "-o", srs_path])
    print(f"✅ 已成功生成: {srs_path}")
