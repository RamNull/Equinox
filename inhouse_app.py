from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import json
import chromadb
from chromadb.config import Settings
import uuid

app = Flask(__name__)

stored_ids = []
# Initialize Chroma DB client and collection
client = chromadb.Client(Settings())
collection = client.create_collection(name="example_collection")

# Initialize the Sentence Transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

@app.route('/upload', methods=['POST'])
def upload_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        file_content = file.read().decode('utf-8')
        data = json.loads(file_content)
        messages = data.get('messages', [])
        for message in messages:
            text = message.get('content', '')
            if text:
                vector = text_to_vector(text)
                try:
                    entry_id = str(uuid.uuid4())
                    collection.add(entry_id, vector, {"text": text})
                    stored_ids.append(entry_id)
                except Exception as e:
                    return jsonify({"error": str(e)}), 500
        return jsonify({"message": "Data uploaded successfully!"}), 200
    

@app.route('/retrieve', methods=['POST'])
def retrieve_data():
    if request.is_json:
        query_data = request.get_json()
        query_text = query_data.get('query', '')
        if query_text:
            query_vector = text_to_vector(query_text)
            try:
                results = collection.query(query_vector)  # Adjust `top_k` as needed
            except Exception as e:
                    return jsonify({"error": str(e)}), 500
            # Construct a response with score and metadata
            return jsonify({"results": results}), 200
        else:
            return jsonify({"error": "Query text not provided"}), 400
    else:
        return jsonify({"error": "Request must be JSON"}), 400

def text_to_vector(text):
    vector = model.encode(text).tolist()
    return vector

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)