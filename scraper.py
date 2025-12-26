import requests
import json
from datetime import datetime

# 1. 监控目标（大厂名单）
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易']

# 2. 核心监控源（增加科技、深度分析源）
SOURCES = [
    "https://rsshub.app/36kr/newsflashes",     # 36氪快讯
    "https://rsshub.app/ithome/it",            # IT之家
    "https://rsshub.app/latepost/1",           # 晚点LatePost（深度分析）
    "https://rsshub.app/jiemian/v6/news/list?id=1" # 界面新闻（大厂动态多）
]

def fetch_all():
    news_items = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 关键词库：专门筛选薪酬、职级、八卦
    PAY_KEYWORDS = ["薪酬", "工资", "年终奖", "职级", "裁员", "调薪", "base", "期权", "包", "福利", "普调", "股票"]
    ORG_KEYWORDS = ["架构", "变动", "任命", "调整", "合并", "换帅", "一把手", "VP", "高管"]

    for url in SOURCES:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            from xml.etree import ElementTree as ET
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = item.find('title').text or ""
                link = item.find('link').text or ""
                
                # 检查大厂命中
                matched_co = next((co for co in COMPANIES if co in title), None)
                if matched_co:
                    # 优先判定：薪酬职级八卦
                    if any(k in title for k in PAY_KEYWORDS):
                        cat = "薪酬职级💰"
                    elif any(k in title for k in ORG_KEYWORDS):
                        cat = "组织变化🏢"
                    else:
                        cat = "业务动态📡"
                    
                    news_items.append({
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "company": matched_co,
                        "category": cat,
                        "content": title,
                        "link": link
                    })
        except:
            continue
    return news_items

if __name__ == "__main__":
    data = fetch_all()
    # 按照分类优先级排序（薪酬八卦排在最前）
    priority = {"薪酬职级💰": 0, "组织变化🏢": 1, "业务动态📡": 2}
    data = sorted(data, key=lambda x: priority.get(x['category'], 3))
    
    # 确保文件写入
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
