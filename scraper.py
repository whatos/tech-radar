import requests, json, os, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
# 监控名单：包含大厂及高频八卦对象
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易', '小米', '华为', '快手', '滴滴']

def fetch_raw():
    items = []
    # 混合信息流：官宣 + 财报 + 职场匿名爆料
    sources = [
        "https://rsshub.app/36kr/newsflashes",         # 36氪快讯 (实时)
        "https://rsshub.app/cls/depth",                # 财联社深度 (财报/研报)
        "https://rsshub.app/xiaohongshu/user/5e5b619a000000000100788d", # 模拟小红书爆料号1
        "https://rsshub.app/xiaohongshu/user/5b2723904e0a4d6f8f539955", # 模拟小红书爆料号2
        "https://rsshub.app/wechat/msgalbum/WzExMTEx", # 微信公众号专辑 (示意)
        "https://rsshub.app/itjuzi/invest",            # IT桔子 (投融资八卦)
        "https://rsshub.app/huxiu/article"             # 虎嗅 (深度/八卦)
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=25)
            if res.status_code != 200: continue
            root = ET.fromstring(res.text)
            for item in root.findall('./channel/item'):
                title = item.find('title').text or ""
                link = item.find('link').text or ""
                desc = item.find('description').text or ""
                
                # 关键词匹配：标题或正文包含大厂名
                matched = [co for co in COMPANIES if co.lower() in (title + desc).lower()]
                if matched:
                    items.append({
                        "title": title, 
                        "link": link, 
                        "raw_content": desc[:300], # 提供给AI判断
                        "source_url": url
                    })
        except: continue
    return items

def ai_process(items):
    if not GEMINI_KEY or not items: return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # 增强版 Prompt：要求 AI 识别并去重八卦
    prompt = f"""
    你是一个精通互联网大厂八卦和财报的分析师。请处理以下碎片信息：
    1. 判重：多渠道报道的同一件事（尤其是裁员、涨薪、发布会、财报）必须合并为一条。
    2. 分类：从 [薪酬职级💰, 组织变化🏢, 业务动态📡, 财报研报📈, 发布会🚀, 小道消息🤫] 中选一。
    3. 提取：识别核心公司。
    4. 过滤：剔除纯广告、无关紧要的日常促销。
    返回严格JSON格式数组(字段:company, category, content, link)。
    数据：{json.dumps(items[:40], ensure_ascii=False)}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        text = res.json()['candidates'][0]['content']['parts'][0]['text']
        return json.loads(text.replace('```json', '').replace('```', '').strip())
    except: return []

if __name__ == "__main__":
    raw = fetch_raw()
    processed = ai_process(raw)
    today = datetime.now().strftime("%Y-%m-%d")
    for item in processed: item['date'] = today
        
    data_file = 'data.json'
    old_data = []
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            try: old_data = json.load(f)
            except: old_data = []

    # 逻辑判重：根据内容文本判定
    seen_contents = {i.get('content') for i in old_data}
    new_entries = [i for i in processed if i.get('content') not in seen_contents]
    
    final_list = new_entries + old_data
    # 仅保留最近7天
    limit_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    final_list = [i for i in final_list if i.get('date', '') >= limit_date]
    final_list.sort(key=lambda x: (x.get('date', ''), x.get('company', '')), reverse=True)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=4)
