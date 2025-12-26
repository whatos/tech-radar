import requests, json, os, re, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DATA_FILE = 'data.json'

def fetch_raw():
    items = []
    # 调整为更接地气的 18 个情报点：快讯 + 深度评论 + 小红书/社交趋势
    sources = [
        # --- 大厂快讯与八卦 ---
        "https://rsshub.app/36kr/newsflashes", 
        "https://rsshub.app/huxiu/article", 
        "https://rsshub.app/cls/depth",
        "https://rsshub.app/wallstreetcn/news/global",
        "https://rsshub.app/jiemian/lists/2",
        
        # --- 小红书社交情报 (通过标签聚合一线反馈) ---
        "https://rsshub.app/xiaohongshu/user/notes/592679865e87e83489873d6b", # 举例：行业观察者
        "https://rsshub.app/xiaohongshu/hashtag/大厂八卦",
        "https://rsshub.app/xiaohongshu/hashtag/产品经理",
        "https://rsshub.app/xiaohongshu/hashtag/AI动态",
        
        # --- 科技与产品洞察 ---
        "https://rsshub.app/geekpark/breaking",
        "https://rsshub.app/tmtpost/it",
        "https://rsshub.app/ifanr/main",
        "https://rsshub.app/pingwest/tag/科技",
        "https://rsshub.app/latepost/main",
        "https://rsshub.app/qbitai/sub",
        
        # --- 财经与出海 ---
        "https://rsshub.app/ft/chinese/main",
        "https://rsshub.app/caixin/article"
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=25)
            if res.status_code != 200: continue
            root = ET.fromstring(res.content)
            for item in root.findall('./channel/item'):
                title = (item.find('title').text or "").strip()
                link = (item.find('link').text or "").strip()
                desc = (item.find('description').text or "")[:600]
                # 过滤明显无关和重复信息
                if len(title) > 10 and not any(kw in title for kw in ["图赏", "开箱", "招聘"]):
                    items.append({"title": title, "link": link, "desc": desc})
        except: continue
    return items

def ai_analyze(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    你是「悟空情报仓」首席分析师。面对来自新闻、快讯以及【小红书】社交媒体的 {len(items)} 条混合情报，请精选 15 条进行深度复盘。
    
    要求：
    1. 【情报敏感度】：关注新闻中的“行业剧震”，更要关注小红书等社交渠道折射出的“人心变化”和“产品微调”。
    2. 【解析逻辑】：comment 字段必须穿透表面。如果是大厂动态，解析其战略意图；如果是社交趋势，解析其背后的用户心理或市场蓝海。
    3. 【格式】：必须返回严格 JSON 数组：company, category, content, comment, score, link。
    
    数据源：{json.dumps(items[:120], ensure_ascii=False)}
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

def generate_weekly_report(all_data):
    if not GEMINI_KEY or not all_data: return None
    last_week = (datetime.utcnow() + timedelta(hours=8) - timedelta(days=7)).strftime("%Y-%m-%d")
    weekly_intel = [i for i in all_data if i.get('date', '') >= last_week and i.get('score', 0) >= 4]
    if len(weekly_intel) < 5: return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"你是首席战略官。请根据本周这些核心情报，总结 3 个本周行业最核心的【变化趋势】。语气要冷静
