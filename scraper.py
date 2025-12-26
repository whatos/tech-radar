import requests
import json
import os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易']

def fetch_data():
    news_items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # 我们减少不稳定的源，增加一个更稳的源
    rss_urls = [
        "https://rsshub.app/36kr/newsflashes",
        "https://rsshub.app/ithome/it"
    ]
    
    for url in rss_urls:
        try:
            # 增加超时时间到 30 秒，防止 GitHub 报错
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code != 200: continue
            
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = item.find('title').text or ""
                link = item.find('link').text or ""
                
                matched_co = next((co for co in COMPANIES if co.lower() in title.lower()), None)
                if matched_co:
                    cat = "业务动态📡"
                    if any(k in title for k in ["薪酬", "年终奖", "裁员"]): cat = "薪酬职级💰"
                    if any(k in title for k in ["架构", "变动", "任命"]): cat = "组织变化🏢"
                    
                    news_items.append({
                        "id": link,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "company": matched_co,
                        "category": cat,
                        "content": title,
                        "link": link
                    })
        except Exception as e:
            print(f"警告: 抓取 {url} 失败，原因: {e}")
            continue # 一个源坏了，继续跑下一个
    return news_items

if __name__ == "__main__":
    data_file = 'data.json'
    all_data = []
    
    # 1. 读取旧数据（带错误保护）
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content: all_data = json.loads(content)
        except: all_data = []

    # 2. 抓取
    new_items = fetch_data()
    
    # 3. 去重合并
    existing_ids = {item.get('id') for item in all_data if isinstance(item, dict)}
    for item in new_items:
        if item['id'] not in existing_ids:
            all_data.append(item)

    # 4. 保底数据（防止页面空白）
    if not all_data:
        all_data = [{"id":"init","date":datetime.now().strftime("%Y-%m-%d"),"company":"系统","category":"状态","content":"悟空哨兵巡逻中，暂未发现大厂重磅头条。","link":"#"}]

    # 5. 只留 7 天并保存
    try:
        limit_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        final_list = [i for i in all_data if isinstance(i, dict) and i.get('date', '') >= limit_date]
        final_list.sort(key=lambda x: x.get('date', ''), reverse=True)

        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(final_list, f, ensure_ascii=False, indent=4)
        print("数据更新成功！")
    except Exception as e:
        print(f"写入文件失败: {e}")
