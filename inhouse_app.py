from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import json
import chromadb
from chromadb.config import Settings
import uuid
import requests

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
                results = collection.query(query_vector,n_results=5)  # Adjust `top_k` as needed
            except Exception as e:
                    return jsonify({"error": str(e)}), 500
            # Construct a response with score and metadata
            return jsonify({"results": results}), 200
        else:
            return jsonify({"error": "Query text not provided"}), 400
    else:
        return jsonify({"error": "Request must be JSON"}), 400

session = {}
session['history'] = []


@app.route('/chat', methods=['POST'])
def chat():

    data = request.get_json()
    user_message = data.get('message',None)
    model = data.get('model')
    user_vector = data.get('vector',True)
    if user_vector:
        croma_data = query_croma(user_message)
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        user_message = f"{user_message}\n\nRelevant information: {croma_data}"
    session['history'].append({"role": "user", "content": user_message})
    try:
        # Connect to OpenAI and get a response
        response = get_llm_response(session['history'],model)
        print(response)
        # Extract the response from OpenAI
        chat_response = response.get('choices')[0].get('message').get('content')
        start = chat_response.find('{')
        end = chat_response.rfind('}') 
        if start != -1 and end != -1:
            chat_response = chat_response[start:end+1]
            print(chat_response)
        generated_text = chat_response.replace('\n','').replace('\\','')
        json_object = json.loads(generated_text)
        session['history'].append({"role": "assistant", "content": chat_response})
        return jsonify({'response': json_object})

    except Exception as e:
        return jsonify({'response': chat_response}), 500
    
def query_croma(query_text):
    if query_text:
            print("start")
            query_vector = text_to_vector(query_text)
            try:
                print("start query")
                results = collection.query(query_vector,n_results=5)  # Adjust `top_k` as needed
                print(results)
                print("end query")
            except Exception as e:
                    return jsonify({"error": str(e)}), 500
            # Construct a response with score and metadata
            return results
    else:
        print("query test should not be empty")
        return None

def get_llm_response(context,model):
    llm_url = 'http://15.77.10.126:8865/chat/completions'
    prompt = {
        "model": model,
        "messages": context
    }
    
    response = requests.post(llm_url, json=prompt)
    if response.status_code == 200:
        return response.json()  # Return LLM's response
    else:
        print(f"Failed to get response from LLM. Status code: {response.status_code}")
        print(response.text)
        return None

def text_to_vector(text):
    vector = model.encode(text).tolist()
    return vector

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)