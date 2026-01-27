#!/usr/bin/env python3
import re
import os
import sys

# Configuration
REPO_OWNER = "Furglitch"
REPO_NAME = "mc-resourcepack"
BRANCH = "master"
DOCS_DIR = "docs"

def remove_unwanted_elements(content):
    """Remove specific HTML elements and tags"""
    # Remove the human-made-floater section
    pattern_floater = r'---\s*<p><center>\s*<a class="human-made-floater"[^>]*>.*?</a>\s*</center></p>'
    content = re.sub(pattern_floater, '', content, flags=re.DOTALL)
    
    # Also try without the --- prefix in case it varies
    pattern_floater_alt = r'<p><center>\s*<a class="human-made-floater"[^>]*>.*?</a>\s*</center></p>'
    content = re.sub(pattern_floater_alt, '', content, flags=re.DOTALL)
    
    # Remove </br> tags (note: <br> is self-closing, </br> is invalid HTML)
    content = content.replace('</br>', '')
    
    # Remove YouTube thumbnail links (anchor tags wrapping img with youtube thumbnails)
    pattern_yt_thumbnail = r'<a\s+href=["\']https?://(?:www\.)?youtube\.com/watch\?v=[^"\']+["\']>\s*<img\s+src=["\']https?://img\.youtube\.com/vi/[^"\']+["\'][^>]*>\s*</a>'
    content = re.sub(pattern_yt_thumbnail, '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove <div hidden> wrapper and just keep the iframe
    # This pattern matches <div hidden>...<iframe...></iframe></div> and replaces it with just the iframe
    pattern_hidden_div = r'<div\s+hidden>\s*(<iframe[^>]*>.*?</iframe>)\s*</div>'
    content = re.sub(pattern_hidden_div, r'\1', content, flags=re.DOTALL | re.IGNORECASE)
    
    return content

def convert_image_paths(content, readme_dir):
    """Convert relative image paths to raw.githubusercontent.com URLs"""
    def replace_img(match):
        full_match = match.group(0)
        src = match.group(1)
        
        # Skip if already absolute URL
        if src.startswith(('http://', 'https://', '//')):
            return full_match
        
        # Calculate the full path relative to repo root
        if readme_dir:
            full_path = os.path.join(readme_dir, src)
        else:
            full_path = src
        
        # Normalize path (remove ./ and resolve ..)
        full_path = os.path.normpath(full_path)
        
        # Create the GitHub raw URL
        new_src = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/refs/heads/{BRANCH}/{full_path}"
        
        return full_match.replace(src, new_src)
    
    # Match img src attributes
    pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
    content = re.sub(pattern, replace_img, content)
    
    # Match markdown image syntax ![alt](path)
    def replace_md_img(match):
        alt = match.group(1)
        src = match.group(2)
        
        if src.startswith(('http://', 'https://', '//')):
            return match.group(0)
        
        if readme_dir:
            full_path = os.path.join(readme_dir, src)
        else:
            full_path = src
        
        full_path = os.path.normpath(full_path)
        new_src = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/refs/heads/{BRANCH}/{full_path}"
        
        return f"![{alt}]({new_src})"
    
    pattern_md = r'!\[([^\]]*)\]\(([^)]+)\)'
    content = re.sub(pattern_md, replace_md_img, content)
    
    return content

def convert_link_paths(content, readme_dir):
    """Convert relative directory/file links to github.com URLs"""
    def replace_link(match):
        text = match.group(1)
        href = match.group(2)
        
        # Skip if already absolute URL or anchor
        if href.startswith(('http://', 'https://', '//', '#')):
            return match.group(0)
        
        # Calculate full path
        if readme_dir:
            full_path = os.path.join(readme_dir, href)
        else:
            full_path = href
        
        full_path = os.path.normpath(full_path)
        
        # Determine if it's a directory or file
        # Directories typically end with / or are folders
        if href.endswith('/') or not '.' in os.path.basename(href):
            # Directory link
            new_href = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/tree/{BRANCH}/{full_path}"
        else:
            # File link - could be markdown or other file
            if href.endswith('.md'):
                # For markdown files, link to the rendered version on GitHub
                new_href = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/{BRANCH}/{full_path}"
            else:
                # For other files, use raw URL
                new_href = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/refs/heads/{BRANCH}/{full_path}"
        
        return f"[{text}]({new_href})"
    
    # Match markdown link syntax [text](path)
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    content = re.sub(pattern, replace_link, content)
    
    return content

def process_readme(file_path, readme_dir):
    """Process a single README file"""
    print(f"Processing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove unwanted elements first
    content = remove_unwanted_elements(content)
    
    # Convert paths
    content = convert_image_paths(content, readme_dir)
    content = convert_link_paths(content, readme_dir)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Converted paths in {file_path}")

def find_markdown_files(directory):
    """Recursively find all .md files in the directory"""
    md_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                md_files.append(file_path)
    return md_files

def get_relative_dir(file_path, docs_dir):
    """Get the directory path relative to repo root"""
    # Get the directory containing the markdown file
    file_dir = os.path.dirname(file_path)
    
    # Remove the docs_dir prefix to get the relative path from repo root
    if file_dir.startswith(docs_dir):
        relative = file_dir[len(docs_dir):].lstrip(os.sep)
        return relative
    
    return ''

def main():
    if not os.path.exists(DOCS_DIR):
        print(f"Error: {DOCS_DIR} directory not found")
        sys.exit(1)
    
    # Find all markdown files in docs directory
    md_files = find_markdown_files(DOCS_DIR)
    
    if not md_files:
        print(f"No markdown files found in {DOCS_DIR}")
        sys.exit(0)
    
    print(f"Found {len(md_files)} markdown file(s)")
    
    for file_path in md_files:
        readme_dir = get_relative_dir(file_path, DOCS_DIR)
        process_readme(file_path, readme_dir)
    
    print(f"\n✅ Successfully processed {len(md_files)} file(s)")

if __name__ == '__main__':
    main()
