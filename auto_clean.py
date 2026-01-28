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
    white_mask = cv2.inRange(hsv, white_lower, white_upper)
    
    # ===== 方法2: 基于形状和直线的标尺检测（不依赖颜色） =====
    # 标尺特征：非常细长的直线，通常在图像边缘
    gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    
    # 使用Canny边缘检测
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    # 使用Hough直线变换检测长直线（标尺的特征）
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=500, maxLineGap=20)
    
    ruler_mask = np.zeros((h, w), dtype=np.uint8)
    
    if lines is not None:
        print(f"检测到 {len(lines)} 条直线")
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # 计算直线的长度和角度
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            
            # 计算是否是水平或垂直线（标尺通常是直的）
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            
            if dx > dy:  # 水平线
                angle_to_straight = dy / (dx + 1)
            else:  # 垂直线
                angle_to_straight = dx / (dy + 1)
            
            is_near_straight = angle_to_straight < 0.1  # 几乎水平或垂直
            is_long_enough = length > 300  # 足够长
            
            if is_near_straight and is_long_enough:
                # 线条宽度膨胀（标尺有宽度）
                pt1 = (x1, y1)
                pt2 = (x2, y2)
                cv2.line(ruler_mask, pt1, pt2, 255, 20)  # 20像素宽
    
    # 补充：轮廓分析找极端细长的物体
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"找到 {len(contours)} 个轮廓，正在筛选标尺...")
    for contour in contours:
        area = cv2.contourArea(contour)
        # 只看极细长的轮廓（与植株区分）
        if 300 < area < 100000:  # 合理的面积范围
            x, y, cw, ch = cv2.boundingRect(contour)
            
            # 计算纵横比
            aspect_ratio = max(cw, ch) / (min(cw, ch) + 1)
            
            # 标尺必须非常细长（至少20:1）
            if aspect_ratio > 20:
                # 检查是否靠近边缘（标尺通常在边缘）
                margin = 150
                is_near_edge = (x < margin or y < margin or 
                               x + cw > w - margin or y + ch > h - margin)
                
                if is_near_edge:
                    # 有一定膨胀空间来确保完全覆盖
                    expand = 8
                    x1 = max(0, x - expand)
                    y1 = max(0, y - expand)
                    x2 = min(w, x + cw + expand)
                    y2 = min(h, y + ch + expand)
                    cv2.rectangle(ruler_mask, (x1, y1), (x2, y2), 255, -1)
    
    # ===== 方法3: 连通域分析 - 找到大块的白色区域（牌子） =====
    # 对白色掩码进行连通域分析
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(white_mask, connectivity=8)
    
    connected_mask = np.zeros((h, w), dtype=np.uint8)
    print(f"找到 {num_labels-1} 个白色连通域")
    
    for i in range(1, num_labels):  # 跳过背景(0)
        area = stats[i, cv2.CC_STAT_AREA]
        # 白色牌子应该有较大面积
        if area > 500:  # 提高阈值，只保留大块白色区域
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w_comp = stats[i, cv2.CC_STAT_WIDTH]
            h_comp = stats[i, cv2.CC_STAT_HEIGHT]
            
            # 检查是否接近正方形或矩形（牌子的特征）
            aspect = max(w_comp, h_comp) / (min(w_comp, h_comp) + 1)
            if aspect < 5:  # 不能太细长
                # 适度扩展区域
                expand = 10
                x1 = max(0, x - expand)
                y1 = max(0, y - expand)
                x2 = min(w, x + w_comp + expand)
                y2 = min(h, y + h_comp + expand)
                
                cv2.rectangle(connected_mask, (x1, y1), (x2, y2), 255, -1)
    
    # ===== 合并所有掩码 =====
    mask = cv2.bitwise_or(white_mask, ruler_mask)
    mask = cv2.bitwise_or(mask, gray_mask)
    mask = cv2.bitwise_or(mask, connected_mask)
    
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
    cv2.imwrite('images/mask_debug.png', mask)
    print("已保存掩码到 images/mask_debug.png 供调试")
    
    # 使用更大的radius参数进行修复以获得更好效果
    print("第一轮修复（Telea算法）...")
    result = cv2.inpaint(bg, mask, 15, cv2.INPAINT_TELEA)
    
    # 第二轮修复：使用Navier-Stokes算法进一步优化
    print("第二轮修复（Navier-Stokes算法）...")
    result = cv2.inpaint(result, mask, 15, cv2.INPAINT_NS)
    
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
