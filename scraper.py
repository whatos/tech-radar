import requests, json, os, re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易', '小米', '华为', '快手', '滴滴', '苹果', '特斯拉', 'OpenAI', '英伟达']

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    }

def fetch_non_rss_sina():
    """直接抓取新浪科技滚动新闻网页版 (非RSS)"""
    items = []
    url = "https://tech.sina.com.cn/roll/rollnews.shtml"
    try:
        res = requests.get(url, headers=get_headers(), timeout=20)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        # 解析新浪滚动新闻的列表结构
        links = soup.select('.list_005 li a')
        for a in links:
            title = a.text.strip()
            link = a.get('href', '')
            if any(co.lower() in title.lower() for co in COMPANIES):
                items.append({"title": title, "link": link, "desc": "来自新浪科技网页抓取"})
    except Exception as e:
        print(f"网页抓取失败: {e}")
    return items

def fetch_rss_sources():
    """原有的 RSS 抓取逻辑作为稳定支撑"""
    items = []
    sources = [
        "https://rsshub.app/36kr/newsflashes", 
        "https://rsshub.app/ithome/it",
        "https://rsshub.app/cls/depth"
    ]
    for url in sources:
        try:
            res = requests.get(url, headers=get_headers(), timeout=20)
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = (item.find('title').text or "").strip()
                link = (item.find('link').text or "").strip()
                if any(co.lower() in title.lower() for co in COMPANIES):
                    items.append({"title": title, "link": link, "desc": ""})
        except: continue
    return items

def ai_analyze(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""
    你是一个资深情报分析师。请处理以下 {len(items)} 条混合来源数据：
    1. 【合并】：语义相同的条目必须合并，保留最全的 link。
    2. 【质量】：剔除纯广告。
    3. 【分类】：[薪酬职级💰, 组织变化🏢, 业务动态📡, 财报研报📈, 发布会🚀, 小道消息🤫]
    4. 【链接】：link 必须保持完整，不能修改。
    返回严格 JSON 数组(字段:company, category, content, link, date, score)。
    数据：{json.dumps(items[:80], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        text = res.json()['candidates'][0]['content']['parts'][0]['text']
        json_str = text.strip().split('```json')[-1].split('```')[0].strip()
        return json.loads(json_str)
    except: return []

if __name__ == "__main__":
    # 结合 RSS 和 直接网页解析
    all_raw = fetch_rss_sources() + fetch_non_rss_sina()
    processed = ai_analyze(all_raw)
    
    data_file = 'data.json'
    old_data = []
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    # 去重合并
    combined = processed + old_data
    unique_data = []
    seen_links = set()
    for i in combined:
        if i.get('link') not in seen_links:
            unique_data.append(i)
            seen_links.add(i.get('link'))
    
    limit_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    final = [i for i in unique_data if i.get('date', '') >= limit_date]
    final.sort(key=lambda x: (x.get('date', ''), x.get('score', 0)), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=4)
