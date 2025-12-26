import requests, json, os, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易', '小米', '华为', '快手', '滴滴', '苹果', '特斯拉', 'OpenAI']

def fetch_raw():
    items = []
    sources = [
        "https://rsshub.app/36kr/newsflashes",         # 36氪快讯
        "https://rsshub.app/ithome/it",                # IT之家（硬件/新机/新版软件）
        "https://rsshub.app/tech/news/industry",       # 行业动态
        "https://rsshub.app/huxiu/article",             # 虎嗅
        "https://rsshub.app/cls/depth"                 # 财联社（财报/公告）
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code != 200: continue
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = (item.find('title').text or "").strip()
                link = (item.find('link').text or "").strip()
                desc = (item.find('description').text or "")[:300]
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                # 关键词匹配，包含“发布”、“新产品”、“测试”等动作词更佳
                if any(co.lower() in (title + desc).lower() for co in COMPANIES):
                    items.append({
                        "title": title, 
                        "link": link, 
                        "desc": desc,
                        "pub_date": pub_date
                    })
        except: continue
    return items

def ai_process(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    你是一个资深行业分析师。请处理以下新闻碎片：
    1. 判重：合并表达同一核心事件的内容，保留最有价值的那个链接。
    2. 分类：[薪酬职级💰, 组织变化🏢, 业务动态📡, 财报研报📈, 发布会🚀, 小道消息🤫]
    3. 特别注意：如果是新手机、新App功能、新模型，请归类为“发布会🚀”或“业务动态📡”。
    返回严格JSON数组(字段:company, category, content, link, date)。
    数据：{json.dumps(items[:50], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=40)
        text = res.json()['candidates'][0]['content']['parts'][0]['text']
        # 清洗 AI 可能生成的 Markdown 块
        json_str = text.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        return json.loads(json_str)
    except Exception as e:
        print(f"AI处理出错: {e}")
        return []

if __name__ == "__main__":
    raw = fetch_raw()
    processed = ai_process(raw)
    
    data_file = 'data.json'
    old_data = []
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
                old_data = json.loads(content) if content else []
            except: old_data = []

    # 逻辑去重：优先保留新抓取的
    combined = processed + old_data
    unique_data = []
    seen_contents = set()
    
    for item in combined:
        # 使用内容前 15 个字作为去重标识
        content_key = item.get('content', '')[:15]
        if content_key not in seen_contents:
            unique_data.append(item)
            seen_contents.add(content_key)
    
    limit_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    final_list = [i for i in unique_data if i.get('date', '') >= limit_date]
    final_list.sort(key=lambda x: (x.get('date', ''), x.get('company', '')), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=4)
