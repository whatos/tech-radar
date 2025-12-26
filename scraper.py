import requests, json, os, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易', '小米', '华为', '快手', '滴滴', '苹果', '特斯拉', 'OpenAI']

def fetch_raw():
    items = []
    sources = [
        "https://rsshub.app/36kr/newsflashes", 
        "https://rsshub.app/ithome/it",
        "https://rsshub.app/cls/depth",
        "https://rsshub.app/huxiu/article"
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=30)
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = item.find('title').text or ""
                link = item.find('link').text or ""
                desc = item.find('description').text or ""
                if any(co.lower() in (title + desc).lower() for co in COMPANIES):
                    items.append({"title": title, "link": link, "desc": desc[:400]})
        except: continue
    return items

def ai_analyze(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # 充分利用 AI 逻辑：分析、摘要、去重
    prompt = f"""
    你是一个资深的科技媒体编辑和行业分析师。
    请阅读以下新闻流，执行以下任务：
    1. 【深度判重】：将探讨同一事件的多个条目合并，选出最全面、最客观的描述。
    2. 【情报加工】：将冗长的标题转化为简练的“一句话情报”。
    3. 【价值分类】：[薪酬职级💰, 组织变化🏢, 业务动态📡, 财报研报📈, 发布会🚀, 小道消息🤫]
    4. 【情报分级】：根据重要程度给出一个评分(1-5分)。
    5. 【自动溯时】：若新闻中提到“今日、昨日”，请对应到 YYYY-MM-DD 格式。
    返回严格JSON数组(字段:company, category, content, link, date, score)。
    待处理：{json.dumps(items[:40], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=50)
        text = res.json()['candidates'][0]['content']['parts'][0]['text']
        # 清洗 Markdown 格式
        json_str = text.strip().split('```json')[-1].split('```')[0].strip()
        return json.loads(json_str)
    except: return []

if __name__ == "__main__":
    raw = fetch_raw()
    processed = ai_analyze(raw)
    
    data_file = 'data.json'
    old_data = []
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    # 逻辑去重
    combined = processed + old_data
    unique_data = []
    seen_keys = set()
    for i in combined:
        key = i.get('content', '')[:12] # 语义相似度初判
        if key not in seen_keys:
            unique_data.append(i)
            seen_keys.add(key)
    
    # 保持最近7天且按日期和分值排序
    limit_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    final = [i for i in unique_data if i.get('date', '') >= limit_date]
    final.sort(key=lambda x: (x.get('date', ''), x.get('score', 0)), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=4)
