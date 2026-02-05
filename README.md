# Pheno Knowledge Base Expanded

This repository contains the **expanded version** of the Human Phenotype Project (HPP) documentation for researchers, featuring an interactive AI chatbot with AWS Lambda backend.

## 🏗️ Architecture

**Serverless architecture with AWS Lambda backend (Development Environment)**

```
GitHub Pages (Frontend) → AWS Lambda Function URL → OpenRouter API → S3 (Logs)
```

**Components:**
- **Frontend**: GitHub Pages (static site with chatbot widget)
- **Backend**: AWS Lambda Function (Development Environment)
- **API**: OpenRouter (Claude 3.5 Sonnet)
- **Storage**: AWS S3 (conversation logs)
- **Security**: API keys in Lambda environment variables, CORS-protected

## 🚀 Quick Start

### Prerequisites

1. **Quarto** - [Install Quarto](https://quarto.org/docs/get-started/)
2. **Python dependencies**: `pip install -r requirements.txt`

### Setup

1. Copy environment file: `cp env.example .env`
2. Edit `.env` and set `BACKEND_URL` to your Lambda Function URL:
   ```
   BACKEND_URL="https://your-lambda-url.lambda-url.region.on.aws/api/chat"
   ```

🔒 **Security:** `.env` is gitignored. API keys are stored in Lambda environment variables.

## 📝 Editing Context (Chatbot Knowledge Base)

The chatbot answers questions based on the knowledge base context file.

### How to Update Context

1. **Edit source documentation files:**
   - Main files: `pheno_knowledge_base_expanded/*.md` and `*.qmd`
   - Dataset files: `pheno_knowledge_base_expanded/datasets/*.ipynb`

2. **Regenerate knowledge base:**
   ```bash
   ./create-knowledge-base.sh
   ```
   This creates: `pheno_knowledge_base_expanded/knowledge-base-context.txt`

3. **Update Lambda (if context changed):**
   ```bash
   cd lambda
   ./package_lambda.sh
   aws lambda update-function-code \
       --function-name pheno-chatbot-backend \
       --zip-file fileb://lambda-deployment.zip
   ```

### What Gets Included in Context

The `create-knowledge-base.sh` script combines:
- `about.qmd` - Project overview
- `participant_journey.md` - Participant information
- `faq.md` - Frequently asked questions
- `data_format.qmd` - Data format documentation
- `datasets_description.md` - Dataset descriptions
- `platform_tutorial.md` - Platform tutorial
- `pheno_utils.md` - Utility documentation

## 🎨 Building and Editing Frontend

### Build Frontend

```bash
./deploy.sh
```

**What this does:**
- Creates knowledge base context
- Injects `BACKEND_URL` from `.env` into chatbot widget
- Builds Quarto site to `docs/` folder
- Restores placeholder (safe to commit)

### Edit Frontend Files

**Main files to edit:**
- `pheno_knowledge_base_expanded/_quarto.yml` - Site configuration
- `pheno_knowledge_base_expanded/chatbot-widget-simple.html` - Chatbot UI
- `pheno_knowledge_base_expanded/*.md` / `*.qmd` - Content pages

**After editing:**
```bash
./deploy.sh  # Rebuilds with changes
```

### Preview Locally

```bash
cd docs
python3 -m http.server 8000
# Visit http://localhost:8000
```

## 🧪 Testing

### Test Locally

1. **Start backend (if testing locally):**
   ```bash
   cd backend
   python3 app.py
   # Backend runs on http://localhost:5000
   ```

2. **Update `.env` for local testing:**
   ```
   BACKEND_URL="http://localhost:5000/api/chat"
   ```

3. **Build and preview:**
   ```bash
   ./deploy.sh
   cd docs
   python3 -m http.server 8000
   ```

4. **Test chatbot:**
   - Visit `http://localhost:8000`
   - Click chatbot button (bottom right)
   - Ask a question
   - Check browser console (F12) for errors

### Test Lambda Backend

```bash
# Test health endpoint
curl https://your-lambda-url.lambda-url.region.on.aws/api/health

# Test chat endpoint
curl -X POST https://your-lambda-url.lambda-url.region.on.aws/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the population dataset?"}'
```

### Test on GitHub Pages

1. Build: `./deploy.sh`
2. Commit and push: `git add docs/ && git commit && git push`
3. Wait 1-2 minutes for GitHub Pages to rebuild
4. Visit your GitHub Pages URL
5. Test chatbot functionality

## 📦 Deployment

### Deploy to GitHub Pages

1. Build: `./deploy.sh`
2. Configure GitHub Pages:
   - Repository → Settings → Pages
   - Source: Deploy from branch
   - Branch: `main` (or your branch)
   - Folder: `/docs`
3. Push: `git add docs/ && git commit && git push`

### Update Lambda Backend

```bash
cd lambda
./package_lambda.sh
aws lambda update-function-code \
    --function-name pheno-chatbot-backend \
    --zip-file fileb://lambda-deployment.zip
```

## 📝 Repository Structure

```
pheno-docs-expanded/
├── pheno_knowledge_base_expanded/  # Quarto site source
│   ├── datasets/                   # Dataset documentation
│   ├── _quarto.yml                 # Site configuration
│   ├── chatbot-widget-simple.html  # Chatbot widget
│   └── knowledge-base-context.txt  # Generated context
├── lambda/                         # AWS Lambda backend
│   ├── lambda_function.py          # Lambda handler
│   ├── package_lambda.sh           # Packaging script
│   └── requirements.txt            # Lambda dependencies
├── deploy.sh                       # Deployment script
├── create-knowledge-base.sh        # Context generator
└── docs/                           # Built site (GitHub Pages)
```

## 🔧 Key Configuration Files

- **`.env`** - Backend URL (gitignored)
- **`lambda/lambda_function.py`** - Backend logic and system prompt
- **`pheno_knowledge_base_expanded/_quarto.yml`** - Site config (enable/disable chatbot)
- **`create-knowledge-base.sh`** - Controls what content goes into context

## 💡 Tips

- **Update context** when documentation changes: `./create-knowledge-base.sh`
- **Rebuild frontend** after editing: `./deploy.sh`
- **Test locally** before deploying to GitHub Pages
- **Check Lambda logs** in AWS CloudWatch for debugging

## Contributing

- Updates via PR
- Separate commits for source changes vs. builds
