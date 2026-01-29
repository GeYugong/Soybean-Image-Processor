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

    def clean_background(self):
        print(">>> Clean background: draw rectangles to remove")
        print("1) Drag rectangles over objects to remove")
        print("2) Press SPACE to confirm, ESC to cancel")

        bg_work = self.bg.copy()
        mask = np.zeros(bg_work.shape[:2], dtype=np.uint8)

        screen_h = 900.0
        bg_h, bg_w = bg_work.shape[:2]
        disp_scale = screen_h / bg_h if bg_h > screen_h else 1.0

        rects = []
        drawing = False
        rect_start = None

        def mouse_callback(event, x, y, flags, param):
            nonlocal drawing, rect_start, rects
            real_x = int(x / disp_scale)
            real_y = int(y / disp_scale)

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
                    cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
                    print(f"Marked region: ({x1}, {y1}) -> ({x2}, {y2})")

        win_name = "Clean Background - Draw rectangles | SPACE confirm | ESC cancel"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(win_name, mouse_callback)

        while True:
            preview = bg_work.copy()
            for x1, y1, x2, y2 in rects:
                cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(preview, 'Remove', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            disp_h, disp_w = int(bg_h * disp_scale), int(bg_w * disp_scale)
            preview_disp = cv2.resize(preview, (disp_w, disp_h))
            cv2.imshow(win_name, preview_disp)

            key = cv2.waitKey(10) & 0xFF
            if key == 32:  # SPACE
                break
            if key == 27:  # ESC
                cv2.destroyWindow(win_name)
                print("Canceled background cleaning")
                return False

        cv2.destroyWindow(win_name)

        if len(rects) == 0:
            print("No regions marked, skip cleaning")
            return False

        print(f"Inpainting {len(rects)} regions...")
        self.bg = cv2.inpaint(bg_work, mask, 5, cv2.INPAINT_TELEA)
        cv2.imwrite(BG_CLEANED_PATH, self.bg)
        print(f"Cleaned background saved to: {BG_CLEANED_PATH}")
        self.bg_black_ref = np.mean(self.bg[0:50, 0:50], axis=(0, 1))
        return True

    def get_roi_zoomed(self, img_path, win_name="Select Region"):
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

        print(f"Select ROI in [{win_name}] then press SPACE/ENTER")
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        roi_rect = cv2.selectROI(win_name, src_disp, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow(win_name)

        x_s, y_s, w_s, h_s = roi_rect
        if w_s == 0 or h_s == 0:
            return None

        real_x, real_y = int(x_s / scale), int(y_s / scale)
        real_w, real_h = int(w_s / scale), int(h_s / scale)
        return src[real_y:real_y + real_h, real_x:real_x + real_w]

    def match_background(self, roi):
        roi_bg_ref = np.mean(roi[0:20, 0:20], axis=(0, 1))
        diff = self.bg_black_ref - roi_bg_ref
        res = roi.astype(np.float32) + diff
        return np.clip(res, 0, 255).astype(np.uint8)

    def interactive_place(self, inset_img):
        current_scale = (self.bg.shape[1] * 0.35) / inset_img.shape[1]
        pos = [0, 0]
        placed = False

        win_name = "Mouse Wheel to Resize | Click to Confirm"
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
                print(f"Current scale: {current_scale:.2f}")
            elif event == cv2.EVENT_LBUTTONDOWN:
                placed = True

        cv2.setMouseCallback(win_name, mouse_callback)

        print(">>> Adjust placement")
        print("  [Mouse move] change position")
        print("  [Mouse wheel] zoom")
        print("  [Left click] confirm")

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
            if key == 27:
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
                print("Placement confirmed")

    def save(self, output_path=OUTPUT_PATH):
        cv2.imwrite(output_path, self.bg)
        print(f"Done: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bg", help="Background image path")
    parser.add_argument("--pod", help="Pod image path")
    parser.add_argument("--seed", help="Seed image path")
    parser.add_argument("--out", help="Output image path")
    parser.add_argument("--cleaned", help="Use cleaned background path (skip prompts)")
    parser.add_argument("--skip-clean", action="store_true", help="Skip manual background cleaning prompt")
    args = parser.parse_args()

    batch_mode = any([args.bg, args.pod, args.seed, args.out, args.cleaned, args.skip_clean])

    if batch_mode:
        bg_path = args.cleaned or args.bg or BG_PATH
        pod_path = args.pod or POD_PATH
        seed_path = args.seed or SEED_PATH
        output_path = args.out or OUTPUT_PATH

        app = UltimatePaster(bg_path)
        print("\n>>> Step 1: Select POD")
        roi1 = app.get_roi_zoomed(pod_path, "Select POD")
        if roi1 is not None:
            roi1 = app.match_background(roi1)
            app.interactive_place(roi1)

        print("\n>>> Step 2: Select SEED")
        roi2 = app.get_roi_zoomed(seed_path, "Select SEED")
        if roi2 is not None:
            roi2 = app.match_background(roi2)
            app.interactive_place(roi2)

        app.save(output_path)
        raise SystemExit(0)

    # Interactive default flow
    use_cleaned = False
    if os.path.exists(BG_CLEANED_PATH):
        print(f"Found cleaned background: {BG_CLEANED_PATH}")
        response = input("Use cleaned background? (y/n, default y): ").strip().lower()
        use_cleaned = response != 'n'

    if use_cleaned:
        print(f"Using cleaned background: {BG_CLEANED_PATH}")
        app = UltimatePaster(BG_CLEANED_PATH)
    else:
        print(f"Using original background: {BG_PATH}")
        app = UltimatePaster(BG_PATH)
        if not args.skip_clean:
            response = input("Clean background now? (y/n, default y): ").strip().lower()
            if response != 'n':
                print("\n>>> Step 0: Clean background")
                app.clean_background()

    print("\n>>> Step 1: Select POD")
    roi1 = app.get_roi_zoomed(POD_PATH, "Select POD")
    if roi1 is not None:
        roi1 = app.match_background(roi1)
        app.interactive_place(roi1)

    print("\n>>> Step 2: Select SEED")
    roi2 = app.get_roi_zoomed(SEED_PATH, "Select SEED")
    if roi2 is not None:
        roi2 = app.match_background(roi2)
        app.interactive_place(roi2)

    app.save(OUTPUT_PATH)
