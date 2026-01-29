import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from auto_clean import auto_clean_background


def extract_id(filename):
    nums = re.findall(r'(\d{4})', filename)
    return nums[-1] if nums else None


def build_map(folder):
    mapping = {}
    for path in Path(folder).glob('*'):
        if path.is_file():
            img_id = extract_id(path.name)
            if img_id:
                mapping[img_id] = str(path)
    return mapping


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bg-dir', default='images/bg')
    parser.add_argument('--pod-dir', default='images/pod')
    parser.add_argument('--seed-dir', default='images/seed')
    parser.add_argument('--out-dir', default='outputs')
    parser.add_argument('--force', action='store_true', help='Overwrite existing outputs')
    args = parser.parse_args()

    bg_map = build_map(args.bg_dir)
    pod_map = build_map(args.pod_dir)
    seed_map = build_map(args.seed_dir)

    ids = sorted(set(bg_map) & set(pod_map) & set(seed_map))
    if not ids:
        print('No matching groups found.')
        return

    out_dir = Path(args.out_dir)
    out_bg = out_dir / 'bg_cleaned'
    out_final = out_dir / 'final'
    out_bg.mkdir(parents=True, exist_ok=True)
    out_final.mkdir(parents=True, exist_ok=True)

    print(f'Found {len(ids)} groups.')

    for idx, img_id in enumerate(ids, 1):
        bg_path = bg_map[img_id]
        pod_path = pod_map[img_id]
        seed_path = seed_map[img_id]

        cleaned_path = out_bg / f'{img_id}_bg_cleaned.jpg'
        final_path = out_final / f'{img_id}_final.jpg'

        if final_path.exists() and not args.force:
            print(f'[{idx}/{len(ids)}] Skip {img_id} (final exists)')
            continue

        print(f'[{idx}/{len(ids)}] Processing {img_id}')
        auto_clean_background(bg_path, str(cleaned_path))

        cmd = [
            sys.executable, 'main.py',
            '--cleaned', str(cleaned_path),
            '--pod', pod_path,
            '--seed', seed_path,
            '--out', str(final_path),
        ]
        subprocess.run(cmd, check=True)


if __name__ == '__main__':
    main()
