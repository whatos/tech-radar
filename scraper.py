import requests, json, os, re, time
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DATA_FILE = 'data.json'

def fetch_from_36kr():
    """直连 36氪 API (最稳)"""
    try:
        url = "https://gateway.36kr.com/api/mis/nav/home/nav/latest"
        data = {"partner_id":"web","timestamp": int(time.time()), "param":{"pageSize":20}}
        res = requests.post(url, json=data, timeout=15).json()
        items = res['data']['itemList']
        return [{"title": i['templateData']['itemTitle'], "link": f"https://36kr.com/p/{i['itemId']}", "desc": ""} for i in items]
    except: return []

def fetch_from_cls():
    """直连财联社 API (财经/政策深度)"""
    try:
        url = "https://www.cls.cn/nodeapi/telegraphList?app=CailianpressWeb&os=web"
        res = requests.get(url, timeout=15).json()
        items = res['data']['roll_data']
        return [{"title": i['title'] or i['content'][:50], "link": "https://www.cls.cn", "desc": i['content']} for i in items]
    except: return []

def ai_analyze(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # 强制 AI 输出 15 条
    prompt = f"""
    你是首席情报官「悟空」。以下是从各大厂接口实时抓取的 {len(items)} 条原始素材。
    任务：筛选并复盘 15 条情报。
    
    要求：
    1. 【结构】：company, category, content, comment, score, link。
    2. 【广度】：必须涵盖大厂动向、AI进展、出海策略。
    3. 【深度】：comment 字段必须解析背后的战略意图，不许复述标题。
    
    素材：{json.dumps(items[:100], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        raw_text = res.json()['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            today = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d")
            for d in data: d['date'] = today
            return data
    except: return []

# 复用之前的 generate_weekly_report 函数 ...

if __name__ == "__main__":
    # 聚合多条直连通道
    raw_materials = fetch_from_36kr() + fetch_from_cls()
    
    # 如果抓取到的太少，增加备选
    if len(raw_materials) < 10:
        # 这里可以加入更多直连接口
        pass

    new_intel = ai_analyze(raw_materials)
    
    # 数据持久化逻辑 (与之前相同)
    data_payload = {"intel": [], "weekly_report": None}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                content = json.load(f)
                data_payload["intel"] = content if isinstance(content, list) else content.get("intel", [])
            except: pass

    unique_map = {item.get('content')[:10]: item for item in (new_intel + data_payload["intel"])}
    limit_date = (datetime.utcnow() + timedelta(hours=8) - timedelta(days=14)).strftime("%Y-%m-%d")
    data_payload["intel"] = sorted(unique_map.values(), key=lambda x: x.get('date', ''), reverse=True)[:100]

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_payload, f, ensure_ascii=False, indent=4)
