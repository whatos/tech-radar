import requests, json, os, re, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易', '小米', '华为', '快手', '滴滴', '苹果', '特斯拉', 'OpenAI', '英伟达', '半导体', '出海', '大模型']

def fetch_raw():
    items = []
    sources = [
        "https://rsshub.app/36kr/newsflashes", 
        "https://rsshub.app/ithome/it",
        "https://rsshub.app/cls/depth",
        "https://rsshub.app/huxiu/article",
        "https://rsshub.app/techweb/it"
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=25)
            if res.status_code != 200: continue
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = (item.find('title').text or "").strip()
                link = (item.find('link').text or "").strip()
                desc = (item.find('description').text or "")[:400]
                if any(co.lower() in (title + desc).lower() for co in COMPANIES):
                    if len(link) > 28:
                        items.append({"title": title, "link": link, "desc": desc})
        except: continue
    return items

def ai_analyze(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    你是一个资深分析师。请处理以下 {len(items)} 条数据：
    1. 【合并】：语义相同的事件必须合并。
    2. 【加工】：content提炼为15字内干货；comment写一句20字内锐评；score打分1-5。
    3. 【格式】：必须返回严格的 JSON 数组。
    数据：{json.dumps(items[:60], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_data = res.json()
        raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
        
        # 强力提取 JSON 数组，过滤 Markdown 标签
        json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            today = datetime.now().strftime("%Y-%m-%d")
            for d in data:
                if 'date' not in d: d['date'] = today
            return data
        return []
    except Exception as e:
        print(f"AI Processing Error: {e}")
        return []

if __name__ == "__main__":
    raw_list = fetch_raw()
    processed = ai_analyze(raw_list)
    
    data_file = 'data.json'
    old_data = []
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    # 增量去重
    unique_map = {item.get('link'): item for item in (processed + old_data) if item.get('link')}
    
    # 保留最近 14 天
    limit_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    final_list = [v for v in unique_map.values() if v.get('date', '') >= limit_date]
    final_list.sort(key=lambda x: (x.get('date', ''), x.get('score', 0)), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=4)
