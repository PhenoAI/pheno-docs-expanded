# Pheno Knowledge Base Expanded

This repository contains the **expanded version** of the Human Phenotype Project (HPP) documentation for researchers, featuring an interactive AI chatbot.

## 🚀 Quick Start

### Prerequisites

1. **Quarto** - [Install Quarto](https://quarto.org/docs/get-started/)
2. **Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Setup API Key (Required for Chatbot)

The chatbot requires an OpenRouter API key:

1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Get your API key from [OpenRouter](https://openrouter.ai/keys)

3. Edit `.env` and add your real API key:
   ```bash
   nano .env
   ```

🔒 **Security Note:** The `.env` file is gitignored and will never be committed.

## 🏗️ Building and Deploying

### Option 1: Full Deployment (Recommended)

```bash
./deploy.sh
```

This script will:
- Create the knowledge base context from all documentation
- Inject your API key into the chatbot widget
- Build the Quarto site
- Restore the placeholder (so the key isn't committed)
- Output to `docs/`

### Option 2: Manual Build

```bash
# 1. Update chatbot knowledge base
./create-knowledge-base.sh

# 2. Build the site
cd pheno_knowledge_base_expanded
quarto render
cd ..

# 3. Preview locally
cd docs
python3 -m http.server 8000
```

⚠️ **Note:** Manual build requires manually injecting the API key from `.env` into the chatbot widget.

## 📦 Deployment to GitHub Pages

1. Build the site: `./deploy.sh`
2. Configure GitHub Pages to serve from the `docs/` folder:
   - Go to Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` (or your default branch)
   - Folder: `/docs`
3. Push your changes (the API key is safely excluded via `.gitignore`)

## 🤖 AI Chatbot (Currently Disabled)

The chatbot feature is currently **disabled** for security reasons. All implementation files are preserved for future use.

### To Re-enable the Chatbot:

1. **Set up your API key**:
   ```bash
   cp env.example .env
   # Edit .env and add your OpenRouter API key from https://openrouter.ai/keys
   ```

2. **Enable the chatbot in the configuration**:
   - Edit `pheno_knowledge_base_expanded/_quarto.yml`
   - Find line ~102-103 with the commented chatbot include
   - Uncomment this line:
     ```yaml
     include-after-body: chatbot-widget-simple.html
     ```

3. **Deploy with the chatbot**:
   ```bash
   ./deploy.sh
   ```

### Chatbot Features (When Enabled):
- **Purple button** in bottom-right corner on all pages
- Answers questions **only from website documentation**
- No backend server required (works on GitHub Pages)
- Powered by OpenRouter API (Claude 3.5 Sonnet)
- Implementation files:
  - `chatbot-widget-simple.html` - Main widget
  - `create-knowledge-base.sh` - Extracts website content
  - `CHATBOT_DEPLOY.md` - Detailed documentation

## 📝 Repository Structure

```
pheno-docs-expanded/
├── pheno_knowledge_base_expanded/  # Quarto site source
│   ├── datasets/                   # Dataset documentation (Jupyter notebooks)
│   ├── _quarto.yml                 # Site configuration
│   └── ...                         # Other content files
├── deploy.sh                       # Main deployment script
├── create-knowledge-base.sh        # Creates chatbot knowledge base
├── convert_md_to_ipynb.py          # Converts markdown to Jupyter notebooks
├── env.example                     # API key template
├── requirements.txt                # Python dependencies
└── docs/                           # Built site (for GitHub Pages)
```

## 🔄 Updating Content

### Source Content Location

Dataset markdown files are maintained in a separate repository:
- **Source**: `/home/ec2-user/workspace/pheno-docs/markdowns-expanded/`
- **Converted to**: `pheno_knowledge_base_expanded/datasets/*.ipynb`

### Update Workflow

1. Edit markdown files in `/home/ec2-user/workspace/pheno-docs/markdowns-expanded/`
2. Run `python3 convert_md_to_ipynb.py` to convert to notebooks
3. Run `./deploy.sh` to rebuild the site
4. Commit and push changes
5. GitHub Pages will automatically serve the updated `docs/` folder

### Recent Updates

- Changed output directory from `docs-expanded/` to `docs/` for simpler deployment
- Added new "Derived Phenotypes" category with Curated Phenotypes dataset
- Fixed formatting issues (bullet points, titles, duplicate content)
- Removed "Get to Know the HPP" from navigation
- Integrated Vaginal Microbiome dataset
- Updated "Health apps" to "Wearables"
- Excluded Samples Inventory from website

## 💡 Tips

- **Preview locally** before deploying:
  ```bash
  cd pheno_knowledge_base_expanded
  quarto preview
  ```

- **Update chatbot knowledge** when you change documentation:
  ```bash
  ./create-knowledge-base.sh
  ```

- **Keep API key safe**: Never commit `.env` file!

## 📚 Documentation

For more details about the Human Phenotype Project, visit the published site.

## Contributing

- Updates should be made via a PR
- Please separate commits for source changes from rendering/builds
