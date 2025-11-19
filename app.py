print("--- Vibe Poetry 程式碼開始執行 ---") # 保持這一行，等等要檢查它有沒有出現
import os
import json
import requests
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# --- 1. Gemini 系統提示詞 ---
SYSTEM_INSTRUCTION_PROMPT = """
您是一位頂尖的文案專家。請根據用戶的主題，以徐志摩、席慕蓉、張嘉佳、林婉瑜等風格，
創作出一段【現代新詩】，適合在社群媒體上發布。
格式要求：請直接輸出 JSON，包含 "poetry_content" (詩的內容，保留換行) 和 "suggested_hashtags"。
"""

# --- 2. Gemini 生成函數 ---
def generate_poetry(topic):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # 如果 Key 未設定，回傳錯誤元組 (這部分是正確的)
            return {"error": "GEMINI_API_KEY 未設定"}, 500

        client = genai.Client(api_key=api_key)
        user_prompt = f"主題: {topic}。請生成一篇新詩，並以 JSON 格式輸出。"

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION_PROMPT,
                response_mime_type="application/json"
            )
        )
        
        # *** 關鍵診斷點 ***
        try:
            # 嘗試解析回傳的文字
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            # 如果解析失敗，印出原始文字內容並回傳錯誤訊息
            print("--- 🚨 JSON 解析失敗！Gemini 回傳的原始文字如下：---")
            print(response.text)
            print("-----------------------------------------------------")
            # 回傳錯誤元組，供外層函數處理
            return {"error": f"JSON Decode Error: {e}"}, 500

    except Exception as e:
        # 處理 API Key 無效等問題
        return {"error": str(e)}, 500

# --- 3. Discord Webhook 發文函數 ---
def post_to_discord(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        return False, "DISCORD_WEBHOOK_URL 未設定"

    payload = {
        "content": message,
        "username": "VibePoetry AI"
    }

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code in [200, 204]:
            return True, "發送成功"
        else:
            return False, f"Discord API Error: {response.status_code}"
    except Exception as e:
        return False, str(e)

# --- 4. API 路由 ---
@app.route('/generate_and_post', methods=['POST'])
def handle_generate_and_post():
    data = request.get_json()
    topic = data.get('topic', '隨機靈感')
    
    # 1. 先生成
    gen_result = generate_poetry(topic)
    
    # *** 關鍵錯誤處理：如果 generate_poetry 失敗，它會回傳一個 (錯誤細節, 狀態碼) 的元組 ***
    if isinstance(gen_result, tuple):
        error_details = gen_result[0]
        status_code = gen_result[1]
        
        # 🚨 輸出到伺服器終端機，讓我們看到 API 失敗的真正原因
        print(f"--- 🚨 Gemini API 錯誤碼: {status_code} ---")
        print(f"--- 🚨 錯誤細節: {error_details} ---")
        
        # 回傳給 curl 請求，讓我們知道問題
        return jsonify({
            "status": "error", 
            "message": "API 內容生成失敗，請檢查 API Key 或網路連線", 
            "details": error_details
        }), status_code

    # --- 程式碼只在 gen_result 是字典 (成功) 時才會執行到這裡 ---
    content = gen_result.get("poetry_content", "")
    hashtags = " ".join(gen_result.get("suggested_hashtags", []))
    
    # 組合內容
    full_message = f"**【{topic}】**\n\n{content}\n\n_{hashtags}_"
    
    # 2. 再發布
    success, disc_result = post_to_discord(full_message)
    
    if success:
        return jsonify({
            "status": "success",
            "message": "已生成並發布至 Discord",
            "poetry": gen_result
        }), 200
    else:
        return jsonify({"status": "partial_success", "message": "發布失敗", "details": disc_result}), 500

# app.py 新的結尾
def main_scheduled_run(topic="每日靈感"):
    """
    專門給排程器呼叫的函數，模擬 POST 請求的邏輯。
    """
    print(f"--- 🚀 排程器觸發: 主題 {topic} ---")
    
    # 直接執行 generate_and_post 的核心邏輯
    # 這裡我們需要重寫一下 handle_generate_and_post，讓它能被直接呼叫
    
    # 為了簡化，我們直接在下面新增一個專門給排程器用的 API
    # 這裡保持原樣，讓 API 透過 HTTP 觸發
    
    # 為了避免複雜的重構，我們保持 Flask 運行，並透過 Cloud Scheduler 呼叫公開 API
    
    pass # 這裡不需要修改，維持原本的 Flask 運行就好

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))