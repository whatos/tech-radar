import requests, json, os, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易', '小米', '华为', '快手', '滴滴', '苹果', '特斯拉', 'OpenAI', '大模型', '英伟达']

def fetch_raw():
    items = []
    # 调整源，确保链接质量
    sources = [
        "https://rsshub.app/36kr/newsflashes", 
        "https://rsshub.app/ithome/it",
        "https://rsshub.app/cls/depth",
        "https://rsshub.app/huxiu/article",
        "https://rsshub.app/techweb/it"
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'}
    
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code != 200: continue
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = (item.find('title').text or "").strip()
                # 关键：提取原始链接，不进行任何截断
                link = (item.find('link').text or "").strip()
                desc = (item.find('description').text or "")[:400]
                
                if any(co.lower() in (title + desc).lower() for co in COMPANIES):
                    # 只有包含具体文章标识的链接才保留，防止跳转首页
                    if len(link) > 20: 
                        items.append({"title": title, "link": link, "desc": desc})
        except: continue
    return items

def ai_analyze(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # 在 Prompt 中增加强制指令：禁止修改 link
    prompt = f"""
    你是一个资深行业分析师。请处理以下新闻：
    1. 【绝对禁令】：严禁修改或缩短 link 字段，必须 100% 保留原始 URL。
    2. 【多样性】：除非内容完全一致，否则请保留。
    3. 【分类】：[薪酬职级💰, 组织变化🏢, 业务动态📡, 财报研报📈, 发布会🚀, 小道消息🤫]
    4. 【评分】：1-5分。
    返回严格JSON数组(字段:company, category, content, link, date, score)。
    待处理：{json.dumps(items[:50], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        text = res.json()['candidates'][0]['content']['parts'][0]['text']
        json_str = text.strip().split('```json')[-1].split('```')[0].strip()
        data = json.loads(json_str)
        # 二次校验：确保 AI 没有把 link 弄丢
        return [d for d in data if d.get('link') and d.get('link').startswith('http')]
    except:
        return []

if __name__ == "__main__":
    raw = fetch_raw()
    processed = ai_analyze(raw)
    
    data_file = 'data.json'
    old_data = []
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    # 去重逻辑：以 link 为唯一 ID，防止内容更新但链接重复
    combined = processed + old_data
    unique_data = []
    seen_links = set()
    for i in combined:
        link = i.get('link')
        if link not in seen_links:
            unique_data.append(i)
            seen_links.add(link)
    
    # 保留最近 7 天
    limit_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    final = [i for i in unique_data if i.get('date', '') >= limit_date]
    final.sort(key=lambda x: (x.get('date', ''), x.get('score', 0)), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=4)
