import requests
import json
import os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易']

def fetch_data():
    news_items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # 增加更多源：新浪科技、36Kr、IT之家
    rss_urls = [
        "https://rsshub.app/36kr/newsflashes",
        "https://rsshub.app/ithome/it",
        "https://rsshub.app/sina/tech/weibo"
    ]
    
    for url in rss_urls:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = item.find('title').text or ""
                link = item.find('link').text or ""
                
                # 检查大厂关键词
                matched_co = next((co for co in COMPANIES if co.lower() in title.lower()), None)
                if matched_co:
                    cat = "业务动态📡"
                    if any(k in title for k in ["薪酬", "年终奖", "裁员", "福利"]): cat = "薪酬职级💰"
                    if any(k in title for k in ["架构", "变动", "任命", "调整"]): cat = "组织变化🏢"
                    
                    news_items.append({
                        "id": link,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "company": matched_co,
                        "category": cat,
                        "content": title,
                        "link": link
                    })
        except: continue
    return news_items

if __name__ == "__main__":
    # 1. 读取旧数据
    data_file = 'data.json'
    all_data = []
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        except: all_data = []

    # 2. 抓取新数据
    new_items = fetch_data()
    
    # 3. 合并并去重
    existing_ids = {item.get('id') for item in all_data}
    for item in new_items:
        if item['id'] not in existing_ids:
            all_data.append(item)

    # 4. 保底：如果真的全网都没大厂新闻（概率极低），留一个系统提示
    if not all_data:
        all_data.append({"id":"init","date":datetime.now().strftime("%Y-%m-%d"),"company":"系统","category":"状态","content":"哨兵已就位，正持续扫描全网情报...","link":"#"})

    # 5. 只留最近 7 天，排序并写入
    limit_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    final_list = [i for i in all_data if i.get('date', '') >= limit_date]
    final_list.sort(key=lambda x: (x.get('date', ''), x.get('id', '')), reverse=True)

    with open(data_file, 'w', encoding
