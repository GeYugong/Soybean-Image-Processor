import argparse
import os

import cv2
import numpy as np

# Default paths
BG_PATH = 'images/bg.png'
POD_PATH = 'images/pod.jpg'
SEED_PATH = 'images/seed.jpg'
OUTPUT_PATH = 'result_final_v4.jpg'
BG_CLEANED_PATH = 'images/bg_cleaned.png'


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
                        # cancel current drawing
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

        # Optional crop after finishing all background edits
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
            if key in (ord('s'), ord('S'), 27):  # skip or exit
                crop_x = None
                break
            if crop_x is not None:
                # Confirm crop after click
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

    def match_background(self, roi):
        roi_bg_ref = np.mean(roi[0:20, 0:20], axis=(0, 1))
        target_ref = self.color_ref if self.color_ref is not None else self.bg_black_ref
        diff = target_ref - roi_bg_ref
        res = roi.astype(np.float32) + diff
        return np.clip(res, 0, 255).astype(np.uint8)

    def select_color_reference(self):
        print("请在背景图中框选一块“植株颜色”区域（SPACE/ENTER确认，R 重做，S 跳过，ESC 退出）")
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
                preview[y1:y2, x1:x2] = inset_resized[iy1:iy2, ix1:ix2]
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
                self.bg[y1:y2, x1:x2] = inset_final[iy1:iy2, ix1:ix2]
                print("放置已确认")

    def save(self, output_path=OUTPUT_PATH):
        cv2.imwrite(output_path, self.bg)
        print(f"完成: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bg", help="背景图像路径")
    parser.add_argument("--pod", help="豆荚图像路径")
    parser.add_argument("--seed", help="种子图像路径")
    parser.add_argument("--out", help="输出图像路径")
    parser.add_argument("--cleaned", help="使用已清理的背景路径 (跳过提示)")
    parser.add_argument("--clean-bg", action="store_true", help="强制手动清理背景")
    parser.add_argument("--cleaned-out", help="将清理后的背景保存到此路径")
    parser.add_argument("--skip-clean", action="store_true", help="跳过手动清理背景提示")
    args = parser.parse_args()

    batch_mode = any([args.bg, args.pod, args.seed, args.out, args.cleaned, args.clean_bg, args.cleaned_out, args.skip_clean])

    if batch_mode:
        bg_path = args.cleaned or args.bg or BG_PATH
        pod_path = args.pod or POD_PATH
        seed_path = args.seed or SEED_PATH
        output_path = args.out or OUTPUT_PATH

        app = UltimatePaster(bg_path)
        if args.clean_bg:
            app.clean_background(args.cleaned_out)
        app.select_color_reference()
        print("\n>>> 第一步: 选择豆荚")
        roi1 = app.get_roi_zoomed(pod_path, "Select Pod")
        if roi1 is not None:
            roi1 = app.match_background(roi1)
            app.interactive_place(roi1)

        print("\n>>> 第二步: 选择种子")
        roi2 = app.get_roi_zoomed(seed_path, "Select Seed")
        if roi2 is not None:
            roi2 = app.match_background(roi2)
            app.interactive_place(roi2)

        app.save(output_path)
        raise SystemExit(0)

    # Interactive default flow
    use_cleaned = False
    if os.path.exists(BG_CLEANED_PATH):
        print(f"找到已清理的背景: {BG_CLEANED_PATH}")
        response = input("使用已清理的背景? (y/n, 默认y): ").strip().lower()
        use_cleaned = response != 'n'

    if use_cleaned:
        print(f"使用已清理的背景: {BG_CLEANED_PATH}")
        app = UltimatePaster(BG_CLEANED_PATH)
    else:
        print(f"使用原始背景: {BG_PATH}")
        app = UltimatePaster(BG_PATH)
        if args.clean_bg:
            app.clean_background(args.cleaned_out)
        elif not args.skip_clean:
            response = input("现在清理背景吗? (y/n, 默认y): ").strip().lower()
            if response != 'n':
                print("\n>>> 第零步: 清理背景")
                app.clean_background(args.cleaned_out)

    app.select_color_reference()
    print("\n>>> 第一步: 选择豆荚")
    roi1 = app.get_roi_zoomed(POD_PATH, "Select Pod")
    if roi1 is not None:
        roi1 = app.match_background(roi1)
        app.interactive_place(roi1)

    print("\n>>> 第二步: 选择种子")
    roi2 = app.get_roi_zoomed(SEED_PATH, "Select Seed")
    if roi2 is not None:
        roi2 = app.match_background(roi2)
        app.interactive_place(roi2)

    app.save(OUTPUT_PATH)
