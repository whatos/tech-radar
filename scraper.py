import requests
import json
import os
from datetime import datetime, timedelta

COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易']
SOURCES = [
    "https://rsshub.app/36kr/newsflashes",
    "https://rsshub.app/ithome/it",
    "https://rsshub.app/latepost/1",
    "https://rsshub.app/jiemian/v6/news/list?id=1"
]

def fetch_new_data():
    news_items = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    PAY_KEYWORDS = ["薪酬", "工资", "年终奖", "职级", "裁员", "调薪", "base", "期权", "福利", "普调"]
    ORG_KEYWORDS = ["架构", "变动", "任命", "调整", "合并", "换帅", "高管"]

    for url in SOURCES:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            from xml.etree import ElementTree as ET
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = item.find('title').text or ""
                link = item.find('link').text or ""
                matched_co = next((co for co in COMPANIES if co in title), None)
                if matched_co:
                    if any(k in title for k in PAY_KEYWORDS): cat = "薪酬职级💰"
                    elif any(k in title for k in ORG_KEYWORDS): cat = "组织变化🏢"
                    else: cat = "业务动态📡"
                    
                    news_items.append({
                        "id": link, # 用链接做唯一标识防止重复
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "company": matched_co,
                        "category": cat,
                        "content": title,
                        "link": link
                    })
        except: continue
    return news_items

if __name__ == "__main__":
    # 1. 读取现有数据
    old_data = []
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    # 2. 抓取新数据并去重合并
    new_data = fetch_new_data()
    existing_ids = {item['id'] for item in old_data}
    for item in new_data:
        if item['id'] not in existing_ids:
            old_data.append(item)

    # 3. 只保留最近 7 天
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    final_data = [item for item in old_data if item['date'] >= seven_days_ago]

    # 4. 排序（日期倒序，最新的在前）
    final_data.sort(key=lambda x: x['date'], reverse=True)

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
