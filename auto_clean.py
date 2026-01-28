"""
背景自动清理脚本
支持自动检测和移除白色对象（如白色牌子）和金属尺子等
"""

import cv2
import numpy as np

def auto_clean_background(bg_path, output_path='images/bg_cleaned.png'):
    """
    自动清理背景图：检测并移除白色对象和金属对象
    """
    print(f"正在加载背景图: {bg_path}")
    bg = cv2.imread(bg_path)
    
    if bg is None:
        raise FileNotFoundError(f"找不到背景图: {bg_path}")
    
    h, w = bg.shape[:2]
    print(f"背景图大小: {h}x{w}")
    
    # 创建掩码用于标记需要移除的区域
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # ===== 方法1: 检测白色区域 =====
    # 白色牌子通常具有高亮度和低饱和度
    hsv = cv2.cvtColor(bg, cv2.COLOR_BGR2HSV)
    
    # 检测白色区域（低饱和度，高亮度）
    white_lower = np.array([0, 0, 200])
    white_upper = np.array([180, 50, 255])
    white_mask = cv2.inRange(hsv, white_lower, white_upper)
    
    # ===== 方法2: 检测灰色金属尺子 =====
    # 金属尺子通常是灰色，在白色背景上会有明显的边界
    # 使用边缘检测
    gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    
    # 高斯模糊
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Canny边缘检测
    edges = cv2.Canny(blurred, 50, 150)
    
    # 查找轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 过滤出尺子形状的轮廓（细长的线性对象）
    ruler_mask = np.zeros((h, w), dtype=np.uint8)
    
    for contour in contours:
        area = cv2.contourArea(contour)
        # 尺子应该是细长的，面积较小但周长较长
        if area > 500:  # 最小面积阈值
            x, y, cw, ch = cv2.boundingRect(contour)
            aspect_ratio = max(cw, ch) / (min(cw, ch) + 1)
            # 尺子的纵横比应该较大（细长）
            if 3 < aspect_ratio < 50:
                cv2.drawContours(ruler_mask, [contour], 0, 255, -1)
    
    # 合并白色和尺子掩码
    mask = cv2.bitwise_or(white_mask, ruler_mask)
    
    # 形态学操作：闭操作（填补小孔）和开操作（去除小噪声）
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    
    # ===== 图像修复 =====
    print(f"检测到 {np.sum(mask > 0)} 个像素需要修复，正在进行修复...")
    
    # 使用多个radius参数进行修复以获得更好效果
    result = cv2.inpaint(bg, mask, 10, cv2.INPAINT_TELEA)
    
    # 可选：进一步优化使用Navier-Stokes算法
    # result = cv2.inpaint(bg, mask, 10, cv2.INPAINT_NS)
    
    # 保存结果
    cv2.imwrite(output_path, result)
    print(f"清理完成，已保存到: {output_path}")
    
    return result

def manual_clean_with_preview(bg_path, output_path='images/bg_cleaned.png'):
    """
    交互式手动清理，显示自动检测的掩码供用户确认
    """
    print(f"正在加载背景图: {bg_path}")
    bg = cv2.imread(bg_path)
    
    if bg is None:
        raise FileNotFoundError(f"找不到背景图: {bg_path}")
    
    h, w = bg.shape[:2]
    
    # 自动生成初始掩码
    hsv = cv2.cvtColor(bg, cv2.COLOR_BGR2HSV)
    white_lower = np.array([0, 0, 200])
    white_upper = np.array([180, 50, 255])
    white_mask = cv2.inRange(hsv, white_lower, white_upper)
    
    gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ruler_mask = np.zeros((h, w), dtype=np.uint8)
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 500:
            x, y, cw, ch = cv2.boundingRect(contour)
            aspect_ratio = max(cw, ch) / (min(cw, ch) + 1)
            if 3 < aspect_ratio < 50:
                cv2.drawContours(ruler_mask, [contour], 0, 255, -1)
    
    mask = cv2.bitwise_or(white_mask, ruler_mask)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
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
    result = cv2.inpaint(bg, mask, 10, cv2.INPAINT_TELEA)
    
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
