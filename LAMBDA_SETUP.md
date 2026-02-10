# Lambda Backend Setup - Summary

## What Was Created

### 1. Lambda Function (`lambda/lambda_function.py`)
- **What it does:** Converts Flask app to Lambda handler
- **Features:**
  - Handles HTTP requests (GET /api/health, POST /api/chat)
  - CORS protection (only your GitHub Pages URL can call)
  - Loads context file from Lambda package
  - Calls OpenRouter API (same as before)
  - Saves conversations to S3 (with logging)
  - Returns answers in same format

### 2. Lambda Requirements (`lambda/requirements.txt`)
- **What it does:** Lists Python packages needed
- **Packages:**
  - `requests` - For calling OpenRouter API
  - `boto3` - For saving to S3

### 3. Packaging Script (`lambda/package_lambda.sh`)
- **What it does:** Creates zip file for Lambda deployment
- **Includes:**
  - Lambda function code
  - Python dependencies
  - Knowledge base context file

### 4. IAM Policy (`lambda/iam-policy.json`)
- **What it does:** Defines permissions Lambda needs
- **Permissions:**
  - Write to S3 bucket (save conversations)
  - Write to CloudWatch logs (automatic logging)

### 5. Updated Files
- **`deploy.sh`:** Changed to use BACKEND_URL (Lambda URL) instead of API key
- **`env.example`:** Updated to show Lambda URL format

## How It Works

### Architecture Flow:
```
GitHub Pages (Frontend)
    ↓
CORS Check (Lambda)
    ↓
Lambda Function
    ↓
OpenRouter API
    ↓
S3 (Save conversation)
    ↓
Return answer to frontend
```

### Key Differences from Flask:

1. **No Flask:** Lambda uses handler function, not Flask routes
2. **CORS:** Manual headers instead of Flask-CORS
3. **Context:** Loaded from package, not filesystem
4. **S3 Logging:** Conversations saved to S3 automatically
5. **Environment:** Uses AWS environment variables, not .env file

## Next Steps

### 1. Create S3 Bucket
- Name: `pheno-chatbot-conversations` (or your choice)
- Region: Same as Lambda

### 2. Package Lambda
```bash
cd lambda
chmod +x package_lambda.sh
./package_lambda.sh
```

### 3. Deploy to AWS Lambda
- Upload `lambda-deployment.zip`
- Set handler: `lambda_function.lambda_handler`
- Set environment variables:
  - `OPENROUTER_API_KEY` - Your OpenRouter API key
  - `S3_BUCKET_NAME` - Your S3 bucket name
  - `FRONTEND_URL` - Your GitHub Pages URL (for CORS)

### 4. Configure IAM Role
- Attach policy from `iam-policy.json` to Lambda execution role
- Update bucket name in policy if different

### 5. Enable Function URL
- In Lambda console, create Function URL
- Copy the URL
- Update `.env` with: `BACKEND_URL=<lambda-url>`

### 6. Deploy Frontend
```bash
./deploy.sh
```

## Environment Variables Needed

### In Lambda (AWS Console):
- `OPENROUTER_API_KEY` - Required
- `S3_BUCKET_NAME` - Required (default: pheno-chatbot-conversations)
- `FRONTEND_URL` - Required (your GitHub Pages URL for CORS)

### In Local .env:
- `BACKEND_URL` - Lambda Function URL

## Security

✅ **API Key:** Stored in Lambda environment (never in frontend)
✅ **CORS:** Only your GitHub Pages URL can call Lambda
✅ **S3:** Conversations saved securely
✅ **Logs:** CloudWatch logs (automatic)

## Testing

### Test Lambda locally:
```bash
# Test health endpoint
curl https://your-lambda-url/api/health

# Test chat endpoint
curl -X POST https://your-lambda-url/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the population dataset?"}'
```

### Test frontend:
```bash
./deploy.sh
cd docs
python3 -m http.server 8000
# Visit http://localhost:8000
```

## Troubleshooting

### Lambda can't find context file:
- Make sure `create-knowledge-base.sh` was run first
- Context file should be in `pheno_knowledge_base_expanded/knowledge-base-context.txt`

### CORS errors:
- Check `FRONTEND_URL` environment variable matches your GitHub Pages URL exactly
- Include protocol: `https://your-username.github.io`

### S3 errors:
- Check IAM policy is attached to Lambda role
- Verify S3 bucket name matches `S3_BUCKET_NAME` environment variable
- Check bucket exists and is in same region as Lambda
