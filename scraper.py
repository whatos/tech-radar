import requests, json, os, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易']

def fetch_raw():
    items = []
    sources = [
        "https://rsshub.app/36kr/newsflashes",
        "https://rsshub.app/ithome/it"
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=30)
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = item.find('title').text or ""
                link = item.find('link').text or ""
                if any(co.lower() in title.lower() for co in COMPANIES):
                    items.append({"title": title, "link": link})
        except: continue
    return items

def ai_process(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"你是一个分析师。请对以下新闻：1.语义判重合并；2.分类为[薪酬职级💰, 组织变化🏢, 业务动态📡]；3.返回严格JSON格式(字段:company, category, content, link)。待处理：{json.dumps(items[:30], ensure_ascii=False)}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        text = res.json()['candidates'][0]['content']['parts'][0]['text']
        return json.loads(text.replace('```json', '').replace('```', '').strip())
    except: return []

if __name__ == "__main__":
    raw = fetch_raw()
    processed = ai_process(raw)
    today = datetime.now().strftime("%Y-%m-%d")
    for item in processed: item['date'] = today
        
    data_file = 'data.json'
    old_data = []
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    seen_contents = {i.get('content') for i in old_data}
    new_entries = [i for i in processed if i.get('content') not in seen_contents]
    
    final_list = new_entries + old_data
    limit_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    final_list = [i for i in final_list if i.get('date', '') >= limit_date]
    final_list.sort(key=lambda x: x.get('date', ''), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=4)
