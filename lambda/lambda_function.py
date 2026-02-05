import json
import os
import logging
import requests
import boto3
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# AWS S3 client
s3_client = boto3.client('s3')

# Configuration from environment variables
API_KEY = os.environ.get('OPENROUTER_API_KEY')
S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'pheno-chatbot-conversations')
CONTEXT_FILE = 'knowledge-base-context.txt'
OPENROUTER_MODEL = 'anthropic/claude-3.5-sonnet'
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
FRONTEND_URL = os.environ.get('FRONTEND_URL', '*')  # Your GitHub Pages URL

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

# Load context file (included in Lambda package)
def load_context():
    """Load knowledge base context from file"""
    try:
        with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Context file {CONTEXT_FILE} not found in Lambda package")
        return ""

# Load context once (Lambda reuses container)
WEBSITE_CONTENT = load_context()
logger.info(f"Context loaded: {len(WEBSITE_CONTENT)} characters")

def get_cors_headers():
    """Get CORS headers for response"""
    return {
        'Access-Control-Allow-Origin': FRONTEND_URL,
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600'
    }

def save_conversation_to_s3(conversation_data):
    """Save conversation to S3"""
    try:
        # Create file path with date structure
        date_str = datetime.utcnow().strftime('%Y/%m/%d')
        conversation_id = str(uuid.uuid4())
        s3_key = f'conversations/{date_str}/{conversation_id}.json'
        
        # Save to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(conversation_data, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Conversation saved to S3: {s3_key}")
        return True
    except Exception as e:
        logger.error(f"Failed to save conversation to S3: {str(e)}")
        return False

def handle_health(event):
    """Handle health check request"""
    logger.info("Health check requested")
    
    response = {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps({
            'status': 'ok',
            'context_loaded': len(WEBSITE_CONTENT) > 0,
            'api_key_configured': bool(API_KEY)
        })
    }
    
    return response

def handle_chat(event):
    """Handle chat request"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        user_question = body.get('question', '')
        conversation_history = body.get('conversation_history', [])
        
        # Get request metadata
        request_id = event.get('requestContext', {}).get('requestId', 'unknown')
        source_ip = event.get('requestContext', {}).get('http', {}).get('sourceIp', 'unknown')
        timestamp = datetime.utcnow().isoformat()
        
        logger.info(f"Chat request received - Question: {user_question[:50]}...")
        
        # Validate input
        if not user_question:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'No question provided'})
            }
        
        if not API_KEY:
            logger.error("API key not configured")
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'API key not configured'})
            }
        
        if not WEBSITE_CONTENT:
            logger.error("Context not loaded")
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Context not loaded'})
            }
        
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
        logger.info("Calling OpenRouter API...")
        start_time = datetime.utcnow()
        
        response = requests.post(
            OPENROUTER_URL,
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': event.get('headers', {}).get('referer', ''),
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
        
        response_time = (datetime.utcnow() - start_time).total_seconds()
        
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', {}).get('message', f'API error: {response.status_code}')
            logger.error(f"OpenRouter API error: {error_msg}")
            
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': error_msg})
            }
        
        # Extract answer
        result = response.json()
        answer = result['choices'][0]['message']['content']
        usage = result.get('usage', {})
        tokens_used = usage.get('total_tokens', 0)
        
        logger.info(f"Answer generated: {len(answer)} characters, {tokens_used} tokens, {response_time:.2f}s")
        
        # Prepare conversation data for S3
        conversation_data = {
            'id': request_id,
            'timestamp': timestamp,
            'source_ip': source_ip,
            'question': user_question,
            'answer': answer,
            'conversation_history_length': len(conversation_history),
            'tokens_used': tokens_used,
            'response_time_seconds': round(response_time, 2),
            'status': 'success'
        }
        
        # Save conversation to S3 (async, don't block response)
        try:
            save_conversation_to_s3(conversation_data)
        except Exception as e:
            logger.error(f"Failed to save to S3 (non-blocking): {str(e)}")
        
        # Return response
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({'answer': answer})
        }
        
    except requests.exceptions.Timeout:
        logger.error("Request timeout")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Request timeout. Please try again.'})
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Network error: {str(e)}'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def lambda_handler(event, context):
    """Main Lambda handler"""
    # Handle CORS preflight (OPTIONS request)
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        logger.info("CORS preflight request")
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    # Get path and method
    path = event.get('requestContext', {}).get('http', {}).get('path', '')
    method = event.get('requestContext', {}).get('http', {}).get('method', '')
    
    logger.info(f"Request: {method} {path}")
    
    # Route requests
    if path == '/api/health' and method == 'GET':
        return handle_health(event)
    elif path == '/api/chat' and method == 'POST':
        return handle_chat(event)
    else:
        return {
            'statusCode': 404,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Not found'})
        }
