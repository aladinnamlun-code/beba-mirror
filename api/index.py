import os
from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Lấy MongoDB URI từ Environment Variable
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "openclaw_mirror"
COLLECTION_NAME = "state"

def get_db():
    if not MONGO_URI:
        return None
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

@app.route('/save', methods=['POST'])
def save_data():
    """Lưu dữ liệu trạng thái vào MongoDB"""
    db = get_db()
    if db is None: return jsonify({"error": "MONGO_URI missing"}), 500
    
    data = request.get_json()
    item_id = data.get("id")
    content = data.get("data")
    
    if not item_id or content is None:
        return jsonify({"error": "Missing id or data"}), 400
    
    db[COLLECTION_NAME].update_one(
        {"_id": item_id},
        {"$set": {"data": content}},
        upsert=True
    )
    return jsonify({"status": "ok"})

@app.route('/load/<item_id>', methods=['GET'])
def load_data(item_id):
    """Tải dữ liệu trạng thái từ MongoDB"""
    db = get_db()
    if db is None: return jsonify({"error": "MONGO_URI missing"}), 500
    
    doc = db[COLLECTION_NAME].find_one({"_id": item_id})
    if doc:
        return jsonify({"status": "ok", "data": doc.get("data")})
    return jsonify({"status": "error", "message": "Not found"}), 404

if __name__ == "__main__":
    app.run()
