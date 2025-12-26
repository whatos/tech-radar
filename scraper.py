import requests
import json
import os
from datetime import datetime, timedelta

COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易']
# 换成直接的 API 接口，更稳定
SOURCES = [
    "https://rsshub.app/36kr/newsflashes",
    "https://rsshub.app/ithome/it"
]

def fetch_new_data():
    news_items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in SOURCES:
        try:
            res = requests.get(url, headers=headers, timeout=20)
            from xml.etree import ElementTree as ET
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = item.find('title').text or ""
                link = item.find('link').text or ""
                matched_co = next((co for co in COMPANIES if co in title), None)
                if matched_co:
                    cat = "业务动态📡"
                    if any(k in title for k in ["薪酬", "工资", "裁员", "年终奖"]): cat = "薪酬职级💰"
                    if any(k in title for k in ["架构", "任命", "调整", "变动"]): cat = "组织变化🏢"
                    
                    news_items.append({
                        "id": link,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "company": matched_co,
                        "category": cat,
                        "content": title,
                        "link": link
                    })
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue
    return news_items

if __name__ == "__main__":
    # 1. 安全读取旧数据
    old_data = []
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        except:
            old_data = []

    # 2. 抓取
    new_data = fetch_new_data()
    
    # 3. 如果没抓到新东西，手动塞入一个“系统状态”，防止 data.json 为空
    if not new_data and not old_data:
        new_data.append({
            "id": "status_check",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "company": "系统",
            "category": "状态",
            "content": "悟空哨兵已上线，正在全网搜索情报中...",
            "link": "#"
        })

    # 4. 合并去重
    existing_ids = {item.get('id') for item in old_data}
    for item in new_data:
        if item['id'] not in existing_ids:
            old_data.append(item)

    # 5. 保留 7 天并保存
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    final_data = [item for item in old_data if item.get('date', '') >= seven_days_ago]
    final_data.sort(key=lambda x: x.get('date', ''), reverse=True)

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
