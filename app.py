from flask import Flask, render_template, request, jsonify, send_from_directory
import sys, os, json
sys.path.append(".")

app = Flask(__name__)

# ── Image serving ──────────────────────────────────────────────────────────────
@app.route("/static/images/<path:filename>")
def serve_image(filename):
    img_dir = os.path.join(os.path.dirname(__file__), "static", "images")
    return send_from_directory(img_dir, filename)

# ── Pages ──────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── Ticker search ──────────────────────────────────────────────────────────────
@app.route("/search")
def search():
    try:
        from core.ticker_search import search_ticker
        q = request.args.get("q", "").strip()
        if not q or len(q) < 2:
            return jsonify([])
        return jsonify(search_ticker(q))
    except Exception as e:
        return jsonify([])

# ── Run full pipeline ──────────────────────────────────────────────────────────
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        from orchestrator import run_athena_pipeline, save_case
        data = request.get_json()
        ticker = (data.get("ticker") or "").strip().upper()
        if not ticker:
            return jsonify({"error": "No ticker provided"}), 400
        case = run_athena_pipeline(ticker)
        save_case(case)
        return jsonify(case.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Human decision ─────────────────────────────────────────────────────────────
@app.route("/decide", methods=["POST"])
def decide():
    data = request.get_json()
    return jsonify({
        "status": "recorded",
        "case_id": data.get("case_id"),
        "decision": data.get("decision"),
        "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z"
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)