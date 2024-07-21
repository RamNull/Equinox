from flask import Flask, request, jsonify,session
import openai
import os
import logging
import uuid
import json
import copy

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = 'sk-proj-Joi94rOX8sO4gDRrhHAJT3BlbkFJVdnHwxEcyUMtLlEKq2BZ'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
MODEL = 'gpt-3.5-turbo-instruct'

app.secret_key = '3a307085-33c8-4b35-8b49-34308322a96d'  # Replace with your secret key

session = {}
session['history'] = []


@app.route('/chat', methods=['POST'])
def chat():

    data = request.get_json()
    user_message = data.get('message',None)
    model = data.get('model')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    session['history'].append({"role": "user", "content": user_message})
    try:
        # Connect to OpenAI and get a response
        response = openai.chat.completions.create(
            model=model,  # or another model you want to use
            messages=session['history']
        )

        # Extract the response from OpenAI
        chat_response = response.choices[0].message.content
        generated_text = chat_response.replace('\n','').replace('\\','')
        json_object = json.loads(generated_text)
        session['history'].append({"role": "assistant", "content": chat_response})
        return jsonify({'response': json_object})

    except Exception as e:
        return jsonify({'response': chat_response}), 500


@app.route('/chat_history/<session_id>',methods=['GET'])
def get_chat_history(session_id):
    if session_id in session: 
        try:
            return jsonify(  json.loads(session['history']))
        except Exception as e:
            return jsonify({
                "storage_history":session['history']
        })
    else:
        return jsonify({"error": "Invalid session ID"}), 400


def extract_file_info(file_obj):
    # Extract relevant data from the FileObject
    return {
        "id": file_obj.id,
        "object": file_obj.object,
        "filename": file_obj.filename,
        "purpose": file_obj.purpose,
        "status": file_obj.status,
        "created_at": file_obj.created_at,
        "bytes": file_obj.bytes,
    }

logging.basicConfig(level=logging.DEBUG)

## generate the file 
@app.route('/generate', methods=['POST'])
def generate_text():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        max_tokens = data.get('max_tokens', 100)

        response = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=max_tokens
        )

        return jsonify(response.choices[0].text.strip())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

## upload the file and train the llm
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        with open(file_path, 'rb') as f:
            response = openai.files.create(file=f, purpose='fine-tune')
        response_dict =  openai.fine_tuning.jobs.create(model="gpt-3.5-turbo", training_file=response.id).to_dict()
        return jsonify(response_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

## Fine tune the llm using the file uploaded 
@app.route('/fine-tune', methods=['POST'])
def fine_tune_model():
    data = request.json
    file_id = data.get('file_id', '')

    if not file_id:
        return jsonify({"error": "File ID is required"}), 400

    try:
      response =  openai.fine_tuning.jobs.create(model="gpt-3.5-turbo", training_file=file_id)
      response_dict = response.to_dict()
      return jsonify(response_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
## get the list of the files that are uploaded in the openai 
@app.route('/files', methods=['GET'])
def list_files():
    try:
        # List all files using OpenAI API
        response = openai.files.list()
        # Convert the response items to a serializable format
        files_info = [extract_file_info(file) for file in response.data]
        return jsonify({"files": files_info})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


## delelte the files that are in the openai 
@app.route('/delete/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    try:
        # Delete the file using OpenAI API
        openai.files.delete(file_id)
        return jsonify({"status": "success", "file_id": file_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


## start Session 

context_storage = {}
history_storage = {}
context_storage["GlobalSession"] = ""
history_storage["GlobalSession_History"] = ""

@app.route('/start', methods=['GET'])
def start_session():
    session_id = str(uuid.uuid4())
    
    # Initialize context for the session
    context_storage[session_id] = ""
    return jsonify({"status": "Session started", "session_id": session_id})

## end Session 
@app.route('/end/<session_id>', methods=['DELETE'])
def end_session(session_id):
    if session_id in context_storage:
        del context_storage[session_id]
        return jsonify({"status": "Session ended", "session_id": session_id})
    else:
        return jsonify({"error": "Invalid session ID"}), 400
    


## generate using session 

@app.route('/generate_using_session', methods=['POST'])
def generate_using_session():
    data = request.json
    session_id = data.get('session_id')
    user_input = data.get('prompt')
    model = data.get('model', MODEL)
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 100)
    scale =  data.get('scale', "free")

    if not session_id or session_id not in context_storage:
        session_id = "GlobalSession"

    if not user_input:
        return jsonify({"error": "Prompt is required"}), 400

    # Retrieve current history
    history = context_storage.get(session_id, [])
    user_input = user_input + " the application is " + scale
    
    # Create the context by combining history and current prompt
    context = "\n".join(history) + f"\nUser: {user_input}\nAI:"
    
    try:
        # Generate text
        response = openai.completions.create(
            model=model,
            prompt=context,
            temperature=temperature,
            max_tokens=max_tokens
        )
        pre_cleanup = response.choices[0].text.strip()
        generated_text = pre_cleanup.replace('\n','').replace('\\','')
        json_object = json.loads(generated_text)
        user_save = copy.deepcopy(user_input)
        generated_save =  copy.deepcopy(generated_text)
        # Update history
      
        update_resopnse = {
            "generated_text": json_object
        }
        context_storage[session_id] += f" User: {user_save},"
        context_storage[session_id] += f"AI: {generated_save},"

        return jsonify(update_resopnse)
    except Exception as e:
        return jsonify({
            "generated_text": generated_text
        })


## end Session 
@app.route('/get_history/<session_id>', methods=['GET'])
def get_history(session_id):
    if session_id in context_storage:
        storage_history = context_storage[session_id]
        storage_history.replace('\n','')
        storage_history = '{'+storage_history+'}'   
    try:
        return jsonify(  json.loads(storage_history))
    except Exception as e:
        return jsonify({
            "storage_history":storage_history
        })
    else:
        return jsonify({"error": "Invalid session ID"}), 400
    
## end Session 
@app.route('/finetunestatus/<finetune_id>', methods=['GET'])
def get_finetunestatus(finetune_id):
    response = openai.fine_tuning.jobs.retrieve(finetune_id)
    return jsonify(response.to_dict())

    


if __name__ == '__main__':
    app.run(debug=True)
