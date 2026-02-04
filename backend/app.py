from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# CORS configuration - allow frontend to call backend
# In production, replace "*" with your actual frontend URL
CORS(app, origins=["http://localhost:8000", "http://127.0.0.1:8000", "*"])

# Configuration
API_KEY = os.getenv('OPENROUTER_API_KEY')
CONTEXT_FILE = '../pheno_knowledge_base_expanded/knowledge-base-context.txt'
OPENROUTER_MODEL = 'anthropic/claude-3.5-sonnet'
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'

# Load context when server starts
print("🚀 Starting Pheno Chatbot Backend...")
print("📚 Loading knowledge base context...")
try:
    with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
        WEBSITE_CONTENT = f.read()
    print(f"✅ Context loaded: {len(WEBSITE_CONTENT)} characters")
except FileNotFoundError:
    print(f"⚠️  Warning: {CONTEXT_FILE} not found. Run ./create-knowledge-base.sh first")
    WEBSITE_CONTENT = ""
except Exception as e:
    print(f"❌ Error loading context: {e}")
    WEBSITE_CONTENT = ""

# System prompt template
SYSTEM_PROMPT_TEMPLATE = """You are a helpful AI assistant for the Human Phenotype Project website.

CRITICAL RULES:
1. Answer ONLY based on the website content provided below
2. If the answer is not in the content, say: "I don't find that information in the current documentation. Please check the website directly."
3. NEVER make up or invent information
4. Be concise and accurate
5. If asked about something not related to this project, politely decline

WEBSITE CONTENT:
{content}

Answer ONLY from the content above. Do not use external knowledge."""

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'context_loaded': len(WEBSITE_CONTENT) > 0,
        'api_key_configured': bool(API_KEY)
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests from frontend"""
    try:
        # Get question from frontend
        data = request.json
        user_question = data.get('question', '')
        conversation_history = data.get('conversation_history', [])
        
        if not user_question:
            return jsonify({'error': 'No question provided'}), 400
        
        if not API_KEY:
            return jsonify({'error': 'API key not configured'}), 500
        
        if not WEBSITE_CONTENT:
            return jsonify({'error': 'Context not loaded'}), 500
        
        # Create system prompt with context
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(content=WEBSITE_CONTENT)
        
        # Prepare messages for OpenRouter
        messages = [
            {'role': 'system', 'content': system_prompt}
        ]
        
        # Add conversation history (last 6 messages)
        messages.extend(conversation_history[-6:])
        
        # Add current question
        messages.append({'role': 'user', 'content': user_question})
        
        # Call OpenRouter API
        response = requests.post(
            OPENROUTER_URL,
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': request.headers.get('Referer', ''),
                'X-Title': 'Pheno.AI Chatbot'
            },
            json={
                'model': OPENROUTER_MODEL,
                'messages': messages,
                'temperature': 0.3,
                'max_tokens': 1000
            },
            timeout=30
        )
        
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', {}).get('message', f'API error: {response.status_code}')
            return jsonify({'error': error_msg}), 500
        
        # Extract answer
        result = response.json()
        answer = result['choices'][0]['message']['content']
        
        return jsonify({'answer': answer})
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout. Please try again.'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 Pheno Chatbot Backend - Local Development")
    print("=" * 60)
    print(f"📍 Backend URL: http://localhost:5000")
    print(f"🔑 API Key configured: {'Yes' if API_KEY else 'No (set OPENROUTER_API_KEY in .env)'}")
    print(f"📚 Context loaded: {'Yes' if WEBSITE_CONTENT else 'No'}")
    print("=" * 60)
    print("\n💡 Frontend should run on http://localhost:8000")
    print("💡 Test backend: curl http://localhost:5000/api/health\n")
    
    app.run(debug=True, port=5000, host='127.0.0.1')
