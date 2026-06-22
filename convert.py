{
  "log": {
    "level": "info",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "tun",
      "tag": "tun-in",
      "interface_name": "tun0",
      "inet4_address": "172.19.0.1/30",
      "auto_route": true,
      "strict_route": true,
      "stack": "system",
      "sniff": true
    }
  ],
  "outbounds": [
    {
      "type": "selector",
      "tag": "proxy",
      "outbounds": ["auto", "节点1", "节点2"]
    },
    {
      "type": "direct",
      "tag": "direct"
    },
    {
      "type": "block",
      "tag": "block"
    },
    {
      "type": "dns",
      "tag": "dns-out"
    }
  ],
  "route": {
    "rule_set": [
      {
        "type": "remote",
        "tag": "rule-apple-cdn",
        "format": "binary",
        "url": "https://cdn.jsdelivr.net/gh/你的用户名/你的仓库名@main/srs/apple.srs",
        "download_detour": "direct"
      },
      {
        "type": "remote",
        "tag": "rule-google-github",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/你的用户名/你的仓库名/main/srs/google.srs",
        "download_detour": "direct"
      }
    ],
    "rules": [
      {
        "protocol": "dns",
        "outbound": "dns-out"
      },
      {
        "rule_set": ["rule-apple-cdn"],
        "outbound": "direct"
      },
      {
        "rule_set": ["rule-google-github"],
        "outbound": "proxy"
      },
      {
        "ip_is_private": true,
        "outbound": "direct"
      }
    ],
    "final": "proxy",
    "auto_detect_interface": true
  }
}
