import requests, json, os, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
# 扩充监控深度：增加子品牌与行业热词
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易', '小米', '华为', '快手', '滴滴', '苹果', '特斯拉', 'OpenAI', '英伟达', '半导体', '出海', '大模型']

def fetch_raw():
    items = []
    # 增加源的多样性
    sources = [
        "https://rsshub.app/36kr/newsflashes", 
        "https://rsshub.app/ithome/it",
        "https://rsshub.app/cls/depth",
        "https://rsshub.app/huxiu/article",
        "https://rsshub.app/techweb/it",
        "https://rsshub.app/geekpark/breaking"
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=20)
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = (item.find('title').text or "").strip()
                link = (item.find('link').text or "").strip()
                desc = (item.find('description').text or "")[:400]
                # 模糊匹配扩容
                if any(co.lower() in (title + desc).lower() for co in COMPANIES):
                    items.append({"title": title, "link": link, "desc": desc})
        except: continue
    return items

def ai_analyze(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # 核心优化：让 AI 产出“锐评”和“价值度”
    prompt = f"""
    你是一个毒舌但专业的科技分析师。请处理以下 {len(items)} 条数据：
    1. 【深度合并】：将重复事件合并，选出最原始、最全的链接。
    2. 【情报脱水】：content 字段请提炼为一句干货（15字内）。
    3. 【AI锐评】：comment 字段请写一句辛辣或深刻的点评（20字内）。
    4. 【价值度】：score 字段打分 1-5。
    返回 JSON 数组 (字段: company, category, content, comment, link, date, score)。
    数据：{json.dumps(items[:60], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        text = res.json()['candidates'][0]['content']['parts'][0]['text']
        json_str = text.strip().split('```json')[-1].split('```')[0].strip()
        return json.loads(json_str)
    except: return []

if __name__ == "__main__":
    raw_data = fetch_raw()
    processed = ai_analyze(raw_data)
    
    # 持久化逻辑：确保数据不断累积，解决“刷新后内容少”
    data_file = 'data.json'
    old_data = []
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    # 以链接为唯一标识去重
    combined = processed + old_data
    unique_map = {i.get('link'): i for i in combined if i.get('link')}
    
    # 保留最近 14 天（两周）的信息，增加厚度
    limit_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    final = [v for k, v in unique_map.items() if v.get('date', '') >= limit_date]
    final.sort(key=lambda x: (x.get('date', ''), x.get('score', 0)), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=4)
