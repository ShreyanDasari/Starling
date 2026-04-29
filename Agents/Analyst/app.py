import os
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import subprocess
import json
import time
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# 1. Load the specific .env from this agent's directory
load_dotenv()

app = Flask(__name__)

# --- AGENT IDENTITY ---
# This allows you to differentiate between BTC Analyst, ETH Analyst, etc.
AGENT_ID = os.environ.get("AGENT_ID")

# --- CONFIG ---
GENE_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GENE_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 0G Settings pulled from the local .env
ZG_RPC = os.environ.get("ZG_RPC_ENDPOINT", "https://rpc-testnet.0g.ai")
# Note: In your .env, use ZEROG_PRIVATE_KEY to match the 0G CLI standards
ZG_PRIVATE_KEY = os.environ.get("ZEROG_PRIVATE_KEY") 

# --- 1. THE 0G STORAGE HANDLER ---
def upload_to_0g(data_dict):
    filename = f"{AGENT_ID}_analysis_{int(time.time())}.json"
    
    with open(filename, "w") as f:
        json.dump(data_dict, f)
    
    # Ensure the key is clean for the CLI
    clean_key = ZG_PRIVATE_KEY.strip().replace("0x", "")
    
    # Check key length (Should be 64 chars)
    if len(clean_key) != 64:
        print(f"⚠️ Warning: Private key length is {len(clean_key)}, expected 64.")

    try:
        zgs_path = "/usr/local/bin/zgs-client"
        
        # Use the Galileo Indexer
        ZG_INDEXER = os.environ.get("ZG_INDEXER_ENDPOINT", "https://indexer-storage-testnet-turbo.0g.ai")

        cmd = [
            zgs_path, "upload",
            "--url", ZG_RPC,
            "--key", clean_key,
            "--file", filename,
            "--indexer", ZG_INDEXER
        ]
        
        print(f"🚀 [{AGENT_ID}] Uploading to 0G Galileo...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # ADD THESE TWO LINES FOR DEBUGGING
        all_output = result.stdout + result.stderr
        
        if result.returncode == 0:
            for line in all_output.split('\n'):
                # We target the specific "root =" string from your logs
                if "root =" in line or "DataRoot:" in line:
                    # Split by '=' or ':' and grab the hex string
                    hash_part = line.replace("root =", ":").split(":")[-1].strip()
                    if hash_part.startswith("0x"):
                        return hash_part, filename
            
            return "0x_upload_verified_check_terminal", filename
        else:
            print(f"❌ 0G Error: {result.stderr}")
            return None, filename
    except Exception as e:
        return f"0x_sim_hash_{AGENT_ID}", filename

# --- 2. BITCOIN DATA SENSOR ---
def fetch_btc_analysis_data():
    # You can customize this function per agent (e.g., yf.Ticker("ETH-USD"))
    btc = yf.Ticker("BTC-USD")
    hist = btc.history(period="2d", interval="1h")
    latest = hist.tail(1).iloc[0]
    
    return {
        "current_price": round(latest['Close'], 2),
        "trend": "Up" if latest['Close'] > hist['Close'].mean() else "Down",
        "volume": int(latest['Volume'])
    }

# --- 3. EXECUTION ENDPOINT ---
@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    user_prompt = data.get("question", "Analyze market")

    market_data = fetch_btc_analysis_data()

    prompt = f"""
    You are {AGENT_ID}, an expert crypto analyst.
    Analyze this data: {market_data}
    User Question: {user_prompt}
    Return ONLY JSON with keys: signal, confidence, reasoning, reply.
    """

    try:
        response = model.generate_content(prompt)
        clean_json_str = response.text.replace('```json', '').replace('```', '').strip()
        analysis_result = json.loads(clean_json_str)

        full_payload = {
            "intelligence": analysis_result,
            "evidence": market_data,
            "agent_id": AGENT_ID, # Matches the identity in .env
            "timestamp": time.time()
        }

        # The upload now uses the specific key for this agent
        zg_hash, local_file = upload_to_0g(full_payload)

        return jsonify({
            "status": "success",
            "agent": AGENT_ID,
            "verifiable_data_hash": zg_hash,
            "storage_layer": "0G-Storage",
            "reply": analysis_result['reply']
        })

    except Exception as e:
        return jsonify({"error": str(e), "agent": AGENT_ID}), 500

if __name__ == "__main__":
    # Use different ports for different agents if running on the same Mac
    # e.g., BTC = 8081, ETH = 8082
    port = int(os.environ.get("PORT", 8081))
    app.run(host="0.0.0.0", port=port)