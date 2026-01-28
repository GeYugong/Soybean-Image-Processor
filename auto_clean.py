"""Auto background cleaning tool."""

import cv2
import numpy as np


def auto_clean_background(bg_path, output_path='images/bg_cleaned.png'):
    """
    Auto clean background:
    - Detect a single white sign (largest connected component)
    - Detect a single ruler on the left (vertical, dark)
    - Inpaint ONLY the white sign (single pass)
    - Fill ruler area with nearby background color
    """
    print(f"Loading background: {bg_path}")
    bg = cv2.imread(bg_path)

    if bg is None:
        raise FileNotFoundError(f"Background not found: {bg_path}")

    h, w = bg.shape[:2]
    print(f"Background size: {h}x{w}")

    # --- White sign detection (HSV threshold) ---
    hsv = cv2.cvtColor(bg, cv2.COLOR_BGR2HSV)
    white_lower = np.array([0, 0, 220])
    white_upper = np.array([180, 40, 255])
    white_mask_raw = cv2.inRange(hsv, white_lower, white_upper)

    # --- Ruler detection (single ruler on the left) ---
    gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    ruler_mask = np.zeros((h, w), dtype=np.uint8)

    gray_dark = cv2.inRange(gray, 10, 30)
    col_count = np.sum(gray_dark, axis=0)
    dark_frac = col_count / float(h)

    left_limit = int(w * 0.35)
    min_dark_frac = 0.8
    min_width = max(5, int(w * 0.005))
    max_width = int(w * 0.12)

    best = None  # (start, end, score)
    col = 0
    while col < left_limit:
        if dark_frac[col] >= min_dark_frac:
            s = col
            while col < left_limit and dark_frac[col] >= min_dark_frac:
                col += 1
            e = col - 1
            width = e - s + 1
            if min_width <= width <= max_width:
                score = dark_frac[s:e + 1].mean()
                if best is None or score > best[2]:
                    best = (s, e, score)
        else:
            col += 1

    ruler_col = -1
    ruler_width = 0
    if best is not None:
        ruler_col, end_col, score = best
        ruler_width = end_col - ruler_col + 1
        print(f"Ruler candidate: {ruler_col}-{end_col}, width={ruler_width}, dark={score:.2f}")
    else:
        print("No ruler candidate matched constraints")

    if ruler_col >= 0 and ruler_width > 0 and ruler_width < 300:
        ruler_mask[:, ruler_col:ruler_col + ruler_width] = 255
        expand = 190
        x1 = max(0, ruler_col - expand)
        x2 = min(w, ruler_col + ruler_width + expand)
        ruler_mask[:, x1:x2] = 255
        print(f"Ruler mask set: cols {x1}-{x2}")
    else:
        print(f"Ruler not found or invalid width: col={ruler_col}, width={ruler_width}")

    # --- White sign: largest connected component ---
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(white_mask_raw, connectivity=8)
    connected_mask = np.zeros((h, w), dtype=np.uint8)
    print(f"White components: {num_labels - 1}")

    best = None  # (area, x, y, w, h)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area > 500:
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w_comp = stats[i, cv2.CC_STAT_WIDTH]
            h_comp = stats[i, cv2.CC_STAT_HEIGHT]
            aspect = max(w_comp, h_comp) / (min(w_comp, h_comp) + 1)
            if aspect < 5:
                if best is None or area > best[0]:
                    best = (area, x, y, w_comp, h_comp)

    if best is not None:
        _, x, y, w_comp, h_comp = best
        expand = 10
        x1 = max(0, x - expand)
        y1 = max(0, y - expand)
        x2 = min(w, x + w_comp + expand)
        y2 = min(h, y + h_comp + expand)
        cv2.rectangle(connected_mask, (x1, y1), (x2, y2), 255, -1)

    # --- Merge & expand white sign mask ---
    white_mask = cv2.bitwise_or(white_mask_raw, connected_mask)
    white_expand_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    white_mask_expanded = cv2.dilate(white_mask, white_expand_kernel, iterations=2)

    # Debug mask includes sign + ruler
    mask_all = cv2.bitwise_or(white_mask_expanded, ruler_mask)
    mask = white_mask_expanded

    # Morphology to clean up mask edges (white sign only)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
    mask = cv2.dilate(mask, kernel_dilate, iterations=1)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)

    pixel_count = np.sum(mask > 0)
    print(f"Pixels to inpaint: {pixel_count} ({pixel_count / (h * w) * 100:.2f}%)")

    cv2.imwrite('images/mask_debug.png', mask_all)
    cv2.imwrite('images/mask_white_expanded.png', white_mask_expanded)

    # Single-pass inpaint (white sign only)
    result = bg.copy()
    print("Single-pass inpaint (Telea, radius=40)...")
    result = cv2.inpaint(result, mask, 40, cv2.INPAINT_TELEA)

    # Ruler: replace with a single background color sample (simple & complete)
    if np.any(ruler_mask > 0):
        ys, xs = np.where(ruler_mask > 0)
        x1, x2 = xs.min(), xs.max()
        ref_start = min(w - 1, x2 + 5)
        ref_end = min(w, x2 + 55)
        if ref_end <= ref_start:
            ref_start = max(0, w - 50)
            ref_end = w
        bg_ref = np.mean(bg[:, ref_start:ref_end], axis=(0, 1)).astype(np.uint8)
        result[ruler_mask > 0] = bg_ref

    cv2.imwrite(output_path, result)
    print(f"Done. Saved to: {output_path}")
    return result


def manual_clean_with_preview(bg_path, output_path='images/bg_cleaned.png'):
    """Manual preview mode: show detected mask, then single-pass inpaint."""
    print(f"Loading background: {bg_path}")
    bg = cv2.imread(bg_path)

    if bg is None:
        raise FileNotFoundError(f"Background not found: {bg_path}")

    h, w = bg.shape[:2]

    # White detection
    hsv = cv2.cvtColor(bg, cv2.COLOR_BGR2HSV)
    white_lower = np.array([0, 0, 220])
    white_upper = np.array([180, 40, 255])
    white_mask = cv2.inRange(hsv, white_lower, white_upper)

    # Gray detection (ruler-ish)
    gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    gray_mask = cv2.inRange(gray, 150, 200)

    # Edge detection (ruler-ish)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ruler_mask = np.zeros((h, w), dtype=np.uint8)

    for contour in contours:
        area = cv2.contourArea(contour)
        if 1000 < area < 50000:
            x, y, cw, ch = cv2.boundingRect(contour)
            aspect_ratio = max(cw, ch) / (min(cw, ch) + 1)
            if aspect_ratio > 10:
                margin = 200
                is_near_edge = (x < margin or y < margin or x + cw > w - margin or y + ch > h - margin)
                if is_near_edge:
                    expand = 5
                    x1 = max(0, x - expand)
                    y1 = max(0, y - expand)
                    x2 = min(w, x + cw + expand)
                    y2 = min(h, y + ch + expand)
                    cv2.rectangle(ruler_mask, (x1, y1), (x2, y2), 255, -1)

    # Connected components for white sign
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(white_mask, connectivity=8)
    connected_mask = np.zeros((h, w), dtype=np.uint8)

    best = None
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area > 500:
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w_comp = stats[i, cv2.CC_STAT_WIDTH]
            h_comp = stats[i, cv2.CC_STAT_HEIGHT]
            aspect = max(w_comp, h_comp) / (min(w_comp, h_comp) + 1)
            if aspect < 5:
                if best is None or area > best[0]:
                    best = (area, x, y, w_comp, h_comp)

    if best is not None:
        _, x, y, w_comp, h_comp = best
        expand = 10
        x1 = max(0, x - expand)
        y1 = max(0, y - expand)
        x2 = min(w, x + w_comp + expand)
        y2 = min(h, y + h_comp + expand)
        cv2.rectangle(connected_mask, (x1, y1), (x2, y2), 255, -1)

    # Merge masks
    mask = cv2.bitwise_or(white_mask, ruler_mask)
    mask = cv2.bitwise_or(mask, gray_mask)
    mask = cv2.bitwise_or(mask, connected_mask)

    # Morphology
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
    mask = cv2.dilate(mask, kernel_dilate, iterations=1)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)

    # Preview
    print("\nPreview detected regions. Press any key to continue...")
    disp_scale = 900.0 / h if h > 900 else 1.0
    disp_h, disp_w = int(h * disp_scale), int(w * disp_scale)

    mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    mask_color[mask > 0] = [0, 0, 255]

    combined = cv2.addWeighted(bg, 0.7, mask_color, 0.3, 0)
    combined_disp = cv2.resize(combined, (disp_w, disp_h))

    cv2.imshow("Detected regions to remove (red)", combined_disp)
    cv2.waitKey(0)
    cv2.destroyWindow("Detected regions to remove (red)")

    # Single-pass inpaint
    print("Single-pass inpaint (Telea)...")
    result = cv2.inpaint(bg, mask, 15, cv2.INPAINT_TELEA)

    cv2.imwrite(output_path, result)
    print(f"Done. Saved to: {output_path}")
    return result


if __name__ == "__main__":
    import sys

    bg_path = 'images/bg.png'
    output_path = 'images/bg_cleaned.png'

    if len(sys.argv) > 1:
        if sys.argv[1] == '--manual':
            manual_clean_with_preview(bg_path, output_path)
        else:
            auto_clean_background(bg_path, output_path)
    else:
        auto_clean_background(bg_path, output_path)
