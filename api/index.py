import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "openclaw_mirror"
COLLECTION_STATE = "state"
COLLECTION_KEYS = "api_keys"

def get_db():
    if not MONGO_URI: return None
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

@app.route('/save', methods=['POST'])
def save_data():
    db = get_db()
    if db is None: return jsonify({"error": "MONGO_URI missing"}), 500
    data = request.get_json()
    db[COLLECTION_STATE].update_one({"_id": data.get("id")}, {"$set": {"data": data.get("data")}}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/load/<item_id>', methods=['GET'])
def load_data(item_id):
    db = get_db()
    if db is None: return jsonify({"error": "MONGO_URI missing"}), 500
    doc = db[COLLECTION_STATE].find_one({"_id": item_id})
    return jsonify({"status": "ok", "data": doc.get("data")}) if doc else jsonify({"error": "Not found"}), 404

@app.route('/get-best-key', methods=['GET'])
def get_best_key():
    """Tìm Key nhàn rỗi nhất cho một model cụ thể (LRU)"""
    db = get_db()
    if db is None: return jsonify({"error": "MONGO_URI missing"}), 500
    
    model = request.args.get("model", "gemini-1.5-flash")
    now = datetime.utcnow()

    # Tìm key: ACTIVE cho model đó VÀ (không cooldown hoặc đã hết cooldown)
    query = {
        "capabilities." + model: "ACTIVE",
        "$or": [
            {"cooldowns." + model: {"$exists": False}},
            {"cooldowns." + model: {"$lt": now}}
        ]
    }
    
    # Sắp xếp last_used tăng dần để lấy key lâu rồi chưa dùng
    key_doc = db[COLLECTION_KEYS].find_one(query, sort=[("last_used", 1)])
    
    if key_doc:
        # Cập nhật last_used ngay để tránh worker khác lấy trùng
        db[COLLECTION_KEYS].update_one({"_id": key_doc["_id"]}, {"$set": {"last_used": now}})
        return jsonify({"status": "ok", "key": key_doc["key_value"], "key_id": str(key_doc["_id"])})
    
    return jsonify({"status": "error", "message": "No active keys available"}), 404

@app.route('/report-limit', methods=['POST'])
def report_limit():
    """Đánh dấu key bị hết quota (Cho vào Cooldown 60s)"""
    db = get_db()
    if db is None: return jsonify({"error": "MONGO_URI missing"}), 500
    
    data = request.get_json()
    key_id = data.get("key_id")
    model = data.get("model")
    
    reset_at = datetime.utcnow() + timedelta(seconds=60)
    db[COLLECTION_KEYS].update_one(
        {"_id": key_id},
        {"$set": {f"cooldowns.{model}": reset_at}}
    )
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run()
