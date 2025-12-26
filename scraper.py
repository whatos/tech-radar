import requests, json, os, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
# 监控库：涵盖硬科技、互联网、AI 及投融资热词
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易', '小米', '华为', '快手', '滴滴', '苹果', '特斯拉', 'OpenAI', '英伟达', '半导体', '出海', '大模型', '融资', '裁员', '财报']

def fetch_raw():
    items = []
    sources = [
        "https://rsshub.app/36kr/newsflashes", 
        "https://rsshub.app/ithome/it",
        "https://rsshub.app/cls/depth",
        "https://rsshub.app/huxiu/article",
        "https://rsshub.app/techweb/it",
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
                desc = (item.find('description').text or "")[:400]
                # 预筛选：确保是我们要的情报，且链接不是首页
                if any(co.lower() in (title + desc).lower() for co in COMPANIES):
                    if len(link) > 28: # 过滤极短链接，防止跳转首页
                        items.append({"title": title, "link": link, "desc": desc})
        except: continue
    return items

def ai_analyze(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # 强化 Prompt：压榨 AI 的分析能力
    prompt = f"""
    你是一个毒舌但专业的科技分析师。请从这 {len(items)} 条数据中提炼今日简报：
    1. 【合并】：语义相同的事件必须合并，严禁重复展示。
    2. 【脱水】：content 字段请提炼为一句干货（15字内）。
    3. 【锐评】：comment 字段写一句深刻点评（20字内）。
    4. 【评分】：score 字段 1-5 分（5分代表足以改变股价的大事）。
    5. 【禁令】：link 必须 100% 保留原始 URL。
    返回严格 JSON 数组格式(
