#!/bin/bash

# Create a combined knowledge base from all website content

OUTPUT="pheno_knowledge_base_expanded/knowledge-base-context.txt"
SOURCE_DIR="pheno_knowledge_base_expanded"

echo "Creating knowledge base from website content..."
echo "" > "$OUTPUT"

echo "=== HUMAN PHENOTYPE PROJECT DOCUMENTATION ===" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Function to add file content with header
add_file_to_context() {
    local file="$1"
    local relative_path="${file#$SOURCE_DIR/}"
    
    echo "" >> "$OUTPUT"
    echo "## FILE: $relative_path" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    cat "$file" 2>/dev/null >> "$OUTPUT"
    echo "" >> "$OUTPUT"
}

# Function to extract first 2 cells from notebook
add_notebook_to_context() {
    local file="$1"
    local relative_path="${file#$SOURCE_DIR/}"
    
    echo "" >> "$OUTPUT"
    echo "## FILE: $relative_path" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    
    # Extract first 2 cells from notebook using jq
    if command -v jq &> /dev/null; then
        jq -r '.cells[:2] | .[] | .source | if type == "array" then join("") else . end' "$file" 2>/dev/null >> "$OUTPUT"
    else
        # Fallback: use python if jq is not available
        python3 -c "
import json, sys
try:
    with open('$file', 'r') as f:
        nb = json.load(f)
    for cell in nb.get('cells', [])[:2]:
        source = cell.get('source', [])
        if isinstance(source, list):
            print(''.join(source))
        else:
            print(source)
        print()
except Exception as e:
    pass
" >> "$OUTPUT"
    fi
    
    echo "" >> "$OUTPUT"
}

# Counter for progress
file_count=0

echo "Processing .md files..."
while IFS= read -r -d '' file; do
    add_file_to_context "$file"
    ((file_count++))
    echo "  Added: ${file#$SOURCE_DIR/}"
done < <(find "$SOURCE_DIR" -type f -name "*.md" -not -path "*/publications/*" -print0 | sort -z)

echo "Processing .qmd files..."
while IFS= read -r -d '' file; do
    add_file_to_context "$file"
    ((file_count++))
    echo "  Added: ${file#$SOURCE_DIR/}"
done < <(find "$SOURCE_DIR" -type f -name "*.qmd" -print0 | sort -z)

echo "Processing .ipynb files (first 2 cells only)..."
while IFS= read -r -d '' file; do
    add_notebook_to_context "$file"
    ((file_count++))
    echo "  Added: ${file#$SOURCE_DIR/}"
done < <(find "$SOURCE_DIR" -type f -name "*.ipynb" -print0 | sort -z)

echo ""
echo "✅ Knowledge base created: $OUTPUT"
echo "📊 Total files processed: $file_count"
echo "📦 Size: $(du -h $OUTPUT | cut -f1)"









