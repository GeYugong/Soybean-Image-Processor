"""
背景自动清理脚本 - 增强版
支持自动检测和彻底移除白色对象（如白色牌子及其附属物）和金属尺子
"""

import cv2
import numpy as np

def auto_clean_background(bg_path, output_path='images/bg_cleaned.png'):
    """
    自动清理背景图：检测并移除白色对象和金属对象
    改进版：更激进的检测策略，确保完全移除标尺和白色牌子及其附属物
    """
    print(f"正在加载背景图: {bg_path}")
    bg = cv2.imread(bg_path)
    
    if bg is None:
        raise FileNotFoundError(f"找不到背景图: {bg_path}")
    
    h, w = bg.shape[:2]
    print(f"背景图大小: {h}x{w}")
    
    # 创建掩码用于标记需要移除的区域
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # ===== 方法1: 精确的白色区域检测 =====
    hsv = cv2.cvtColor(bg, cv2.COLOR_BGR2HSV)
    
    # 只检测非常白的区域（纯白色牌子）
    white_lower = np.array([0, 0, 220])  # 高亮度阈值
    white_upper = np.array([180, 40, 255])  # 低饱和度（接近纯白）
    white_mask_raw = cv2.inRange(hsv, white_lower, white_upper)
    
    # ===== 方法2: 标尺检测 =====
    # 策略：从左边扫描，找到第一个主要的暗灰色竖直条纹
    gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    
    ruler_mask = np.zeros((h, w), dtype=np.uint8)

    # Ruler detection (single ruler on the left, vertical) 
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
                score = dark_frac[s:e+1].mean()
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
        # 添加到掩码
        ruler_mask[:, ruler_col:ruler_col + ruler_width] = 255
        
        # 大幅膨胀确保完全覆盖标尺及其阴影
        expand = 80  # 大幅增加膨胀范围
        x1 = max(0, ruler_col - expand)
        x2 = min(w, ruler_col + ruler_width + expand)
        ruler_mask[:, x1:x2] = 255
        
        print(f"标尺掩码已设置：列 {x1}-{x2}")
    else:
        print(f"标尺未找到或宽度不合理：col={ruler_col}, width={ruler_width}")
    
    # ===== 方法3: 连通域分析 - 找到大块的白色区域（牌子） =====
    # 对白色掩码进行连通域分析
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(white_mask_raw, connectivity=8)
    
    connected_mask = np.zeros((h, w), dtype=np.uint8)
    print(f"找到 {num_labels-1} 个白色连通域")
    
    # ??????????????????????
    best = None  # (area, x, y, w, h)
    for i in range(1, num_labels):  # ????(0)
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

    # Merge and expand white regions (signs)
    # Merge and expand white regions (signs)
    white_mask = cv2.bitwise_or(white_mask_raw, connected_mask)
    white_expand_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    white_mask_expanded = cv2.dilate(white_mask, white_expand_kernel, iterations=2)

    # Debug mask should include both white sign + ruler
    mask_all = cv2.bitwise_or(white_mask_expanded, ruler_mask)

    # Inpainting mask only for white sign
    mask = white_mask_expanded
    white_expand_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    white_mask_expanded = cv2.dilate(white_mask, white_expand_kernel, iterations=2)

    # Merge all masks
    mask = cv2.bitwise_or(white_mask_expanded, ruler_mask)
    
    # ===== 适度的形态学操作 =====
    # 使用适度的核进行闭操作
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
    
    # 适度膨胀，确保边缘被覆盖但不要过度
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
    mask = cv2.dilate(mask, kernel_dilate, iterations=1)
    
    # 开操作：去除小噪声
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
    
    # ===== 图像修复 =====
    pixel_count = np.sum(mask > 0)
    print(f"检测到 {pixel_count} 个像素需要修复（{pixel_count/(h*w)*100:.2f}%），正在进行修复...")
    
    # 保存掩码用于调试
    cv2.imwrite('images/mask_debug.png', mask_all)
    cv2.imwrite('images/mask_white_expanded.png', white_mask_expanded)
    print("已保存掩码到 images/mask_debug.png 供调试")
    
    # 修复策略：多次inpaint + 边界平滑
    result = bg.copy()
    
    # 第一轮：大radius的Telea修复
    print("第一轮修复（Telea，radius=40）...")
    result = cv2.inpaint(result, mask, 40, cv2.INPAINT_TELEA)
    
    # 第二轮：Navier-Stokes修复
    print("第二轮修复（NS，radius=40）...")
    result = cv2.inpaint(result, mask, 40, cv2.INPAINT_NS)

    # Extra pass for white signs with larger radius
    result = cv2.inpaint(result, white_mask_expanded, 50, cv2.INPAINT_TELEA)
    
    # 第三轮：Telea细致修复
    print("第三轮修复（Telea，radius=35）...")
    result = cv2.inpaint(result, mask, 35, cv2.INPAINT_TELEA)

    # ????????????????inpaint?
    if np.any(ruler_mask > 0):
        bg_ref = np.mean(bg[0:50, max(0, w-50):w], axis=(0, 1)).astype(np.uint8)
        result[ruler_mask > 0] = bg_ref
    
    # 第四轮：使用双边滤波平滑修复区域
    print("应用边界平滑...")
    result = cv2.bilateralFilter(result, 9, 75, 75)
    
    # 保存结果
    cv2.imwrite(output_path, result)
    print(f"清理完成，已保存到: {output_path}")
    
    return result

def manual_clean_with_preview(bg_path, output_path='images/bg_cleaned.png'):
    """
    交互式手动清理，显示改进的自动检测掩码供用户确认
    使用与auto_clean_background相同的增强检测策略
    """
    print(f"正在加载背景图: {bg_path}")
    bg = cv2.imread(bg_path)
    
    if bg is None:
        raise FileNotFoundError(f"找不到背景图: {bg_path}")
    
    h, w = bg.shape[:2]
    
    # 使用改进的检测策略生成初始掩码
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # 白色检测（精确）
    hsv = cv2.cvtColor(bg, cv2.COLOR_BGR2HSV)
    white_lower = np.array([0, 0, 220])
    white_upper = np.array([180, 40, 255])
    white_mask = cv2.inRange(hsv, white_lower, white_upper)
    
    # 灰色检测（精确）
    gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    gray_mask = cv2.inRange(gray, 150, 200)
    
    # 边缘检测
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
                is_near_edge = (x < margin or y < margin or 
                               x + cw > w - margin or y + ch > h - margin)
                if is_near_edge:
                    expand = 5
                    x1 = max(0, x - expand)
                    y1 = max(0, y - expand)
                    x2 = min(w, x + cw + expand)
                    y2 = min(h, y + ch + expand)
                    cv2.rectangle(ruler_mask, (x1, y1), (x2, y2), 255, -1)
    
    # 连通域分析
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(white_mask, connectivity=8)
    connected_mask = np.zeros((h, w), dtype=np.uint8)
    
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area > 500:
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w_comp = stats[i, cv2.CC_STAT_WIDTH]
            h_comp = stats[i, cv2.CC_STAT_HEIGHT]
            
            aspect = max(w_comp, h_comp) / (min(w_comp, h_comp) + 1)
            if aspect < 5:
                expand = 10
                x1 = max(0, x - expand)
                y1 = max(0, y - expand)
                x2 = min(w, x + w_comp + expand)
                y2 = min(h, y + h_comp + expand)
                
                cv2.rectangle(connected_mask, (x1, y1), (x2, y2), 255, -1)
    
    # 合并掩码
    mask = cv2.bitwise_or(white_mask, ruler_mask)
    mask = cv2.bitwise_or(mask, gray_mask)
    mask = cv2.bitwise_or(mask, connected_mask)
    
    # 形态学操作
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
    mask = cv2.dilate(mask, kernel_dilate, iterations=1)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
    
    # 显示预览
    print("\n显示自动检测结果，按任意键继续...")
    
    # 缩放显示
    disp_scale = 900.0 / h if h > 900 else 1.0
    disp_h, disp_w = int(h * disp_scale), int(w * disp_scale)
    
    # 创建可视化
    mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    mask_color[mask > 0] = [0, 0, 255]  # 红色表示需要移除的区域
    
    combined = cv2.addWeighted(bg, 0.7, mask_color, 0.3, 0)
    combined_disp = cv2.resize(combined, (disp_w, disp_h))
    
    cv2.imshow("Detected regions to remove (red)", combined_disp)
    cv2.waitKey(0)
    cv2.destroyWindow("Detected regions to remove (red)")
    
    # 进行修复
    print("进行图像修复...")
    print("第一轮修复（Telea算法）...")
    result = cv2.inpaint(bg, mask, 15, cv2.INPAINT_TELEA)
    print("第二轮修复（Navier-Stokes算法）...")
    result = cv2.inpaint(result, mask, 15, cv2.INPAINT_NS)
    
    cv2.imwrite(output_path, result)
    print(f"清理完成，已保存到: {output_path}")
    
    return result

if __name__ == "__main__":
    import sys
    
    bg_path = 'images/bg.png'
    output_path = 'images/bg_cleaned.png'
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--manual':
            # 手动模式：显示检测结果供用户确认
            manual_clean_with_preview(bg_path, output_path)
        else:
            # 自动模式
            auto_clean_background(bg_path, output_path)
    else:
        # 默认自动模式
        auto_clean_background(bg_path, output_path)
