import json
import re
import subprocess
from pathlib import Path
import shutil
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests
import boto3
import pandas as pd
from Bio import Entrez
from notion_client import Client


def get_notion_token_from_aws_secret_manager(aws_region: str='eu-west-1', secret_id: str='notion_token') -> str:
    """
    Retrieve a secret from AWS Secrets Manager.

    Args:
        secret_name: The name of the secret.

    Returns:
        dict: The secret as a dictionary.
    """
    session = boto3.Session(region_name=aws_region)
    client = session.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_id)
    dict_secret = json.loads(response["SecretString"])

    return dict_secret['notion_token']


def fetch_database(notion_token: str, database_id: str):
    """
    High-level function to fetch a database from Notion and return a pandas DataFrame.
    """
    notion_client = Client(auth=notion_token)
    return pages_to_dataframe(fetch_all_database_pages(notion_client, database_id))


def fetch_all_database_pages(notion_client: Client, database_id: str):
    """
    Low-level function to fetch all pages from a Notion database.
    """
    all_pages = []
    start_cursor = None

    while True:
        response = notion_client.databases.query(
            database_id=database_id,
            start_cursor=start_cursor,
            page_size=100
        )
        all_pages.extend(response.get("results", []))
        
        if response.get("has_more"):
            start_cursor = response.get("next_cursor")
        else:
            break

    return all_pages

def pages_to_dataframe(pages: list):
    """
    Low-level function to convert a list of Notion pages to a pandas DataFrame.
    """
    rows = []
    for page in pages:
        row_data = {
            "page_id": page.get("id"),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
        }

        properties = page.get("properties", {})
        for prop_name, prop_data in properties.items():
            row_data[prop_name] = parse_property_value(prop_data)

        rows.append(row_data)

    return pd.DataFrame(rows)


def parse_property_value(prop_data: dict):
    """
    Low-level function to parse the value of a Notion property.
    """
    prop_type = prop_data.get("type")

    if prop_type == "title":
        title_list = prop_data.get("title", [])
        return " ".join(t["plain_text"] for t in title_list) if title_list else ""

    elif prop_type == "rich_text":
        rich_text_list = prop_data.get("rich_text", [])
        return " ".join(t["plain_text"] for t in rich_text_list) if rich_text_list else ""

    elif prop_type == "select":
        select_data = prop_data.get("select")
        return select_data["name"] if select_data else None

    elif prop_type == "multi_select":
        multi_select_list = prop_data.get("multi_select", [])
        return [option["name"] for option in multi_select_list] if multi_select_list else []

    elif prop_type == "checkbox":
        return prop_data.get("checkbox", False)

    elif prop_type == "number":
        return prop_data.get("number", None)

    elif prop_type == "date":
        date_data = prop_data.get("date")
        if date_data is None:
            return None
        return (date_data.get("start"), date_data.get("end"))

    elif prop_type == "url":
        return prop_data.get("url", None)

    elif prop_type == "email":
        return prop_data.get("email", None)

    elif prop_type == "phone_number":
        return prop_data.get("phone_number", None)

    elif prop_type == "people":
        people_list = prop_data.get("people", [])
        return [person["name"] for person in people_list if "name" in person]

    return prop_data  # Fallback: return raw if not handled


def process_publication(row: pd.Series, notion_token: str=None):
    """
    Process a publication row by fetching the publication details and creating a markdown file.
    """
    if pd.isna(row.Year):
        return

    # Run notion2md as subprocess
    subprocess.run(['notion2md', '--download', '--unzipped', 
                   '--path=publications',
                   f'--token={notion_token}', 
                   f'--id={row.page_id}'], check=True)
    
    # Get markdown file path
    md_file = Path(f'publications/{row.page_id}.md')
    
    # Read existing content
    with open(md_file) as f:
        content = f.read()
    
    has_business = "business summary" in content.lower()
    has_paper = "paper summary" in content.lower()
    if has_business and has_paper:
        # Remove business summary section
        content = re.sub(r'(?i)## business summary.*?(?=\n#|$)', '', content, flags=re.DOTALL)
        content = content.strip()
    elif has_business:
        # Rename business summary to paper summary
        content = re.sub(r'(?i)## business summary', '## Paper summary', content)

    # Remove related links section
    content = re.sub(r'(?i)## related links.*?(?=\n#|$)', '', content, flags=re.DOTALL)
    content = re.sub(r'(?i)## relevant links.*?(?=\n#|$)', '', content, flags=re.DOTALL)
    content = content.strip()

    # Extract first image if present
    image_match = re.search(r'!\[.*?\]\((.*?)\)', content)
    image_path = f'image: {image_match.group(1)}' if image_match else ''
    
    # Clean journal name by removing trailing periods
    journal_name = row['Journal'].rstrip('.') if isinstance(row['Journal'], str) else ''

    weblink = row['weblink'] if row['weblink'] else ''
    if 'arxiv.org' not in weblink:
        weblink = row['DOI'] if row['DOI'] else weblink
    authors, pub_date, abstract = get_publication_details(weblink)
    abstract = '## Paper summary\n\n' + abstract if abstract else ''
    year = pub_date.split('-')[0] if pub_date else row['Year']

    # Create frontmatter
    categories = list(row['Tags']) + list(row['Groups involved']) + [journal_name] + [year]
    frontmatter = f"""---
title: "{row['Title']}"
date: "{pub_date if pub_date else row['Year']}"
link: {weblink}
{image_path}
categories:
{chr(10).join(f'  - "{cat}"' for cat in categories)}
---

{', '.join(authors)}, [*{journal_name}*]({weblink})

{abstract if not has_business and not has_paper else ''}

"""

    # Write new content with frontmatter
    with open(md_file, 'w') as f:
        f.write(frontmatter + content)


def get_publication_details(weblink: str) -> tuple[list[str], str, str]:
    """
    Extract publication details from DOI using CrossRef API with fallback for preprints
    Returns author list, publication date and abstract
    """
    if not weblink:
        return [], None, None

    print('Fetching publication details for', weblink)

    # Handle arXiv preprints
    if 'arxiv.org' in weblink:
        return get_arxiv_details(weblink)
    
    # Handle bioRxiv/medRxiv preprints or DOIs
    doi = None
    if 'doi.org' in weblink:
        doi = urlparse(weblink).path.strip('/')
    elif any(x in weblink for x in ['biorxiv.org', 'medrxiv.org']):
        # Extract DOI from biorxiv/medrxiv URL (usually in format: /content/10.1101/...)
        match = re.search(r'10\.1101/[0-9.]+', weblink)
        if match:
            doi = match.group(0)

    if doi:
        try:
            # Use CrossRef API
            response = requests.get(f'https://api.crossref.org/works/{doi}')
            response.raise_for_status()
            data = response.json()['message']

            # Extract authors
            authors = []
            if 'author' in data:
                for author in data['author']:
                    if 'family' in author:
                        # Take first initial of given name if available
                        if 'given' in author:
                            first_initial = author['given'][0]
                            authors.append(f"{author['family']} {first_initial}")
                        else:
                            authors.append(author['family'])

            # Extract publication date
            pub_date = None
            if 'issued' in data:
                date_parts = data['issued']['date-parts'][0]    
            elif 'published-print' in data:
                date_parts = data['published-print']['date-parts'][0]
            elif 'published-online' in data:
                date_parts = data['published-online']['date-parts'][0]
            elif 'created' in data:
                date_parts = data['created']['date-parts'][0]
            else:
                return authors, None, None

            if len(date_parts) >= 3:
                pub_date = f"{date_parts[0]}-{date_parts[1]:0>2}-{date_parts[2]:0>2}"
            elif len(date_parts) >= 1:
                pub_date = f"{date_parts[0]}-01-01"

            # Extract abstract
            abstract = data.get('abstract', None)

            # return data
            return authors, pub_date, abstract

        except Exception as e:
            print(f"Error fetching CrossRef details: {e}")
            return [], None, None

    return [], None, None


def get_arxiv_details(weblink: str) -> tuple[list[str], str, str]:
    """
    Extract publication details from arXiv using their API
    """
    try:
        # Extract arXiv ID from URL or DOI
        arxiv_id = None
        if 'arxiv.org' in weblink:
            # Handle different arXiv URL formats
            arxiv_id = urlparse(weblink).path.split('/')[-1]
        print(arxiv_id)
        
        if not arxiv_id:
            return [], None, None

        # Query arXiv API
        response = requests.get(
            'http://export.arxiv.org/api/query',
            params={'id_list': arxiv_id}
        )
        response.raise_for_status()

        # Parse XML response
        root = ElementTree.fromstring(response.content)

        # Extract authors (using namespace)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        authors = []
        for author in root.findall('.//atom:author/atom:name', ns):
            # Split name and take first initial of given name
            name_parts = author.text.split()
            if len(name_parts) > 1:
                last_name = name_parts[-1]
                first_initial = name_parts[0][0]
                authors.append(f"{last_name} {first_initial}")
            else:
                authors.append(author.text)

        # Extract publication date
        published = root.find('.//atom:published', ns)
        pub_date = None
        if published is not None:
            # arXiv date format: YYYY-MM-DDTHH:MM:SSZ
            pub_date = published.text[:10]  # Take just YYYY-MM-DD

        # Extract abstract
        abstract = None
        summary = root.find('.//atom:summary', ns)
        if summary is not None:
            abstract = summary.text

        return authors, pub_date, abstract

    except Exception as e:
        print(f"Error fetching arXiv details: {e}")
        return [], None, None


def move_publications_to_website():
    """
    Move publications to the website folder by removing old folder and moving new one
    """
    dest = Path('../pheno_knowledge_base_expanded/publications')
    
    # Remove old publications folder if it exists
    if dest.exists():
        shutil.rmtree(dest)
    
    # Move new publications folder
    shutil.move('publications', str(dest))
