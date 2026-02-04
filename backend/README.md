# Pheno Chatbot Backend

Secure backend server for the Pheno.AI chatbot that handles OpenRouter API integration.

## Setup

### 1. Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp env.example .env
# Edit .env and add your OpenRouter API key
nano .env
```

### 3. Ensure Knowledge Base Exists

```bash
# From project root
./create-knowledge-base.sh
```

## Running Locally

```bash
cd backend
source venv/bin/activate
python app.py
```

Backend will run on `http://localhost:5000`

## API Endpoints

### Health Check
```
GET /api/health
```

### Chat
```
POST /api/chat
Body: {
  "question": "What is the population dataset?",
  "conversation_history": []  // Optional
}
```

## Environment Variables

- `OPENROUTER_API_KEY` - Your OpenRouter API key (required)

## Notes

- The backend loads the knowledge base context on startup
- API key is stored securely in `.env` (never committed)
- CORS is configured to allow frontend requests
