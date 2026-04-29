import os
import yfinance as yf
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()

app = Flask(__name__)

# --- 1. SETUP THE BRAIN (Gemini API) ---
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest') # High speed, low latency

# --- 2. BITCOIN DATA SENSOR ---
def fetch_btc_analysis_data():
    """Fetches real-time price, volume, and simple indicators."""
    print("📈 Fetching Bitcoin market data...")
    btc = yf.Ticker("BTC-USD")
    
    # Get last 48 hours for trend context
    hist = btc.history(period="2d", interval="1h")
    
    # Simple Technical Indicators
    hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
    latest = hist.tail(1).iloc[0]
    
    return {
        "current_price": round(latest['Close'], 2),
        "high_24h": round(hist['High'].max(), 2),
        "low_24h": round(hist['Low'].min(), 2),
        "volume": int(latest['Volume']),
        "trend_data": hist[['Close', 'Volume', 'SMA_20']].tail(5).to_dict()
    }

# --- 3. EXECUTION ENDPOINT ---
@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    user_prompt = data.get("question", "Analyze Bitcoin current status")

    # 1. Gather Market Evidence
    market_data = fetch_btc_analysis_data()

    # 2. Construct the Reasoning Prompt
    prompt = f"""
    You are the 'Starling Bitcoin Analyst'. 
    Analyze the following real-time Bitcoin data and answer the user's question.
    
    USER QUESTION: {user_prompt}
    
    MARKET SNAPSHOT:
    - Price: ${market_data['current_price']}
    - 24h Range: ${market_data['low_24h']} - ${market_data['high_24h']}
    - Recent Trend (Last 5h): {market_data['trend_data']}

    Your output MUST follow this JSON format:
    {{
        "signal": "BUY | SELL | HOLD",
        "confidence": "0-100%",
        "reasoning": "Short professional explanation",
        "reply": "A friendly summary for the chat interface"
    }}
    """

    # 3. LLM Inference
    try:
        response = model.generate_content(prompt)
        # Assuming the LLM returns valid text/JSON
        raw_reply = response.text
        
        return jsonify({
            "reply": raw_reply,
            "agent": "btc-analyst-v1",
            "data_source": "yfinance",
            "verifiable_hash": "0x..." # In Starling, you'd put a 0G hash here
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "target": "BTC-USD"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    print(f"🚀 Starling BTC Agent active on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port)