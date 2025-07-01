from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from interrogate import ask_question
from clue_engine import load_clue

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/ask', methods=['POST'])
def ask_endpoint():
    try:
        data = request.get_json()
        suspect = data.get('suspect', '')
        question = data.get('question', '')
        
        if not suspect or not question:
            return jsonify({'error': 'Missing suspect or question'}), 400
        
        response = ask_question(suspect, question)
        return jsonify({'response': response})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clue', methods=['GET'])
def clue_endpoint():
    try:
        day = request.args.get('day', type=int)
        suspect = request.args.get('suspect', '')
        
        if not day or not suspect:
            return jsonify({'error': 'Missing day or suspect parameter'}), 400
        
        clue = load_clue(day, suspect)
        return jsonify({'clue': clue})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("🚀 Starting Flask API server...")
    print("📡 API will be available at http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)