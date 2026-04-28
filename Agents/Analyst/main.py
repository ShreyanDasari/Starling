import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# We'll start with a stub, then add the real LLM
@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    question = data.get("question", "")
    
    print(f"🤖 Analyst received: {question}")
    
    # ── STUB REPLY (we'll replace this with a real LLM next) ──
    reply = f"Analyst agent received your question: '{question}'\n\nI'm a stub for now. Add your OpenAI/Anthropic key to get real analysis."
    # ───────────────────────────────────────────────────────────
    
    return jsonify({
        "reply": reply,
        "agent": "analyst-v1"
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "agent": "analyst"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    print(f"🤖 Analyst agent running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)