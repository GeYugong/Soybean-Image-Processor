import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


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
    parser.add_argument('--force', action='store_true', help='覆盖现有输出')
    parser.add_argument('--start-id', help='从此4位数ID开始 (含), 例如 0010')
    parser.add_argument('--only-id', help='仅处理一个4位数ID, 例如 0012')
    parser.add_argument('--ids', help='以逗号分隔的ID列表, 例如 0003,0007,0011')
    args = parser.parse_args()

    bg_map = build_map(args.bg_dir)
    pod_map = build_map(args.pod_dir)
    seed_map = build_map(args.seed_dir)

    ids = sorted(set(bg_map) & set(pod_map) & set(seed_map))
    if not ids:
        print('未找到匹配的图像组。')
        return

    if args.only_id:
        ids = [args.only_id]
    elif args.ids:
        wanted = {i.strip() for i in args.ids.split(',') if i.strip()}
        ids = [i for i in ids if i in wanted]

    if args.start_id:
        ids = [i for i in ids if i >= args.start_id]

    out_dir = Path(args.out_dir)
    out_bg = out_dir / 'bg_cleaned'
    out_final = out_dir / 'final'
    out_bg.mkdir(parents=True, exist_ok=True)
    out_final.mkdir(parents=True, exist_ok=True)

    print(f'找到 {len(ids)} 个图像组。')

    start_input = input(f'从第几组开始? (1-{len(ids)}, 默认1): ').strip()
    try:
        start_idx = int(start_input) if start_input else 1
    except ValueError:
        start_idx = 1
    if start_idx < 1:
        start_idx = 1
    if start_idx > len(ids):
        print('起始索引超过组数。没有要处理的内容。')
        return

    for idx, img_id in enumerate(ids, 1):
        if idx < start_idx:
            continue
        bg_path = bg_map[img_id]
        pod_path = pod_map[img_id]
        seed_path = seed_map[img_id]

        cleaned_path = out_bg / f'{img_id}_bg_cleaned.jpg'
        final_path = out_final / f'{img_id}_final.jpg'

        if final_path.exists() and not args.force:
            resp = input(f'[{idx}/{len(ids)}] {img_id} 已处理。重新处理并覆盖? (y/N): ').strip().lower()
            if resp != 'y':
                print(f'[{idx}/{len(ids)}] 跳过 {img_id}')
                continue

        print(f'[{idx}/{len(ids)}] 正在处理 {img_id}')
        cmd = [
            sys.executable, 'main.py',
            '--bg', bg_path,
            '--pod', pod_path,
            '--seed', seed_path,
            '--out', str(final_path),
            '--clean-bg',
            '--cleaned-out', str(cleaned_path),
        ]
        subprocess.run(cmd, check=True)


if __name__ == '__main__':
    main()
