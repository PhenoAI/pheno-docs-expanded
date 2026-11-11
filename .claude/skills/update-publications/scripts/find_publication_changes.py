"""List HPP publications that are new, edited or removed in Notion vs. the site.

Run from the repo root:  PYTHONPATH=src python .claude/skills/update-publications/scripts/find_publication_changes.py
Read-only: queries Notion and git, writes nothing. Never prints the Notion token.
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from publications import fetch_database, get_notion_token_from_aws_secret_manager

DATABASE_ID = '851933e545a843799ac66da227acc50a'
SRC_DIR = Path('pheno_knowledge_base_expanded/publications')


def last_commit_time(path: Path):
    out = subprocess.run(['git', 'log', '-1', '--format=%cI', '--', str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return datetime.fromisoformat(out) if out else None


def main():
    if not SRC_DIR.is_dir():
        sys.exit(f'Run from the repo root ({SRC_DIR} not found)')

    pubs = fetch_database(get_notion_token_from_aws_secret_manager(), DATABASE_ID)
    relevant = pubs.loc[pubs['Is relevant?'] == True]
    # Unfilled template rows (title like "{Publication Title}" or empty) are not papers
    placeholder = relevant.Title.fillna('').str.strip().str.match(r'^(\{.*\})?$')
    if placeholder.any():
        print(f'Ignoring {placeholder.sum()} unfilled template row(s) marked relevant: '
              + ', '.join(relevant.loc[placeholder, 'page_id']))
    relevant = relevant.loc[~placeholder]
    published = {p.stem: p for p in SRC_DIR.glob('*.md')}
    print(f'Notion rows: {len(pubs)} | relevant: {len(relevant)} | published .md: {len(published)}')

    rows = []
    for _, r in relevant.iterrows():
        md = published.get(r.page_id)
        edited = pd.Timestamp(r.last_edited_time).to_pydatetime()
        if md is None:
            status = 'NEW' if pd.notna(r.Year) else 'NEW-SKIPPED (no Year; process_publication skips it)'
        else:
            committed = last_commit_time(md)
            if committed is None:
                status = 'UNCOMMITTED (.md exists but not in git)'
            elif edited > committed:
                status = 'EDITED'
            else:
                continue
        rows.append((status, r.page_id, edited.date(), r.Title))

    relevant_ids = set(relevant.page_id)
    all_ids = set(pubs.page_id)
    for pid, md in published.items():
        if pid not in relevant_ids:
            why = 'un-ticked "Is relevant?"' if pid in all_ids else 'deleted from Notion'
            rows.append((f'REMOVED ({why})', pid, None, md.read_text().split('\n')[1]))

    dup = relevant[relevant.Title.str.strip().str.lower().duplicated(keep=False)]
    for _, r in dup.iterrows():
        rows.append(('DUPLICATE-TITLE', r.page_id, None, r.Title))

    if not rows:
        print('No changes: the site matches Notion.')
    for status, pid, edited, title in sorted(rows):
        print(f'{status:<45} {pid}  {str(edited or ""):<10}  {title[:90]}')


if __name__ == '__main__':
    main()
