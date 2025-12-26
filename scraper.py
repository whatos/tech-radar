import requests, json, os, re, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# 配置区
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DATA_FILE = 'data.json'

def fetch_raw():
    """多源情报巡航：聚合科技、财经、AI前沿"""
    items = []
    sources = [
        "https://rsshub.app/36kr/newsflashes",       # 36氪快讯
        "https://rsshub.app/huxiu/article",           # 虎嗅深度
        "https://rsshub.app/cls/depth",               # 财联社深度
        "https://rsshub.app/wallstreetcn/news/global",# 华尔街见闻
        "https://rsshub.app/ithome/it",               # IT之家
        "https://rsshub.app/geekpark/breaking",       # 极客公园
        "https://rsshub.app/tmtpost/it",              # 钛媒体
        "https://rsshub.app/qbitai/sub",              # 量子位
        "https://rsshub.app/jiemian/lists/2",         # 界面商业
        "https://rsshub.app/pingwest/tag/科技"         # 品玩
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code != 200: continue
            root = ET.fromstring(res.content)
            for item in root.findall('./channel/item'):
                title = (item.find('title').text or "").strip()
                link = (item.find('link').text or "").strip()
                desc = (item.find('description').text or "")[:500]
                if len(title) > 8:
                    items.append({"title": title, "link": link, "desc": desc})
        except: continue
    return items

def ai_analyze(items):
    """AI 战略研判：从生料中筛选并加工深度情报"""
    if not GEMINI_KEY or not items: return []
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    你现在是「悟空情报仓」首席战略分析师。请处理这 {len(items)} 条动态：
    1. 【筛选】：仅保留 15 条具有产业穿透力、影响行业格局的消息。
    2. 【深度】：comment 字段必须一针见血。解析其商业动机、核心竞争或潜在风险，严禁废话和复述标题。
    3. 【格式】：必须返回严格 JSON 数组，包含字段：company(主体), category(分类), content(原意), comment(深度解析), score(1-5), link。
    数据源：{json.dumps(items[:100], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        raw_text = res.json()['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            # 标记日期为北京时间
            today = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d")
            for d in data: d['date'] = today
            return data
        return []
    except Exception as e:
        print(f"AI 解析失败: {e}")
        return []

if __name__ == "__main__":
    # 执行抓取与分析
    raw_data = fetch_raw()
    new_intel = ai_analyze(raw_data)
    
    # 持久化逻辑：合并、去重、归档
    old_data = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    # 按 link 去重合并
    unique_map = {item.get('link'): item for item in (new_intel + old_data) if item.get('link')}
    
    # 强制保留 14 天数据
    limit_date = (datetime.utcnow() + timedelta(hours=8) - timedelta(days=14)).strftime("%Y-%m-%d")
    final = [v for v in unique_map.values() if v.get('date', '') >= limit_date]
    final.sort(key=lambda x: (x.get('date', ''), x.get('score', 0)), reverse=True)

    if final:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(final, f, ensure_ascii=False, indent=4)
