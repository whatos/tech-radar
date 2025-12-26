import requests, json, os, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易', '小米', '华为', '快手', '滴滴']

def fetch_raw():
    items = []
    sources = [
        "https://rsshub.app/36kr/newsflashes",         # 36氪快讯
        "https://rsshub.app/cls/depth",                # 财联社深度
        "https://rsshub.app/huxiu/article",             # 虎嗅
        "https://rsshub.app/jiemian/v6/news/list/40",   # 界面科技
        "https://rsshub.app/xiaohongshu/user/5e5b619a000000000100788d" # 小红书爆料
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code != 200: continue
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = item.find('title').text or ""
                link = item.find('link').text or ""
                desc = item.find('description').text or ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                if any(co.lower() in (title + desc).lower() for co in COMPANIES):
                    items.append({
                        "title": title, 
                        "link": link, 
                        "desc": desc[:200],
                        "pub_date": pub_date # 记录原始发布时间
                    })
        except: continue
    return items

def ai_process(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    你是一个资深行业分析师。请处理以下本周的新闻碎片：
    1. 判重：合并语义相同的条目。
    2. 溯时：根据提供的 pub_date 或内容，判断该事件发生的具体日期(格式YYYY-MM-DD)。
    3. 分类：[薪酬职级💰, 组织变化🏢, 业务动态📡, 财报研报📈, 发布会🚀, 小道消息🤫]
    返回严格JSON数组(字段:company, category, content, link, date)。
    数据：{json.dumps(items[:50], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        text = res.json()['candidates'][0]['content']['parts'][0]['text']
        return json.loads(text.replace('```json', '').replace('```', '').strip())
    except: return []

if __name__ == "__main__":
    raw = fetch_raw()
    processed = ai_process(raw)
        
    data_file = 'data.json'
    old_data = []
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    # 混合新旧数据并去重
    combined = processed + old_data
    unique_data = []
    seen_links = set()
    
    for item in combined:
        if item.get('link') not in seen_links:
            unique_data.append(item)
            seen_links.add(item.get('link'))
    
    # 仅保留最近 7 天
    limit_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    final_list = [i for i in unique_data if i.get('date', '') >= limit_date]
    
    # 排序：日期倒序，公司正序
    final_list.sort(key=lambda x: (x.get('date', ''), x.get('company', '')), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=4)
