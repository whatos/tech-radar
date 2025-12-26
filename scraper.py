import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime

COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI']
# 增加一个备用源：IT之家（科技新闻非常密集）
SOURCES = [
    "https://rsshub.app/36kr/newsflashes",
    "https://rsshub.app/ithome/it"
]

def fetch_news():
    news_items = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in SOURCES:
        try:
            response = requests.get(url, headers=headers, timeout=20)
            root = ET.fromstring(response.text)
            for item in root.findall('./channel/item'):
                title = item.find('title').text or ""
                desc = item.find('description').text or ""
                link = item.find('link').text or ""
                full_text = title + desc # 同时扫描标题和正文

                matched_co = next((co for co in COMPANIES if co in full_text), None)
                if matched_co:
                    cat = "产品变化"
                    if any(k in full_text for k in ["架构", "变动", "任命", "调整", "合并"]): cat = "组织变化"
                    if any(k in full_text for k in ["薪酬", "工资", "年终奖", "职级", "裁员"]): cat = "薪酬职级"
                    
                    news_items.append({
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "company": matched_co,
                        "category": cat,
                        "content": title[:100], # 截取标题
                        "link": link
                    })
        except:
            continue
    return news_items

if __name__ == "__main__":
    data = fetch_news()
    # 如果没抓到，至少留一个“今日无事”的记录，方便调试
    if not data:
        data = [{"date": datetime.now().strftime("%Y-%m-%d"), "company": "系统", "category": "提示", "content": "暂未抓取到大厂动态，机器人持续监控中...", "link": "#"}]
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
