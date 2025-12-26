import requests, json, os, re, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# 极大扩展关键词，只要沾边就抓取
KEYWORDS = [
    '百度', '阿里', '字节', '腾讯', '小红书', '京东', '美团', '小米', '华为', '快手', '滴滴', '拼多多',
    'OpenAI', 'Google', '特斯拉', '英伟达', 'Apple', '苹果', 'AI', '大模型', '机器人', '自动驾驶',
    '裁员', '架构调整', '年终奖', '薪酬', '职级', '高管变动', '融资', '上市', '财报', '发布会',
    '低空经济', '半导体', '出海', '周报'
]

def fetch_raw():
    items = []
    sources = [
        "https://rsshub.app/36kr/newsflashes", 
        "https://rsshub.app/ithome/it",
        "https://rsshub.app/cls/depth",
        "https://rsshub.app/huxiu/article",
        "https://rsshub.app/techweb/it",
        "https://rsshub.app/wallstreetcn/news/global", # 华尔街见闻
        "https://rsshub.app/geekpark/breaking",        # 极客公园
        "https://rsshub.app/tmtpost/it"               # 钛媒体
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)'}
    
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=25)
            if res.status_code != 200: continue
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = (item.find('title').text or "").strip()
                link = (item.find('link').text or "").strip()
                desc = (item.find('description').text or "")[:500]
                
                # 模糊匹配：只要标题或正文包含任一关键词
                if any(kw.lower() in (title + desc).lower() for kw in KEYWORDS):
                    if len(link) > 25:
                        items.append({"title": title, "link": link, "desc": desc})
        except: continue
    return items

def ai_analyze(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # 彻底放宽 AI 过滤限制
    prompt = f"""
    你是一个资深情报分析师。请处理以下 {len(items)} 条混合来源数据：
    1. 【高包容度】：只要涉及科技行业、公司动态、前沿技术，请全部保留。
    2. 【任务】：提炼company(主语), category, content(15字内), comment(辛辣点评), score(1-5)。
    3. 【去重】：仅合并完全相同的事件。
    返回严格 JSON 数组格式。
    数据：{json.dumps(items[:80], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_text = res.json()['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\[.*\]', res_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            today = datetime.now().strftime("%Y-%m-%d")
            for d in data: d['date'] = d.get('date', today)
            return data
        return []
    except: return []

if __name__ == "__main__":
    new_items = fetch_raw()
    processed = ai_analyze(new_items)
    
    data_file = 'data.json'
    # 读取旧数据以实现累积
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    except: old_data = []

    # 增量合并逻辑：link 为王
    unique_map = {item['link']: item for item in (old_data + processed) if 'link' in item}
    
    # 保留最近 14 天，确保页面有厚度
    limit_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    final = [v for v in unique_map.values() if v.get('date', '') >= limit_date]
    final.sort(key=lambda x: (x.get('date', ''), x.get('score', 0)), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=4)
