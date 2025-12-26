import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime

# 目标公司
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI']
# 采集源（36氪快讯 RSS）
RSS_URL = "https://rsshub.app/36kr/newsflashes"

def fetch_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(RSS_URL, headers=headers, timeout=20)
        root = ET.fromstring(response.text)
        news_items = []
        for item in root.findall('./channel/item'):
            title = item.find('title').text
            link = item.find('link').text
            # 匹配公司
            matched_co = next((co for co in COMPANIES if co in title), None)
            if matched_co:
                # 识别分类
                cat = "产品变化"
                if any(k in title for k in ["架构", "变动", "任命", "调整"]): cat = "组织变化"
                if any(k in title for k in ["薪酬", "工资", "年终奖", "职级"]): cat = "薪酬职级"
                
                news_items.append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "company": matched_co,
                    "category": cat,
                    "content": title,
                    "link": link
                })
        return news_items
    except:
        return []

if __name__ == "__main__":
    data = fetch_news()
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
