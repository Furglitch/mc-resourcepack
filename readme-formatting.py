#!/usr/bin/env python3
import argparse
import difflib
import os
import re
import sys


def replace_urls(content: str, to_modrinth: bool) -> str:
    if to_modrinth:
        pattern = re.compile(r'https?://(?:www\.)?curseforge\.com/minecraft/mc-mods/[A-Za-z0-9_\-./%]+')
        def repl(m):
            start = m.start()
            line_start = content.rfind('\n', 0, start) + 1
            line_end = content.find('\n', m.end())
            if line_end == -1:
                line_end = len(content)
            line = content[line_start:line_end]
            if 'shields.io' in line or 'img.shields' in line or ('shields' in line and 'img' in line):
                return m.group(0)
            tail = m.group(0).split('/')[-1]
            return 'https://modrinth.com/mod/' + tail
        return pattern.sub(repl, content)
    else:
        pattern = re.compile(r'https?://(?:www\.)?modrinth\.com/mod/[A-Za-z0-9_\-./%]+')
        def repl(m):
            start = m.start()
            line_start = content.rfind('\n', 0, start) + 1
            line_end = content.find('\n', m.end())
            if line_end == -1:
                line_end = len(content)
            line = content[line_start:line_end]
            if 'shields.io' in line or 'img.shields' in line or ('shields' in line and 'img' in line):
                return m.group(0)
            tail = m.group(0).split('/')[-1]
            return 'https://curseforge.com/minecraft/mc-mods/' + tail
        return pattern.sub(repl, content)


def transform_p_align(content: str, to_modrinth: bool) -> str:
    if to_modrinth:
        out = re.sub(r'<p\s+align=["\']center["\']>(.*?)</p>', r'<p><center>\1</center></p>', content, flags=re.DOTALL|re.IGNORECASE)
        out = re.sub(r'<p\s+style=["\']\s*text-align\s*:\s*center\s*["\']>(.*?)</p>', r'<p><center>\1</center></p>', out, flags=re.DOTALL|re.IGNORECASE)
        return out
    else:
        out = re.sub(r'<p>\s*<center>(.*?)</center>\s*</p>', r'<p style="text-align:center">\1</p>', content, flags=re.DOTALL|re.IGNORECASE)
        out = re.sub(r'<p\s+align=["\']center["\']>(.*?)</p>', r'<p style="text-align:center">\1</p>', out, flags=re.DOTALL|re.IGNORECASE)
        return out


def remove_youtube_thumbnail_and_unhide(content: str) -> str:
    content = re.sub(r'<a[^>]*>\s*<img[^>]*https?://img\.youtube\.com/vi/[^>]*>\s*</a>\s*', '', content, flags=re.IGNORECASE|re.DOTALL)
    content = re.sub(r'<div[^>]*hidden[^>]*>(.*?)</div>', r'\1', content, flags=re.IGNORECASE|re.DOTALL)
    return content


OWNER = 'Furglitch'
REPO = 'mc-resourcepack'
BRANCH = 'master'


def replace_icon_path(content: str, rel_dir: str) -> str:
    """Replace occurrences of local icon.png with raw.githubusercontent URL for that folder.

    Example result:
    https://raw.githubusercontent.com/Furglitch/mc-resourcepack/refs/heads/master/noticably-suspicious/icon.png
    """

    if rel_dir in ('.', ''):
        icon_url = f'https://raw.githubusercontent.com/{OWNER}/{REPO}/refs/heads/{BRANCH}/icon.png'
    else:
        # Ensure no leading './'
        rel = rel_dir.lstrip('./')
        icon_url = f'https://raw.githubusercontent.com/{OWNER}/{REPO}/refs/heads/{BRANCH}/{rel}/icon.png'

    content = re.sub(r'(src\s*=\s*["\'])(?:\./|/)?icon\.png(["\'])', r"\1" + icon_url + r"\2", content, flags=re.IGNORECASE)

    content = re.sub(r'(\!\[[^\]]*\]\()(?:\./|/)?icon\.png(\))', r"\1" + icon_url + r"\2", content)
    content = re.sub(r'(\[[^\]]*\]\()(?:\./|/)?icon\.png(\))', r"\1" + icon_url + r"\2", content)

    return content


def replace_screenshot_paths(content: str, rel_dir: str) -> str:
    """Replace local screenshots paths (HTML src and Markdown image links) with raw.githubusercontent URLs."""
    # Build base URL for screenshots in this directory
    if rel_dir in ('.', ''):
        base = f'https://raw.githubusercontent.com/{OWNER}/{REPO}/refs/heads/{BRANCH}/screenshots'
    else:
        rel = rel_dir.lstrip('./')
        base = f'https://raw.githubusercontent.com/{OWNER}/{REPO}/refs/heads/{BRANCH}/{rel}/screenshots'

    # HTML img src attributes: src="screenshots/..." or src='./screenshots/...'
    content = re.sub(r'(src\s*=\s*["\'])(?:\./|/)?screenshots/([^"\'>\s]+)(["\'])', r"\1" + base + r"/\2" + r"\3", content, flags=re.IGNORECASE)

    # Markdown image syntax: ![alt](screenshots/...) or [img](screenshots/...)
    content = re.sub(r'(\!\[[^\]]*\]\()(?:\./|/)?screenshots/([^\)\s]+)(\))', r"\1" + base + r"/\2" + r"\3", content)
    content = re.sub(r'(\[[^\]]*\]\()(?:\./|/)?screenshots/([^\)\s]+)(\))', r"\1" + base + r"/\2" + r"\3", content)

    return content


def transform_centered_headings(content: str, to_modrinth: bool) -> str:
    """When converting to CurseForge, replace <h1 align="center"> and <h2 align="center">
    with a div wrapper using inline style (which CurseForge prefers).
    Example: <h1 align="center">Title</h1> -> <div style="text-align:center"><h1>Title</h1></div>
    """
    if to_modrinth:
        # Undo div-wrapped centerings: convert <div style="text-align:center"><h1>..</h1></div>
        # back to <h1 align="center">..</h1>. Also convert <h3> back to <h2>.
        def _unwrap(m):
            level = m.group(1)
            inner = m.group(2)
            out_level = '2' if level == '3' else level
            return f'<h{out_level} align="center">{inner}</h{out_level}>'

        out = re.sub(r'<div[^>]*style=["\"][^"\"]*text-align\s*:\s*center[^"\"]*["\"][^>]*>\s*<h([123])\b[^>]*>(.*?)</h\1>\s*</div>', _unwrap, content, flags=re.DOTALL|re.IGNORECASE)
        return out
    # handle h1 and h2 with align="center" (attributes may appear in any order)
    pattern = re.compile(r'<h([12])\b([^>]*)\balign=["\']center["\']([^>]*)>(.*?)</h\1>', flags=re.DOTALL|re.IGNORECASE)
    def _wrap(m):
        level = m.group(1)
        inner = m.group(4)
        # For CurseForge, change h2 to h3 as requested
        out_level = '3' if level == '2' else level
        return f'<div style="text-align:center"><h{out_level}>{inner}</h{out_level}></div>'

    out = pattern.sub(_wrap, content)
    # Also convert any existing <div style="text-align:center"> <h2>...</h2> </div> to use h3
    out = re.sub(r'(<div[^>]*style=["\"][^"\"]*text-align\s*:\s*center[^"\"]*["\"][^>]*>\s*)<h2\b([^>]*)>(.*?)</h2>(\s*</div>)', r'\1<h3\2>\3</h3>\4', out, flags=re.DOTALL|re.IGNORECASE)
    return out


def should_skip(path: str, repo_root: str) -> bool:
    rel = os.path.relpath(path, repo_root)
    if os.path.normpath(rel) == 'README.md':
        return True
    parts = rel.split(os.sep)
    if '.example' in parts:
        return True
    return False


def process_file(path: str, to_modrinth: bool, repo_root: str, dry_run: bool = False):
    """Process a file. Returns (changed: bool, original: str, new: str).

    If dry_run is False, the file will be written when changed.
    """
    with open(path, 'r', encoding='utf-8') as f:
        original = f.read()
    new = original
    new = replace_urls(new, to_modrinth)
    rel_dir = os.path.relpath(os.path.dirname(path), repo_root)
    new = replace_icon_path(new, rel_dir)
    # Replace screenshots paths with raw.githubusercontent URLs
    new = replace_screenshot_paths(new, rel_dir)
    new = transform_p_align(new, to_modrinth)
    new = transform_centered_headings(new, to_modrinth)
    new = remove_youtube_thumbnail_and_unhide(new)
    changed = (new != original)
    if changed and not dry_run:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new)
    return changed, original, new


def main():
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--modrinth', action='store_true', help='Convert CurseForge links to Modrinth and adjust HTML')
    group.add_argument('--curseforge', action='store_true', help='Convert Modrinth links to CurseForge and adjust HTML')
    p.add_argument('--root', default='.', help='Repository root (default: current directory)')
    p.add_argument('--dry-run', action='store_true', help='Show changes (diffs) without modifying files')
    args = p.parse_args()
    repo_root = os.path.abspath(args.root)
    to_modrinth = args.modrinth
    dry_run = args.dry_run

    changed = []
    diffs = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        if '.example' in dirpath.split(os.sep):
            continue
        for name in filenames:
            if name != 'README.md':
                continue
            path = os.path.join(dirpath, name)
            if should_skip(path, repo_root):
                continue
            try:
                file_changed, original, new = process_file(path, to_modrinth, repo_root, dry_run=dry_run)
                if file_changed:
                    changed.append(os.path.relpath(path, repo_root))
                    if dry_run:
                        ud = ''.join(difflib.unified_diff(
                            original.splitlines(keepends=True),
                            new.splitlines(keepends=True),
                            fromfile=os.path.relpath(path, repo_root) + ' (original)',
                            tofile=os.path.relpath(path, repo_root) + ' (modified)'))
                        diffs.append((os.path.relpath(path, repo_root), ud))
            except Exception as e:
                print(f'Error processing {path}: {e}', file=sys.stderr)

    if dry_run:
        if diffs:
            print('Files that would be changed:')
            for pth, ud in diffs:
                print('\n---', pth)
                print(ud)
        else:
            print('No files would be changed')
    else:
        if changed:
            print('Updated files:')
            for c in changed:
                print(' -', c)
        else:
            print('No files changed')


if __name__ == '__main__':
    main()
