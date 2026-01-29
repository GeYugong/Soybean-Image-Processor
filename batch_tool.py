"""
大豆图像处理工具 - 单文件版本
将 main.py 和 batch_process.py 合并，确保打包后正常工作
"""

import argparse
import os
import re
import sys
from pathlib import Path

import cv2
import numpy as np

# Default paths
BG_PATH = 'images/bg.png'
POD_PATH = 'images/pod.jpg'
SEED_PATH = 'images/seed.jpg'
OUTPUT_PATH = 'result_final_v4.jpg'
BG_CLEANED_PATH = 'images/bg_cleaned.png'


# ==========================================
# UltimatePaster 类 (来自 main.py)
# ==========================================
class UltimatePaster:
    def __init__(self, bg_path):
        self.bg = cv2.imread(bg_path)
        if self.bg is None:
            raise FileNotFoundError(f"Background not found: {bg_path}")
        self.bg_black_ref = np.mean(self.bg[0:50, 0:50], axis=(0, 1))
        self.color_ref = None

    def clean_background(self, output_path=None):
        print(">>> 清理背景：绘制矩形来移除对象")
        print("1) 在要移除的对象上拖动矩形")
        print("2) 按空格键确认，按ESC取消")

        pass_count = 0
        skip_more = False
        while True:
            bg_work = self.bg.copy()
            mask = np.zeros(bg_work.shape[:2], dtype=np.uint8)

            screen_h = 900.0
            bg_h, bg_w = bg_work.shape[:2]
            disp_scale = screen_h / bg_h if bg_h > screen_h else 1.0

            rects = []
            drawing = False
            rect_start = None
            current_pos = None
            cancel_current = False

            def rebuild_mask():
                mask[:] = 0
                for rx1, ry1, rx2, ry2 in rects:
                    cv2.rectangle(mask, (rx1, ry1), (rx2, ry2), 255, -1)

            def mouse_callback(event, x, y, flags, param):
                nonlocal drawing, rect_start, rects, current_pos, cancel_current
                real_x = int(x / disp_scale)
                real_y = int(y / disp_scale)

                if event == cv2.EVENT_MOUSEMOVE:
                    current_pos = (real_x, real_y)
                if event == cv2.EVENT_LBUTTONDOWN:
                    drawing = True
                    rect_start = (real_x, real_y)
                elif event == cv2.EVENT_LBUTTONUP:
                    if drawing and rect_start:
                        drawing = False
                        x1, y1 = rect_start
                        x2, y2 = real_x, real_y
                        x1, x2 = min(x1, x2), max(x1, x2)
                        y1, y2 = min(y1, y2), max(y1, y2)
                        rects.append((x1, y1, x2, y2))
                        rebuild_mask()
                        print(f"标记区域: ({x1}, {y1}) -> ({x2}, {y2})")
                elif event == cv2.EVENT_RBUTTONDOWN:
                    if drawing:
                        drawing = False
                        rect_start = None
                        current_pos = None
                        cancel_current = True
                        print("已取消当前框选")
                    elif rects:
                        rects.pop()
                        rebuild_mask()
                        print("已撤销上一个框选")

            win_name = "Background Cleanup"
            cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
            cv2.setMouseCallback(win_name, mouse_callback)

            while True:
                preview = bg_work.copy()
                if rects or (drawing and rect_start and current_pos):
                    overlay = preview.copy()
                    for x1, y1, x2, y2 in rects:
                        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 255), -1)
                        cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 255), 3)
                        cv2.putText(preview, '移除', (x1, max(0, y1 - 10)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    if drawing and rect_start and current_pos:
                        x1, y1 = rect_start
                        x2, y2 = current_pos
                        x1, x2 = min(x1, x2), max(x1, x2)
                        y1, y2 = min(y1, y2), max(y1, y2)
                        cv2.rectangle(preview, (x1, y1), (x2, y2), (255, 255, 0), 2)
                        cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 255, 0), -1)
                    preview = cv2.addWeighted(overlay, 0.35, preview, 0.65, 0)

                disp_h, disp_w = int(bg_h * disp_scale), int(bg_w * disp_scale)
                preview_disp = cv2.resize(preview, (disp_w, disp_h))
                cv2.imshow(win_name, preview_disp)

                key = cv2.waitKey(10) & 0xFF
                if key in (ord('r'), ord('R')):
                    rects.clear()
                    mask[:] = 0
                    drawing = False
                    rect_start = None
                    current_pos = None
                    print("已重做当前步骤")
                    continue
                if key in (ord('s'), ord('S')):
                    if pass_count == 0 and len(rects) == 0:
                        cv2.destroyWindow(win_name)
                        print("已跳过背景清理")
                        return False
                    skip_more = True
                    break
                if key == 32:  # SPACE
                    break
                if key == 27:  # ESC
                    cv2.destroyWindow(win_name)
                    print("已取消背景清理")
                    return False

            cv2.destroyWindow(win_name)

            if len(rects) == 0:
                if pass_count == 0:
                    print("未标记任何区域，跳过清理")
                    return False
                break

            print(f"修复 {len(rects)} 个区域... (第 {pass_count + 1} 次)")
            self.bg = cv2.inpaint(bg_work, mask, 5, cv2.INPAINT_TELEA)
            pass_count += 1
            if skip_more:
                break

        # Optional crop
        crop_x = None
        current_x = None

        def crop_mouse_callback(event, x, y, flags, param):
            nonlocal crop_x, current_x
            real_x = int(x / disp_scale)
            if event == cv2.EVENT_MOUSEMOVE:
                current_x = real_x
            elif event == cv2.EVENT_LBUTTONDOWN:
                crop_x = real_x

        crop_win = "Crop Line"
        cv2.namedWindow(crop_win, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(crop_win, crop_mouse_callback)

        while True:
            preview = self.bg.copy()
            x_line = crop_x if crop_x is not None else current_x
            if x_line is not None:
                cv2.line(preview, (x_line, 0), (x_line, preview.shape[0]), (0, 255, 255), 2)
                cv2.putText(preview, '从这里开始裁剪 ->', (x_line + 10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            disp_h, disp_w = int(self.bg.shape[0] * disp_scale), int(self.bg.shape[1] * disp_scale)
            preview_disp = cv2.resize(preview, (disp_w, disp_h))
            cv2.imshow(crop_win, preview_disp)

            key = cv2.waitKey(10) & 0xFF
            if key in (ord('r'), ord('R')):
                crop_x = None
                current_x = None
                print("已重做当前步骤")
                continue
            if key in (ord('s'), ord('S'), 27):
                crop_x = None
                break
            if crop_x is not None:
                break

        cv2.destroyWindow(crop_win)
        if crop_x is not None and 0 < crop_x < self.bg.shape[1]:
            self.bg = self.bg[:, crop_x:]
        save_path = output_path or BG_CLEANED_PATH
        cv2.imwrite(save_path, self.bg)
        print(f"清理后的背景已保存到: {save_path}")
        self.bg_black_ref = np.mean(self.bg[0:50, 0:50], axis=(0, 1))
        return True

    def get_roi_zoomed(self, img_path, win_name="选择区域"):
        src = cv2.imread(img_path)
        if src is None:
            raise FileNotFoundError(f"Image not found: {img_path}")

        h, w = src.shape[:2]
        target_h = 900.0
        scale = target_h / h if h > target_h else 1.0

        if scale < 1.0:
            src_disp = cv2.resize(src, (int(w * scale), int(target_h)))
        else:
            src_disp = src.copy()

        print(f"在 [{win_name}] 中框选区域，SPACE/ENTER 确认，R 重做，S 跳过，ESC 退出，右键撤销")
        roi_rect = self._select_roi_interactive(src_disp, win_name)
        if roi_rect is None:
            return None

        x_s, y_s, w_s, h_s = roi_rect
        real_x, real_y = int(x_s / scale), int(y_s / scale)
        real_w, real_h = int(w_s / scale), int(h_s / scale)
        return src[real_y:real_y + real_h, real_x:real_x + real_w]

    def auto_mask_object(self, roi, keep_top_k=1):
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            clean_mask = np.zeros_like(mask)
            for c in contours[:keep_top_k]:
                cv2.drawContours(clean_mask, [c], -1, 255, -1)
            mask = clean_mask

        mask = cv2.GaussianBlur(mask, (3, 3), 0)
        b, g, r = cv2.split(roi)
        rgba = cv2.merge([b, g, r, mask])
        return rgba

    def match_background(self, roi):
        roi_bg_ref = np.mean(roi[0:20, 0:20], axis=(0, 1))
        target_ref = self.color_ref if self.color_ref is not None else self.bg_black_ref
        diff = target_ref - roi_bg_ref
        res = roi.astype(np.float32) + diff
        return np.clip(res, 0, 255).astype(np.uint8)

    def select_color_reference(self):
        print("请在背景图中框选一块植株颜色区域（SPACE/ENTER确认，R 重做，S 跳过，ESC 退出）")
        src = self.bg.copy()
        h, w = src.shape[:2]
        target_h = 900.0
        scale = target_h / h if h > target_h else 1.0

        if scale < 1.0:
            src_disp = cv2.resize(src, (int(w * scale), int(target_h)))
        else:
            src_disp = src.copy()

        win_name = "Select Color Reference"
        roi_rect = self._select_roi_interactive(src_disp, win_name)
        if roi_rect is None:
            print("未选择参考区域，将使用默认参考色。")
            return False

        x_s, y_s, w_s, h_s = roi_rect
        if w_s == 0 or h_s == 0:
            print("未选择参考区域，将使用默认参考色。")
            return False

        real_x, real_y = int(x_s / scale), int(y_s / scale)
        real_w, real_h = int(w_s / scale), int(h_s / scale)
        ref_patch = src[real_y:real_y + real_h, real_x:real_x + real_w]
        if ref_patch.size == 0:
            print("参考区域无效，将使用默认参考色。")
            return False

        self.color_ref = np.mean(ref_patch, axis=(0, 1))
        print("已设置植株颜色参考。")
        return True

    def _select_roi_interactive(self, img_disp, win_name):
        rect_start = None
        current_pos = None
        drawing = False
        rect = None

        def mouse_callback(event, x, y, flags, param):
            nonlocal rect_start, current_pos, drawing, rect
            if event == cv2.EVENT_MOUSEMOVE:
                current_pos = (x, y)
            elif event == cv2.EVENT_LBUTTONDOWN:
                drawing = True
                rect_start = (x, y)
            elif event == cv2.EVENT_LBUTTONUP:
                if drawing and rect_start:
                    drawing = False
                    x1, y1 = rect_start
                    x2, y2 = x, y
                    x1, x2 = min(x1, x2), max(x1, x2)
                    y1, y2 = min(y1, y2), max(y1, y2)
                    rect = (x1, y1, x2 - x1, y2 - y1)
            elif event == cv2.EVENT_RBUTTONDOWN:
                if drawing:
                    drawing = False
                    rect_start = None
                    current_pos = None
                    print("已取消当前框选")
                elif rect is not None:
                    rect = None
                    print("已撤销上一个框选")

        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(win_name, mouse_callback)

        while True:
            preview = img_disp.copy()
            overlay = preview.copy()

            if rect is not None:
                x1, y1, w1, h1 = rect
                x2, y2 = x1 + w1, y1 + h1
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 255), -1)
                cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 255), 2)
                preview = cv2.addWeighted(overlay, 0.35, preview, 0.65, 0)

            if drawing and rect_start and current_pos:
                x1, y1 = rect_start
                x2, y2 = current_pos
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                cv2.rectangle(preview, (x1, y1), (x2, y2), (255, 255, 0), 2)

            cv2.imshow(win_name, preview)
            key = cv2.waitKey(10) & 0xFF
            if key in (ord('r'), ord('R')):
                rect = None
                rect_start = None
                drawing = False
                print("已重做当前步骤")
                continue
            if key in (ord('s'), ord('S')):
                rect = None
                break
            if key in (32, 13):  # SPACE or ENTER
                break
            if key == 27:  # ESC
                rect = None
                break

        cv2.destroyWindow(win_name)
        return rect

    def interactive_place(self, inset_img):
        current_scale = (self.bg.shape[1] * 0.35) / inset_img.shape[1]
        initial_scale = current_scale
        pos = [0, 0]
        placed = False

        win_name = "Adjust Position & Size"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)

        screen_h = 900.0
        bg_h, bg_w = self.bg.shape[:2]
        disp_scale = screen_h / bg_h if bg_h > screen_h else 1.0

        def mouse_callback(event, x, y, flags, param):
            nonlocal placed, current_scale
            real_x = int(x / disp_scale)
            real_y = int(y / disp_scale)

            if event == cv2.EVENT_MOUSEMOVE:
                pos[0], pos[1] = real_x, real_y
            elif event == cv2.EVENT_MOUSEWHEEL:
                if flags > 0:
                    current_scale *= 1.05
                else:
                    current_scale *= 0.95
                print(f"当前缩放比例: {current_scale:.2f}")
            elif event == cv2.EVENT_LBUTTONDOWN:
                placed = True

        cv2.setMouseCallback(win_name, mouse_callback)

        print(">>> 调整放置位置")
        print("  [鼠标移动] 改变位置")
        print("  [鼠标滚轮] 缩放")
        print("  [左键点击] 确认")

        while not placed:
            h_i, w_i = inset_img.shape[:2]
            new_w, new_h = int(w_i * current_scale), int(h_i * current_scale)
            inset_resized = cv2.resize(inset_img, (new_w, new_h))

            preview = self.bg.copy()
            top_x = pos[0] - new_w // 2
            top_y = pos[1] - new_h // 2

            y1, y2 = max(0, top_y), min(bg_h, top_y + new_h)
            x1, x2 = max(0, top_x), min(bg_w, top_x + new_w)
            iy1, iy2 = y1 - top_y, y2 - top_y
            ix1, ix2 = x1 - top_x, x2 - top_x

            if y2 > y1 and x2 > x1:
                region = preview[y1:y2, x1:x2]
                ins = inset_resized[iy1:iy2, ix1:ix2]
                if ins.shape[2] == 4:
                    alpha = ins[:, :, 3] / 255.0
                    alpha = np.stack([alpha] * 3, axis=2)
                    fg = ins[:, :, :3]
                    blended = (fg * alpha + region * (1 - alpha)).astype(np.uint8)
                    region[:] = blended
                else:
                    region[:] = ins
                preview[y1:y2, x1:x2] = region
                cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 2)

            disp_h, disp_w = int(bg_h * disp_scale), int(bg_w * disp_scale)
            cv2.imshow(win_name, cv2.resize(preview, (disp_w, disp_h)))

            key = cv2.waitKey(10) & 0xFF
            if key in (ord('r'), ord('R')):
                current_scale = initial_scale
                pos[0], pos[1] = 0, 0
                print("已重做当前步骤")
                continue
            if key in (ord('s'), ord('S'), 27):
                placed = False
                break

        cv2.destroyWindow(win_name)

        if placed:
            h_i, w_i = inset_img.shape[:2]
            new_w, new_h = int(w_i * current_scale), int(h_i * current_scale)
            inset_final = cv2.resize(inset_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

            top_x = pos[0] - new_w // 2
            top_y = pos[1] - new_h // 2

            y1, y2 = max(0, top_y), min(bg_h, top_y + new_h)
            x1, x2 = max(0, top_x), min(bg_w, top_x + new_w)
            iy1, iy2 = y1 - top_y, y2 - top_y
            ix1, ix2 = x1 - top_x, x2 - top_x

            if y2 > y1 and x2 > x1:
                region = self.bg[y1:y2, x1:x2]
                ins = inset_final[iy1:iy2, ix1:ix2]
                if ins.shape[2] == 4:
                    alpha = ins[:, :, 3] / 255.0
                    alpha = np.stack([alpha] * 3, axis=2)
                    fg = ins[:, :, :3]
                    blended = (fg * alpha + region * (1 - alpha)).astype(np.uint8)
                    region[:] = blended
                else:
                    region[:] = ins
                self.bg[y1:y2, x1:x2] = region
                print("放置已确认")

    def save(self, output_path=OUTPUT_PATH):
        cv2.imwrite(output_path, self.bg)
        print(f"完成: {output_path}")


# ==========================================
# 单组处理函数
# ==========================================
def process_single(bg_path, pod_path, seed_path, output_path, cleaned_out=None):
    """处理单组图片"""
    app = UltimatePaster(bg_path)
    app.clean_background(cleaned_out)
    app.select_color_reference()

    print("\n>>> 第一步: 选择豆荚")
    roi1 = app.get_roi_zoomed(pod_path, "Select Pod")
    if roi1 is not None:
        roi1 = app.match_background(roi1)
        roi1 = app.auto_mask_object(roi1)
        app.interactive_place(roi1)

    print("\n>>> 第二步: 选择种子")
    roi2 = app.get_roi_zoomed(seed_path, "Select Seed")
    if roi2 is not None:
        roi2 = app.match_background(roi2)
        roi2 = app.auto_mask_object(roi2, keep_top_k=2)
        app.interactive_place(roi2)

    app.save(output_path)


# ==========================================
# 批处理函数 (来自 batch_process.py)
# ==========================================
def extract_id(filename):
    nums = re.findall(r'(\d{4})', filename)
    return nums[-1] if nums else None


def build_map(folder):
    mapping = {}
    path_obj = Path(folder)
    if not path_obj.exists():
        print(f"警告: 文件夹不存在 - {folder}")
        return {}
    
    for path in path_obj.glob('*'):
        if path.is_file():
            img_id = extract_id(path.name)
            if img_id:
                mapping[img_id] = str(path)
    return mapping


def batch_main():
    """批处理主函数"""
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

    print("=" * 50)
    print("  大豆图像处理工具 v2.0")
    print("=" * 50)
    print()
    
    print("正在扫描图片目录...")
    bg_map = build_map(args.bg_dir)
    pod_map = build_map(args.pod_dir)
    seed_map = build_map(args.seed_dir)

    print(f"  bg/  : {len(bg_map)} 张图片")
    print(f"  pod/ : {len(pod_map)} 张图片")
    print(f"  seed/: {len(seed_map)} 张图片")
    print()

    ids = sorted(set(bg_map) & set(pod_map) & set(seed_map))
    if not ids:
        print('错误：未找到匹配的图像组！')
        print('请检查 images/ 下的 bg, pod, seed 文件夹是否都有同号图片。')
        print()
        print('文件命名规则：')
        print('  bg/   GY2025HHN-0001.jpg  (包含4位数字)')
        print('  pod/  GY2025-0001.jpg     (相同的4位数字)')
        print('  seed/ GY-0001.jpg         (相同的4位数字)')
        input("\n按回车键退出...")
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

    print(f'找到 {len(ids)} 个匹配的图像组。')
    print()

    start_input = input(f'从第几组开始? (1-{len(ids)}, 默认1): ').strip()
    try:
        start_idx = int(start_input) if start_input else 1
    except ValueError:
        start_idx = 1
    if start_idx < 1:
        start_idx = 1
    if start_idx > len(ids):
        print('起始索引超过组数。没有要处理的内容。')
        input("\n按回车键退出...")
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
            print(f'[{idx}/{len(ids)}] {img_id} 已存在，跳过。')
            continue

        print()
        print("=" * 50)
        print(f'[{idx}/{len(ids)}] 正在处理 {img_id}')
        print("=" * 50)
        
        try:
            process_single(bg_path, pod_path, seed_path, str(final_path), str(cleaned_path))
        except Exception as e:
            print(f"处理 {img_id} 时发生错误: {e}")
            continue

    print()
    print("=" * 50)
    print("所有任务已完成！")
    print(f"输出目录: {out_dir.absolute()}")
    print("=" * 50)
    print()
    input("按回车键退出...")


# ==========================================
# 主入口
# ==========================================
if __name__ == '__main__':
    batch_main()
