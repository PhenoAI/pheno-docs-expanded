"""List HPP publications that are new, edited or removed in Notion vs. the site.

Run from the repo root:
    PYTHONPATH=src python .claude/skills/update-publications/scripts/find_publication_changes.py
    python .claude/skills/update-publications/scripts/find_publication_changes.py --record <scratch>/exported.json [page_id ...]
    python .claude/skills/update-publications/scripts/find_publication_changes.py --forget <page_id> ...

Default mode is read-only. --record copies each page's Notion "Last edited time" *as of
export* (from the exported.json written in step 3) into the sync file - call it once a
paper's change is applied or deliberately skipped; with no page_ids it records every
page in the file. Using the export-time value means a Notion edit made after export is
still flagged next run. --forget drops pages from the sync file (after a removal).
Never prints the Notion token.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from publications import fetch_database, get_notion_token_from_aws_secret_manager

DATABASE_ID = '851933e545a843799ac66da227acc50a'
SRC_DIR = Path('pheno_knowledge_base_expanded/publications')
# page_id -> Notion last_edited_time of the version reflected on the site.
# Dotfile, so quarto ignores it.
SYNC_FILE = SRC_DIR / '.notion_sync.json'


def load_sync() -> dict:
    return json.loads(SYNC_FILE.read_text()) if SYNC_FILE.exists() else {}


def save_sync(sync: dict):
    SYNC_FILE.write_text(json.dumps(dict(sorted(sync.items())), indent=2) + '\n')


def last_commit_time(path: Path):
    out = subprocess.run(['git', 'log', '-1', '--format=%cI', '--', str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return datetime.fromisoformat(out) if out else None


def is_placeholder(title) -> pd.Series:
    # Unfilled template rows: empty title or "{Publication Title}"
    return title.fillna('').str.strip().str.match(r'^(\{.*\})?$')


def report(pubs: pd.DataFrame):
    sync = load_sync()
    checked = pubs.loc[pubs['Is relevant?'] == True]
    placeholder = is_placeholder(checked.Title)
    published = {p.stem: p for p in SRC_DIR.glob('*.md')}
    print(f'Notion rows: {len(pubs)} | ticked relevant: {len(checked)} | '
          f'published .md: {len(published)} | in sync file: {len(sync)}')

    rows = []
    unfilled = []
    for (_, r), ph in zip(checked.iterrows(), placeholder):
        md = published.get(r.page_id)
        edited = pd.Timestamp(r.last_edited_time).to_pydatetime()
        if ph:
            if md is not None:
                # A published paper whose Notion title was cleared - not a removal
                rows.append(('TITLE-CLEARED (published, still ticked)', r.page_id, edited.date(), md.stem))
            else:
                unfilled.append(r.page_id)
            continue
        if md is None:
            status = 'NEW' if pd.notna(r.Year) else 'NEW-SKIPPED (no Year; process_publication skips it)'
        elif r.page_id in sync:
            if edited <= pd.Timestamp(sync[r.page_id]).to_pydatetime():
                continue
            status = 'EDITED'
        else:
            committed = last_commit_time(md)
            if committed is None:
                status = 'UNCOMMITTED (.md exists but not in git)'
            elif edited > committed:
                status = 'EDITED (no sync entry; vs commit time)'
            else:
                continue
        rows.append((status, r.page_id, edited.date(), r.Title))

    if unfilled:
        print(f'Ignoring {len(unfilled)} unfilled template row(s) marked relevant: ' + ', '.join(unfilled))

    # Removal is decided against ALL ticked rows, before the placeholder filter
    checked_ids = set(checked.page_id)
    all_ids = set(pubs.page_id)
    for pid, md in published.items():
        if pid not in checked_ids:
            why = 'un-ticked "Is relevant?"' if pid in all_ids else 'deleted from Notion'
            rows.append((f'REMOVED ({why})', pid, None, md.read_text().split('\n')[1]))

    named = checked.loc[~placeholder]
    dup = named[named.Title.str.strip().str.lower().duplicated(keep=False)]
    for _, r in dup.iterrows():
        rows.append(('DUPLICATE-TITLE', r.page_id, None, r.Title))

    if not rows:
        print('No changes: the site matches Notion.')
    for status, pid, edited, title in sorted(rows):
        print(f'{status:<45} {pid}  {str(edited or ""):<10}  {title[:90]}')


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--record', nargs='+', metavar=('EXPORTED_JSON', 'PAGE_ID'))
    g.add_argument('--forget', nargs='+', metavar='PAGE_ID')
    args = ap.parse_args()

    if not SRC_DIR.is_dir():
        sys.exit(f'Run from the repo root ({SRC_DIR} not found)')

    sync = load_sync()
    if args.forget:
        for pid in args.forget:
            print(f'forget {pid}: {"removed" if sync.pop(pid, None) else "was not in sync file"}')
        save_sync(sync)
        return

    if args.record:
        exported = json.loads(Path(args.record[0]).read_text())
        ids = args.record[1:] or list(exported)
        missing = [p for p in ids if p not in exported]
        if missing:
            sys.exit(f'Not in {args.record[0]}: {", ".join(missing)}')
        for pid in ids:
            sync[pid] = exported[pid]
            print(f'record {pid}: {sync[pid]}')
        save_sync(sync)
        return

    report(fetch_database(get_notion_token_from_aws_secret_manager(), DATABASE_ID))


if __name__ == '__main__':
    main()
