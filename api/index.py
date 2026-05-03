import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

# Env Vars
MONGO_URI = os.getenv("MONGO_URI") # The connection string from MongoDB Atlas
DB_NAME = "cloud_guardian"
COLLECTION_NAME = "memory_mirror"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

@app.route('/save', methods=['POST'])
def save_memory():
    """
    Saves a JSON blob to the mirror.
    Payload: {"id": "server_id", "data": {...}}
    """
    payload = request.json
    item_id = payload.get("id")
    data = payload.get("data")
    
    if not item_id or data is None:
        return jsonify({"status": "error", "message": "Missing id or data"}), 400
    
    collection.update_one(
        {"_id": item_id},
        {"$set": {"data": data}},
        upsert=True
    )
    return jsonify({"status": "ok"}), 200

@app.route('/load/<item_id>', methods=['GET'])
def load_memory(item_id):
    """
    Loads a JSON blob from the mirror.
    """
    doc = collection.find_one({"_id": item_id})
    if doc:
        return jsonify({"status": "ok", "data": doc["data"]}), 200
    return jsonify({"status": "error", "message": "Not found"}), 404

# For Vercel deployment
def handler(request):
    # This is the wrapper for Vercel Serverless Functions
    # (Optional: depending on how Flask is integrated with Vercel)
    return app(request)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 80)))
# test
