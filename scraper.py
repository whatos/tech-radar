import requests, json, os, re, time
from datetime import datetime, timedelta

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DATA_FILE = 'data.json'

def fetch_materials():
    pool = []
    print("开始抓取公开新闻...")
    # 36氪
    try:
        r = requests.post("https://gateway.36kr.com/api/mis/nav/home/nav/latest", json={"partner_id":"web","param":{"pageSize":30}}, timeout=10).json()
        titles = [f"【36Kr】{i['templateData']['itemTitle']}" for i in r['data']['itemList']]
        pool += titles
        print(f"36氪抓取成功: {len(titles)} 条")
    except Exception as e: print(f"36氪抓取失败: {e}")

    # 财联社
    try:
        r = requests.get("https://www.cls.cn/nodeapi/telegraphList?app=CailianpressWeb", timeout=10).json()
        contents = [f"【财联社】{i['content'][:150]}" for i in r['data']['roll_data']]
        pool += contents
        print(f"财联社抓取成功: {len(contents)} 条")
    except Exception as e: print(f"财联社抓取失败: {e}")
    
    return list(set(pool))

def ai_analyze(raw_texts):
    if not GEMINI_KEY:
        print("错误: 缺少 GEMINI_API_KEY")
        return []
    if not raw_texts:
        print("警告: 原始素材池为空")
        return []
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"你是顶尖顾问。请从以下语料提炼 12 条深度情报，重点词用 **加粗**。JSON格式 [{{'company':'..','category':'..','content':'..','comment':'..','score':5,'link':'..'}}]。语料：{json.dumps(raw_texts, ensure_ascii=False)}"
    
    try:
        print("正在请求 AI 进行深度研判...")
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_json = res.json()
        
        if 'candidates' not in res_json:
            print(f"AI 请求失败，API响应: {res_json}")
            return []

        text = res_json['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            today = (datetime.utcnow() + timedelta(hours=8)).strftime("%m/%d %H:%M") # 加入分钟，确保文件内容发生变化
            for d in data: d['date'] = today
            print(f"AI 研判成功: 获得 {len(data)} 条情报")
            return data
    except Exception as e:
        print(f"AI 研判异常: {e}")
    return []

if __name__ == "__main__":
    materials = fetch_materials()
    new_data = ai_analyze(materials)
    
    storage = {"intel": []}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                content = json.load(f)
                storage["intel"] = content if isinstance(content, list) else content.get("intel", [])
        except: pass

    if new_data:
        # 强制更新：将新数据放在最前面
        storage["intel"] = (new_data + storage["intel"])[:100]
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(storage, f, ensure_ascii=False, indent=4)
        print("数据已写入 data.json")
    else:
        print("未获取到新数据，跳过写入")
