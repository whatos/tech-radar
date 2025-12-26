import requests, json, os, re, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
# 扩充关键词，只要沾边就采集
KEYWORDS = [
    '百度', '阿里', '字节', '腾讯', '小红书', '京东', '美团', '小米', '华为', '快手', '滴滴', '拼多多',
    'OpenAI', 'Google', '特斯拉', '英伟达', 'Apple', '苹果', 'AI', '大模型', '机器人', '自动驾驶',
    '裁员', '架构调整', '年终奖', '薪酬', '职级', '高管变动', '融资', '上市', '财报', '发布会',
    '低空经济', '半导体', '出海', '周报', '马斯克'
]

def fetch_raw():
    items = []
    # 覆盖主流科技+财经+滚动新闻
    sources = [
        "https://rsshub.app/36kr/newsflashes", 
        "https://rsshub.app/ithome/it",
        "https://rsshub.app/cls/depth",
        "https://rsshub.app/huxiu/article",
        "https://rsshub.app/techweb/it",
        "https://rsshub.app/wallstreetcn/news/global",
        "https://rsshub.app/geekpark/breaking",
        "https://rsshub.app/pintu/news"
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
                desc = (item.find('description').text or "")[:500]
                if any(kw.lower() in (title + desc).lower() for kw in KEYWORDS):
                    if len(link) > 28:
                        items.append({"title": title, "link": link, "desc": desc})
        except: continue
    return items

def ai_analyze(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    你是一个毒舌且专业的资深科技主编。请处理以下 {len(items)} 条数据：
    1. 【高包容度】：只要涉及科技行业变动或大厂动态，请全部保留。
    2. 【任务】：提炼 company(主语), category, content(15字内干货), comment(15字内辛辣点评), score(1-5)。
    3. 【去重】：仅合并完全相同的事件，保留最全的链接。
    4. 【禁令】：link 必须 100% 保持原始字符串，严禁缩短或修改！
    返回严格 JSON 数组格式。
    数据：{json.dumps(items[:80], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_data = res.json()
        raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
        # 强力清洗：只提取 [ ] 之间的内容
        json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            today = datetime.now().strftime("%Y-%m-%d")
            for d in data: d['date'] = d.get('date', today)
            return data
        return []
    except Exception as e:
        print(f"AI解析异常: {e}")
        return []

if __name__ == "__main__":
    new_list = fetch_raw()
    processed = ai_analyze(new_list)
    
    data_file = 'data.json'
    old_data = []
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    # 增量去重逻辑
    unique_map = {item.get('link'): item for item in (processed + old_data) if item.get('link')}
    
    # 保留最近 14 天的情报
    limit_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    final = [v for v in unique_map.values() if v.get('date', '') >= limit_date]
    final.sort(key=lambda x: (x.get('date', ''), x.get('score', 0)), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=4)
