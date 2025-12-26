import requests, json, os, re, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def fetch_raw():
    items = []
    # 增加深度信源，确保 AI 有足够的上下文素材
    sources = [
        "https://rsshub.app/36kr/newsflashes", 
        "https://rsshub.app/huxiu/article",
        "https://rsshub.app/cls/depth", 
        "https://rsshub.app/wallstreetcn/news/global"
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=25)
            root = ET.fromstring(res.content)
            for item in root.findall('./channel/item'):
                title = (item.find('title').text or "").strip()
                link = (item.find('link').text or "").strip()
                desc = (item.find('description').text or "")[:600] # 给 AI 更多文字素材
                if len(title) > 8:
                    items.append({"title": title, "link": link, "desc": desc})
        except: continue
    return items

def ai_analyze(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # 深度解析 Prompt 升级
    prompt = f"""
    你现在是顶级战略分析师「悟空」。请从以下 {len(items)} 条新闻中，筛选出 10 条最具“产业穿透力”的消息进行日报复盘。
    
    要求：
    1. 【深度解析】：不要复述新闻！请解析背后的商业逻辑、行业竞争态势或未来的隐忧。语气要犀利、专业、一针见血。
    2. 【任务】：输出 JSON 数组。字段包括：company(主体), category(分类), content(原新闻缩写), comment(深度解析), score(价值分1-5)。
    3. 【解析范例】：
       - 表面新闻：美团入局大模型。
       - 悟空解析：并非为了技术秀肌肉，而是为了防御。美团的核心资产是“人”，在大模型重塑搜索入口的当下，它必须守住本地生活的流量闭环，防止百度或字节釜底抽薪。
    
    数据源：{json.dumps(items[:80], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = res.json()
        raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            today = datetime.now().strftime("%Y-%m-%d")
            for d in data: d['date'] = today
            return data
    except: return []

if __name__ == "__main__":
    new_data = ai_analyze(fetch_raw())
    data_file = 'data.json'
    old_data = []
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    unique_map = {item.get('link'): item for item in (new_data + old_data) if item.get('link')}
    # 只保留 14 天
    limit_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    final = [v for v in unique_map.values() if v.get('date', '') >= limit_date]
    final.sort(key=lambda x: (x.get('date', ''), x.get('score', 0)), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=4)
