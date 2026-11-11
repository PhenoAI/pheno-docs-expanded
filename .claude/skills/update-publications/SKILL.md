---
name: update-publications
description: Sync the HPP publications pages on the pheno-docs-expanded site with the Notion "HPP Publications" database — add new papers, re-render edited ones, and flag removed ones. Use whenever the user says a paper was added or updated on Notion, asks to add/refresh/sync publications, mentions the publications page or listing count being out of date, or names a specific HPP paper that should appear on the docs site, even if they don't say "skill" or "sync".
---

# Update publications from Notion

The site's publication pages are generated from the Notion database
`851933e545a843799ac66da227acc50a` by `src/publications.py`. Source `.md` files live in
`pheno_knowledge_base_expanded/publications/`; quarto renders them into `docs/`, which
GitHub Pages serves from `main` (live ~1 min after merge; browsers may cache up to 10 min).

## Never do these

- **Don't run `move_publications_to_website()`** (or the last cells of
  `src/create_publications.ipynb`). It `rmtree`s the whole source folder and replaces it
  with whatever was just processed, wiping manual fixes and any paper not reprocessed.
- **Don't print the Notion token.** It comes from AWS Secrets Manager
  (`get_notion_token_from_aws_secret_manager()`); filter it out of any output you show.
- **Don't `quarto render` the whole project.** Render only the changed pages and
  `publications.md`, so the diff stays reviewable.
- **Don't show the user `.md` files.** They don't want to read them. Printing a `diff` is
  fine; full file contents are not. Check files yourself and report only problems.
- Don't commit, push, open a PR, or delete files without the user's explicit OK for that step.

## Workflow

### 1. Find what changed

From the repo root (read-only — safe to run before branching):

```bash
PYTHONPATH=src python .claude/skills/update-publications/scripts/find_publication_changes.py
```

It prints counts, then one line per candidate:

| Status | Meaning |
|---|---|
| `NEW` | Relevant in Notion, no `.md` on the site |
| `NEW-SKIPPED` | No `Year` in Notion — `process_publication` silently skips these; ask the user to fill it |
| `EDITED` | Notion "Last edited time" is after the last commit touching the `.md` |
| `REMOVED` | `.md` exists but the row is un-ticked or deleted in Notion |
| `DUPLICATE-TITLE` | Two relevant rows share a title — usually a stub; ask which is real |

Unfilled template rows (title `{Publication Title}`) are ignored and listed on one line.

`EDITED` is only a candidate: merely opening or touching a Notion page bumps its edit
time. Step 4 decides whether anything really changed.

If the user referred to one paper ("another paper was updated") but several rows match,
propose the most recently edited one and ask, rather than processing them all.

### 2. Branch

`git fetch` and start a new branch from `origin/main`, named after the paper(s), e.g.
`add-<short-topic>-publication`. Ask before reusing an existing branch.

### 3. Process the selected rows in the scratchpad

Run in a fresh scratchpad directory, never in the repo — `process_publication` writes to
`./publications/` relative to the cwd:

```python
from publications import fetch_database, get_notion_token_from_aws_secret_manager, process_publication
tok = get_notion_token_from_aws_secret_manager()
pubs = fetch_database(tok, '851933e545a843799ac66da227acc50a')
for pid in [...selected page_ids...]:
    process_publication(pubs.loc[pubs.page_id == pid].iloc[0], notion_token=tok)
```

(`PYTHONPATH=<repo>/src`.) Each row yields `<page_id>.md` plus downloaded figures. Only the
`Exported` and `Fetching publication details` lines matter in the output.

### 4. Check the results

**New papers** — check, and report only problems:
- `date:` — CrossRef sometimes returns only a year (`YYYY-01-01`). Flag it and ask for the
  real publication date rather than guessing.
- Authors line is present; if CrossRef failed, it falls back to Notion's `Author` field.
- `link:` has no stray whitespace/tabs (Notion DOI fields have had leading tabs).
- Categories look right (tags + groups + journal + year).

**Edited papers** — run `diff -u <committed .md> <new .md>` and print it as-is. Then sort
each paper into one of:
- *No diff* → the Notion edit didn't change anything rendered. Say so in one line and skip it.
- *Only code-generated formatting* (e.g. the `{fig-alt="..."}` image syntax added by
  `add_figure_alt_text`) → the difference comes from a newer `src/publications.py`, not
  from Notion. Say that, and ask whether to include it.
- *Real content change* → apply it.

Manual fixes live only in the committed file (e.g. a hand-set `date:`), so keep them by
default: apply the Notion changes on top of the existing file, and only drop a manual fix
if the user approves. Figures that are byte-identical (`cmp`) don't need copying.

**Removed papers** — before proposing deletion, check `git log --oneline -- <the .md>`.
If history shows it was deliberately added back (e.g. a "restore" commit), the Notion
un-tick may be a mistake: ask whether the removal is intentional. If the user confirms,
list the `.md`, `docs/publications/<id>.html`, and figures no other `.md` references, and
ask before deleting any.

### 5. Copy in and render

Before rendering, confirm quarto sees the project — otherwise it silently renders a
standalone page next to the source instead of into `docs/` (this happens e.g. in checkouts
under a hidden directory such as `.claude/worktrees/`):

```bash
cd pheno_knowledge_base_expanded
quarto inspect . | python -c "import json,sys; print(len(json.load(sys.stdin)['files']['input']))"   # must be > 0
```

Then:

```bash
cp <scratch>/publications/<files> pheno_knowledge_base_expanded/publications/
cd pheno_knowledge_base_expanded
quarto render publications/<page_id>.md     # once per changed paper
quarto render publications.md               # rebuilds the listing
```

Every `Output created:` line must point under `../docs/`. If one doesn't, stop and report.
Render paper pages before the listing: the listing reads each item's author/description
line from the already-rendered pages in `docs/`. For removals, re-render
`publications.md` after deleting.

### 6. Verify

- `git status --short` — expect only the paper `.md`/figures, their `docs/` HTML/figures,
  and `docs/publications.html`, `docs/listings.json`, `docs/search.json`. No `??` `.html`
  or `_files/` under `pheno_knowledge_base_expanded/`.
- Re-rendering the listing rewrites `data-listing-file-modified-sort` on every item and may
  reorder same-date items in `listings.json`. That's expected (file mtimes), not a problem;
  don't hand-revert it.
- Listing count: `grep -c 'class="quarto-post' docs/publications.html` matches the
  expected number (previous count ± changes).
- Rendered page has the title and `alt="Figure from the publication: ..."` on figures.
- Offer a local preview: `python -m http.server 8765 --bind 127.0.0.1` from `docs/` (run in
  background), then the user forwards the port. Stop it when they're done.

### 7. Commit / push / PR — each only after the user's OK

Stage named files only (never `git add .`). Commit message style:

```
Add <short description> publication(s)

- Add source + rendered page for "<Title>" (<Journal>, <Year>) from Notion
- Rebuild publications listing (now N publications)

<Any manual fixes, skipped rows, or caveats>
```
