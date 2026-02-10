# Lambda Function for Pheno Chatbot

## Setup

### 1. Create S3 Bucket
- Bucket name: `pheno-chatbot-conversations` (or your choice)
- Region: Same as Lambda

### 2. Create Knowledge Base
```bash
cd ..
./create-knowledge-base.sh
```

### 3. Package Lambda
```bash
cd lambda
chmod +x package_lambda.sh
./package_lambda.sh
```

### 4. Deploy to AWS Lambda
- Upload `lambda-deployment.zip` to Lambda
- Set environment variables:
  - `OPENROUTER_API_KEY` - Your OpenRouter API key
  - `S3_BUCKET_NAME` - Your S3 bucket name
  - `FRONTEND_URL` - Your GitHub Pages URL (for CORS)

### 5. Configure IAM Role
- Attach the policy from `iam-policy.json` to Lambda execution role

## Environment Variables

- `OPENROUTER_API_KEY` - Required
- `S3_BUCKET_NAME` - Required (default: pheno-chatbot-conversations)
- `FRONTEND_URL` - Required for CORS (your GitHub Pages URL)

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
  "conversation_history": []
}
```

## Features

- ✅ CORS protection (only your GitHub Pages URL can call)
- ✅ S3 logging (all conversations saved)
- ✅ CloudWatch logs (automatic)
- ✅ Error handling
- ✅ Context loading from package
