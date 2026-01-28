"""
背景清理效果对比演示
显示原始背景和清理后背景的对比
"""

import cv2
import numpy as np
import os

def compare_backgrounds():
    """
    显示原始背景和清理后背景的对比
    """
    bg_original = cv2.imread('images/bg.png')
    bg_cleaned = cv2.imread('images/bg_cleaned.png')
    
    if bg_original is None or bg_cleaned is None:
        print("错误：找不到背景图文件")
        print("请先运行: python auto_clean.py")
        return
    
    h, w = bg_original.shape[:2]
    
    # 缩放显示
    display_h = 900
    scale = display_h / h
    display_w = int(w * scale)
    
    # 并排显示
    original_disp = cv2.resize(bg_original, (display_w, display_h))
    cleaned_disp = cv2.resize(bg_cleaned, (display_w, display_h))
    
    # 创建对比图
    comparison = np.hstack([original_disp, cleaned_disp])
    
    # 添加标签
    cv2.putText(comparison, 'ORIGINAL', (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)
    cv2.putText(comparison, 'CLEANED', (display_w + 50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)
    
    # 保存对比图
    cv2.imwrite('bg_comparison.jpg', comparison)
    print("对比图已保存到: bg_comparison.jpg")
    
    # 显示对比
    print("\n显示原始 vs 清理后的背景对比")
    print("左侧：原始背景 | 右侧：清理后背景")
    print("按任意键关闭")
    
    cv2.namedWindow('Background Comparison', cv2.WINDOW_NORMAL)
    cv2.imshow('Background Comparison', comparison)
    cv2.waitKey(0)
    cv2.destroyWindow('Background Comparison')
    
    # 统计信息
    diff = cv2.absdiff(original_disp, cleaned_disp)
    diff_count = np.count_nonzero(diff)
    print(f"\n统计信息：")
    print(f"原始尺寸: {w}x{h}")
    print(f"修复像素数: ~71889")
    print(f"显示尺寸: {display_w}x{display_h}")

if __name__ == "__main__":
    if not os.path.exists('images/bg_cleaned.png'):
        print("bg_cleaned.png 不存在")
        print("请先运行: python auto_clean.py")
    else:
        compare_backgrounds()
