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

# 动态获取上游仓库的所有支持的文件（兼容 yaml, yml, srm, list, txt）
files = []
for ext in ('*.yaml', '*.yml', '*.srm', '*.list', '*.txt'):
    files.extend(glob.glob(f"{upstream_dir}/**/{ext}", recursive=True))

if not files:
    print(f"❌ 在 {upstream_dir} 下没有找到任何规则文件！请检查路径或后缀。")
    exit(0)

for filepath in files:
    filename = os.path.basename(filepath)
    # 提取无后缀的文件名，比如 apple.srm 变成 apple
    name = os.path.splitext(filename)[0]
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    domain_suffix = []
    domain = []
    domain_keyword = []
    
    in_yaml_payload = False
    for line in lines:
        line = line.strip()
        # 忽略空行和注释行
        if not line or line.startswith('#'):
            continue
            
        # 兼容 YAML 格式的开头
        if line == 'payload:':
            in_yaml_payload = True
            continue
            
        item = ""
        # 兼容 YAML 的列表写法 "- xxx"
        if line.startswith('- '):
            item = line[2:].strip("'\" ")
        else:
            # 兼容 srm/list 的纯文本写法
            item = line.strip("'\" ")
            
        if not item:
            continue
            
        # 匹配具体的域名规则
        if item.startswith('+.'):
            domain_suffix.append(item[2:])
        elif item.startswith('DOMAIN-SUFFIX,'):
            domain_suffix.append(item.split(',')[1])
        elif item.startswith('DOMAIN,'):
            domain.append(item.split(',')[1])
        elif item.startswith('DOMAIN-KEYWORD,'):
            domain_keyword.append(item.split(',')[1])
        elif ',' not in item and not in_yaml_payload:
            # 纯文本域名列表，默认当做 suffix 处理
            domain_suffix.append(item)
        elif in_yaml_payload and ',' not in item:
            domain_suffix.append(item)
                
    rules = []
    if domain: rules.append({"domain": domain})
    if domain_suffix: rules.append({"domain_suffix": domain_suffix})
    if domain_keyword: rules.append({"domain_keyword": domain_keyword})
    
    if not rules:
        print(f"⚠️ {filename} 中未解析到任何有效规则，跳过。")
        continue

    # 封装为 Sing-box 接受的 JSON 结构
    singbox_rule = {
        "version": 1,
        "rules": rules
    }
    
    json_path = os.path.join(output_json_dir, f"{name}.json")
    srs_path = os.path.join(output_srs_dir, f"{name}.srs")
    
    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(singbox_rule, f, indent=2)
        
    # 调用 sing-box 1.8.0 核心编译为 srs 格式
    subprocess.run(["sing-box", "rule-set", "compile", json_path, "-o", srs_path])
    print(f"✅ 已成功生成: {srs_path}")
