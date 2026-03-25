# Conversation Notes — Pheno-docs-expanded Publications Update

## Context
- User is working on updating publications on the pheno-docs-expanded website
- The site uses Quarto for the front-end
- Instructions received: update a Notion table with new publications, render Quarto, then preview

## Repo Structure (publications-related)
- `src/publications.py` — Python module that fetches publications from Notion API, processes them via notion2md, enriches with CrossRef/arXiv metadata, outputs markdown files
- `src/create_publications.ipynb` — Notebook that orchestrates the full pipeline (fetch from Notion → process → move to site folder)
- `pheno_knowledge_base_expanded/publications.md` — Quarto listing page for publications
- `pheno_knowledge_base_expanded/publications/` — folder containing individual publication markdown files
- `deploy.sh` — full deploy script (injects chatbot backend URL, runs quarto render, etc.)
- `create-knowledge-base.sh` — builds knowledge base context file from site content

## Publication Workflow (established from code)
1. Add new publications to the **Notion table** (in browser)
2. Run `src/create_publications.ipynb` — this syncs Notion → local markdown files in `publications/`
3. Run `quarto render` from `pheno_knowledge_base_expanded/` to build the site
4. Preview the site

## Required Notion Table Fields
**Must have values:**
- `Year` — if NaN, the row is skipped entirely
- `Title` — used in frontmatter, no null check
- `Is relevant?` — must be `True` (notebook filters on this)
- `Tags` and `Groups involved` — used to build categories list

**Should have for best results:**
- `Journal`
- `weblink` or `DOI` — needed to fetch authors, date, and abstract from CrossRef/arXiv

## Workspace Move
- Deleted old workspace copy at `/home/ec2-user/workspace/pheno-docs-expanded` (it was behind, only had rendered `docs/` changes)
- Moved `/home/ec2-user/pheno-docs-expanded` → `/home/ec2-user/workspace/pheno-docs-expanded`
- **Note:** The `rm -rf` succeeded but the `mv` may not have completed — verify the repo exists at the new location and is intact. If not, the repo may need to be re-cloned.
- No git push/commit was made during this process

## Key Files
- `src/publications.py:135` — `process_publication()` function that processes each row
- `src/publications.py:206` — `get_publication_details()` fetches metadata from CrossRef/arXiv
- `src/publications.py:338` — `move_publications_to_website()` moves output to site folder
- `src/create_publications.ipynb` — the notebook to run the full pipeline
