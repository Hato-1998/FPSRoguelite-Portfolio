"""Verify the reading repository; does not build or run Unreal Engine.

Usage:
    python tools/verify_portfolio.py
    python tools/verify_portfolio.py --source-repo /path/to/private/project
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-repo', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'source-manifest.json').read_text(encoding='utf-8'))
    errors = []
    checked_links = 0
    cache = {}
    known_blocks = set()

    for entry in manifest['excerpts']:
        sample = (root / entry['sample']).resolve()
        if not sample.is_relative_to(root):
            errors.append('Sample path escapes repository')
            continue
        text = sample.read_text(encoding='utf-8')
        blocks = re.findall(r'^```cpp\n(.*?)^```\s*$', text, re.M | re.S)
        index = entry['block_index']
        key = (entry['sample'], index)
        if key in known_blocks:
            errors.append(f'Duplicate manifest block: {key}')
        known_blocks.add(key)
        if index >= len(blocks):
            errors.append(f'Missing block: {key}')
            continue
        code = blocks[index]
        if hashlib.sha256(code.encode('utf-8')).hexdigest() != entry['sha256']:
            errors.append(f'Excerpt digest mismatch: {key}')
        if args.source_repo:
            path = entry['source_path']
            if path not in cache:
                result = subprocess.run(
                    ['git', '-C', str(args.source_repo), 'show',
                     manifest['source_commit'] + ':' + path],
                    check=True, capture_output=True,
                )
                cache[path] = result.stdout.decode('utf-8').replace('\r\n', '\n')
            start, end = entry['start_line'], entry['end_line']
            original = ''.join(cache[path].splitlines(keepends=True)[start - 1:end])
            if original != code:
                errors.append(f'Original source mismatch: {key}')

    for file in sorted(root.rglob('*.md')):
        if '.git' in file.relative_to(root).parts:
            continue
        text = file.read_text(encoding='utf-8')
        fences = re.findall(r'^```.*$', text, re.M)
        if len(fences) % 2:
            errors.append(f'Unbalanced code fences: {file.relative_to(root)}')
        if file.parent.name == 'samples':
            count = len(re.findall(r'^```cpp$', text, re.M))
            for index in range(count):
                if (file.relative_to(root).as_posix(), index) not in known_blocks:
                    errors.append(f'Unregistered code block: {file.name}:{index}')
        prose = re.sub(r'^```.*?^```\s*$', '', text, flags=re.M | re.S)
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', prose):
            url = urlsplit(target)
            if url.scheme or not url.path:
                continue
            destination = (file.parent / unquote(url.path)).resolve()
            checked_links += 1
            if not destination.is_relative_to(root) or not destination.exists():
                errors.append(f'Broken/local-only link: {file.name} -> {target}')

    allowed_suffixes = {'.md', '.json', '.py'}
    allowed_names = {'.gitignore', '.gitattributes'}
    for file in root.rglob('*'):
        if not file.is_file():
            continue
        parts = file.relative_to(root).parts
        if '.git' in parts or '__pycache__' in parts:
            continue
        if file.name not in allowed_names and file.suffix not in allowed_suffixes:
            errors.append(f'Unexpected publication file: {file.relative_to(root)}')

    if errors:
        for error in errors:
            print('FAIL:', error)
        raise SystemExit(1)
    print(f'PASS: {len(manifest["excerpts"])} excerpt hashes; '
          f'{checked_links} local links; code fences; publication file types.')
    if args.source_repo:
        print(f'PASS: all excerpts match source commit {manifest["source_commit"]}.')
    else:
        print('Source comparison skipped (use --source-repo). Unreal tests not run.')


if __name__ == '__main__':
    main()
