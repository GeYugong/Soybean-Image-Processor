import cv2
import numpy as np

# === 配置区域 ===
BG_PATH = 'images/bg.png'      
POD_PATH = 'images/pod.jpg'    
SEED_PATH = 'images/seed.jpg'  
OUTPUT_PATH = 'result_final_v4.jpg'
BG_CLEANED_PATH = 'images/bg_cleaned.png'  # 清理后的背景

class UltimatePaster:
    def __init__(self, bg_path):
        self.bg = cv2.imread(bg_path)
        if self.bg is None:
            raise FileNotFoundError(f"找不到背景图: {bg_path}")
        # 计算背景基准值 (左上角)
        self.bg_black_ref = np.mean(self.bg[0:50, 0:50], axis=(0, 1))

    def clean_background(self):
        """
        清理背景图：移除尺子和白色牌子
        用户可交互式地标记需要移除的区域，使用inpainting技术修复
        """
        print(">>> 清理背景图：标记需要移除的区域")
        print("按照以下步骤操作：")
        print("1. 在显示的图像上标记尺子和白色牌子的位置（可标记多个）")
        print("2. 标记完成后，程序会自动修复这些区域")
        
        # 创建工作副本
        bg_work = self.bg.copy()
        mask = np.zeros(bg_work.shape[:2], dtype=np.uint8)
        
        # 设置显示缩放
        screen_h = 900.0
        bg_h, bg_w = bg_work.shape[:2]
        disp_scale = screen_h / bg_h if bg_h > screen_h else 1.0
        
        rects = []  # 存储用户标记的矩形
        drawing = False
        rect_start = None
        
        def mouse_callback(event, x, y, flags, param):
            nonlocal drawing, rect_start, rects
            
            # 映射回真实坐标
            real_x = int(x / disp_scale)
            real_y = int(y / disp_scale)
            
            if event == cv2.EVENT_LBUTTONDOWN:
                drawing = True
                rect_start = (real_x, real_y)
                
            elif event == cv2.EVENT_LBUTTONUP:
                if drawing and rect_start:
                    drawing = False
                    # 确保坐标正确排列
                    x1, y1 = rect_start
                    x2, y2 = real_x, real_y
                    x1, x2 = min(x1, x2), max(x1, x2)
                    y1, y2 = min(y1, y2), max(y1, y2)
                    
                    rects.append((x1, y1, x2, y2))
                    # 在mask上标记该区域
                    cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
                    print(f"已标记区域: ({x1}, {y1}) -> ({x2}, {y2})")
        
        win_name = "Clean Background - Draw rectangles | SPACE to confirm | ESC to cancel"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(win_name, mouse_callback)
        
        # 显示预览直到用户确认
        while True:
            preview = bg_work.copy()
            
            # 绘制已标记的矩形
            for x1, y1, x2, y2 in rects:
                cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(preview, 'Remove', (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # 显示缩放版本
            disp_h, disp_w = int(bg_h * disp_scale), int(bg_w * disp_scale)
            preview_disp = cv2.resize(preview, (disp_w, disp_h))
            cv2.imshow(win_name, preview_disp)
            
            key = cv2.waitKey(10) & 0xFF
            if key == 32:  # SPACE 确认
                break
            elif key == 27:  # ESC 取消
                cv2.destroyWindow(win_name)
                print("已取消背景清理")
                return False
        
        cv2.destroyWindow(win_name)
        
        # 如果没有标记任何区域，直接返回
        if len(rects) == 0:
            print("未标记任何区域，跳过清理")
            return False
        
        # 使用 Telea 或 Navier-Stokes 算法进行inpainting修复
        print(f"正在修复 {len(rects)} 个区域...")
        
        # 使用多次迭代的Telea算法进行修复
        self.bg = cv2.inpaint(bg_work, mask, 5, cv2.INPAINT_TELEA)
        
        # 保存清理后的背景
        cv2.imwrite(BG_CLEANED_PATH, self.bg)
        print(f"清理完成，已保存清理后的背景: {BG_CLEANED_PATH}")
        
        # 重新计算背景基准值
        self.bg_black_ref = np.mean(self.bg[0:50, 0:50], axis=(0, 1))
        
        return True

    def get_roi_zoomed(self, img_path, win_name="Select Region"):
        """ (保持不变) 高清切片提取 """
        src = cv2.imread(img_path)
        if src is None: raise FileNotFoundError(f"找不到: {img_path}")
        
        h, w = src.shape[:2]
        target_h = 900.0 
        scale = target_h / h if h > target_h else 1.0
        
        if scale < 1.0:
            src_disp = cv2.resize(src, (int(w * scale), int(target_h)))
        else:
            src_disp = src.copy()

        print(f"请在 [{win_name}] 中框选区域，按 SPACE/ENTER 确认。")
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        roi_rect = cv2.selectROI(win_name, src_disp, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow(win_name)
        
        x_s, y_s, w_s, h_s = roi_rect
        if w_s == 0 or h_s == 0: return None
        
        real_x, real_y = int(x_s/scale), int(y_s/scale)
        real_w, real_h = int(w_s/scale), int(h_s/scale)
        return src[real_y:real_y+real_h, real_x:real_x+real_w]

    def match_background(self, roi):
        """ (保持不变) 自动色差平衡 """
        roi_bg_ref = np.mean(roi[0:20, 0:20], axis=(0, 1))
        diff = self.bg_black_ref - roi_bg_ref
        res = roi.astype(np.float32) + diff
        return np.clip(res, 0, 255).astype(np.uint8)

    def interactive_place(self, inset_img):
        """ 
        >>> 滚轮版交互模式 <<<
        - 鼠标移动：控制位置
        - 鼠标滚轮：放大/缩小 (每次 5%)
        - 鼠标左键：确认放置
        """
        # 初始缩放设为背景宽度的 35%
        current_scale = (self.bg.shape[1] * 0.35) / inset_img.shape[1]
        
        # 状态变量
        pos = [0, 0] # [x, y]
        placed = False
        
        # 窗口设置
        win_name = "Mouse Wheel to Resize | Click to Confirm"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        
        # 预计算显示缩放比例
        screen_h = 900.0
        bg_h, bg_w = self.bg.shape[:2]
        disp_scale = screen_h / bg_h if bg_h > screen_h else 1.0
        
        # === 核心修改：鼠标回调函数 ===
        def mouse_callback(event, x, y, flags, param):
            nonlocal placed, current_scale
            # 映射回真实坐标
            real_x = int(x / disp_scale)
            real_y = int(y / disp_scale)
            
            if event == cv2.EVENT_MOUSEMOVE:
                # 更新位置
                pos[0], pos[1] = real_x, real_y
                
            elif event == cv2.EVENT_MOUSEWHEEL:
                # 滚轮缩放逻辑
                # flags > 0 表示向前滚(放大)，flags < 0 表示向后滚(缩小)
                if flags > 0:
                    current_scale *= 1.05 # 放大 5%
                else:
                    current_scale *= 0.95 # 缩小 5%
                print(f"当前缩放比例: {current_scale:.2f}")
                
            elif event == cv2.EVENT_LBUTTONDOWN:
                # 确认放置
                placed = True 

        cv2.setMouseCallback(win_name, mouse_callback)
        
        print(">>> 进入调整模式：")
        print("    [鼠标移动] 选择位置")
        print("    [鼠标滚轮] 放大 / 缩小")
        print("    [鼠标左键] 确认并保存")

        while not placed:
            # 1. 根据当前 scale 计算插图大小
            h_i, w_i = inset_img.shape[:2]
            new_w, new_h = int(w_i * current_scale), int(h_i * current_scale)
            inset_resized = cv2.resize(inset_img, (new_w, new_h))
            
            # 2. 绘制预览
            preview = self.bg.copy()
            
            # 让鼠标位于插图中心
            top_x = pos[0] - new_w // 2
            top_y = pos[1] - new_h // 2
            
            # 边界计算
            y1, y2 = max(0, top_y), min(bg_h, top_y + new_h)
            x1, x2 = max(0, top_x), min(bg_w, top_x + new_w)
            iy1, iy2 = y1 - top_y, y2 - top_y
            ix1, ix2 = x1 - top_x, x2 - top_x
            
            if y2 > y1 and x2 > x1:
                preview[y1:y2, x1:x2] = inset_resized[iy1:iy2, ix1:ix2]
                cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 2) # 绿框

            # 3. 显示
            disp_h, disp_w = int(bg_h * disp_scale), int(bg_w * disp_scale)
            cv2.imshow(win_name, cv2.resize(preview, (disp_w, disp_h)))
            
            key = cv2.waitKey(10) & 0xFF
            if key == 27: # ESC 退出
                break
        
        cv2.destroyWindow(win_name)
        
        # 4. 最终放置
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
                print(f"成功放置！")

    def save(self):
        cv2.imwrite(OUTPUT_PATH, self.bg)
        print(f"全部完成: {OUTPUT_PATH}")

# === 主程序 ===
if __name__ == "__main__":
    import os
    import sys
    
    # 检查是否存在预清理的背景
    use_cleaned = False
    if os.path.exists(BG_CLEANED_PATH):
        print(f"检测到清理后的背景: {BG_CLEANED_PATH}")
        response = input("是否使用预清理的背景？(y/n, 默认y): ").strip().lower()
        use_cleaned = response != 'n'
    
    # 加载背景
    if use_cleaned:
        print(f"使用清理后的背景: {BG_CLEANED_PATH}")
        app = UltimatePaster(BG_CLEANED_PATH)
    else:
        print(f"使用原始背景: {BG_PATH}")
        app = UltimatePaster(BG_PATH)
        
        # 询问是否进行清理
        response = input("是否现在清理背景？(y/n, 默认y): ").strip().lower()
        if response != 'n':
            print("\n>>> 步骤0: 清理背景图（移除尺子和白色牌子）")
            app.clean_background()
    
    print("\n>>> 步骤1: 提取豆荚")
    roi1 = app.get_roi_zoomed(POD_PATH, "Select POD")
    if roi1 is not None:
        roi1 = app.match_background(roi1)
        app.interactive_place(roi1) 
        
    print("\n>>> 步骤2: 提取种子")
    roi2 = app.get_roi_zoomed(SEED_PATH, "Select SEED")
    if roi2 is not None:
        roi2 = app.match_background(roi2)
        app.interactive_place(roi2) 
        
    app.save()