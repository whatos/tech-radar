import requests
import json
import os
from datetime import datetime, timedelta

# 从 GitHub Secrets 读取 Key
API_KEY = os.getenv("GEMINI_API_KEY")
COMPANIES = ['百度', '阿里', '字节', '小红书', '京东', '拼多多', '腾讯', 'Google', 'AI', '美团', '网易']

def ask_gemini_to_refine(items):
    if not items or not API_KEY:
        return items

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    # 构造 Prompt
    prompt = f"""
    你是一个专业行业分析师。请处理以下新闻数据：
    1. 语义判重：合并表达同一事件的新闻。
    2. 分类：从 [薪酬职级💰, 组织变化🏢, 业务动态📡] 中选一。
    3. 格式：严格返回 JSON 数组，包含 fields: company, category, content, link, date。
    
    待处理数据：{json.dumps(items, ensure_ascii=False)}
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        res = requests.post(url, json=payload, timeout=30)
        # 提取 Gemini 返回的文本并清理（去掉 Markdown 标记）
        raw_text = res.json()['candidates'][0]['content']['parts'][0]['text']
        clean_json = raw_text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI 处理失败: {e}")
        return items

# --- 主逻辑 ---
if __name__ == "__main__":
    # 1. 抓取逻辑 (保持你之前的 fetch_data 即可)
    raw_items = [] # 假设这里是抓取到的原始数据
    
    # 2. 调用免费 AI 加工
    refined_items = ask_gemini_to_refine(raw_items)
    
    # 3. 保存逻辑 (同之前，去重后存入 data.json)
