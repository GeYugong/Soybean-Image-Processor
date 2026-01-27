import cv2
import numpy as np

# === 配置区域 ===
BG_PATH = 'images/bg.png'      
POD_PATH = 'images/pod.jpg'    
SEED_PATH = 'images/seed.jpg'  
OUTPUT_PATH = 'result_final_v3.jpg'

class UltimatePaster:
    def __init__(self, bg_path):
        self.bg = cv2.imread(bg_path)
        if self.bg is None:
            raise FileNotFoundError(f"找不到背景图: {bg_path}")
        # 计算背景基准值 (左上角)
        self.bg_black_ref = np.mean(self.bg[0:50, 0:50], axis=(0, 1))

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
        >>> 游戏级交互模式 <<<
        - 鼠标移动：控制位置
        - 键盘 W/S：放大/缩小 (每次 1%)
        - 鼠标左键：确认放置
        """
        # 初始缩放设为背景宽度的 35%
        current_scale = (self.bg.shape[1] * 0.35) / inset_img.shape[1]
        
        # 状态变量
        pos = [0, 0] # [x, y]
        placed = False
        
        # 窗口设置
        win_name = "WASD to Resize | Click to Confirm"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        
        # 预计算显示缩放比例（为了在你的屏幕上能完整看到背景图）
        screen_h = 900.0
        bg_h, bg_w = self.bg.shape[:2]
        disp_scale = screen_h / bg_h if bg_h > screen_h else 1.0
        
        # 鼠标回调：只更新位置坐标
        def mouse_callback(event, x, y, flags, param):
            nonlocal placed
            # 映射回真实坐标
            real_x = int(x / disp_scale)
            real_y = int(y / disp_scale)
            
            if event == cv2.EVENT_MOUSEMOVE:
                pos[0], pos[1] = real_x, real_y
            elif event == cv2.EVENT_LBUTTONDOWN:
                placed = True # 点击确认

        cv2.setMouseCallback(win_name, mouse_callback)
        
        print(">>> 进入调整模式：")
        print("    [鼠标移动] 选择位置")
        print("    [W / S] 放大 / 缩小")
        print("    [鼠标左键] 确认并保存")

        while not placed:
            # 1. 根据当前 scale 计算插图大小
            h_i, w_i = inset_img.shape[:2]
            new_w, new_h = int(w_i * current_scale), int(h_i * current_scale)
            inset_resized = cv2.resize(inset_img, (new_w, new_h))
            
            # 2. 在背景副本上绘制预览
            # 为了性能，我们只在每一帧复制一次背景
            preview = self.bg.copy()
            
            # 计算左上角坐标 (让鼠标位于插图中心)
            top_x = pos[0] - new_w // 2
            top_y = pos[1] - new_h // 2
            
            # 边界保护与绘制
            # 只在图像范围内绘制有效区域
            y1, y2 = max(0, top_y), min(bg_h, top_y + new_h)
            x1, x2 = max(0, top_x), min(bg_w, top_x + new_w)
            
            # 对应的插图切片坐标
            iy1, iy2 = y1 - top_y, y2 - top_y
            ix1, ix2 = x1 - top_x, x2 - top_x
            
            if y2 > y1 and x2 > x1:
                preview[y1:y2, x1:x2] = inset_resized[iy1:iy2, ix1:ix2]
                # 画个绿框表示选中状态
                cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 3. 显示 (缩放以适应屏幕)
            disp_h, disp_w = int(bg_h * disp_scale), int(bg_w * disp_scale)
            cv2.imshow(win_name, cv2.resize(preview, (disp_w, disp_h)))
            
            # 4. 键盘控制
            key = cv2.waitKey(10) & 0xFF # 10ms 延迟，保证流畅
            if key == ord('w'): # 放大
                current_scale *= 1.02
            elif key == ord('s'): # 缩小
                current_scale *= 0.98
            elif key == 27: # ESC 退出
                break
        
        cv2.destroyWindow(win_name)
        
        # 5. 循环结束，执行最终的“烙印”
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
                print(f"成功放置！位置: {top_x}, {top_y}, 缩放: {current_scale:.2f}")

    def save(self):
        cv2.imwrite(OUTPUT_PATH, self.bg)
        print(f"全部完成: {OUTPUT_PATH}")

# === 主程序 ===
if __name__ == "__main__":
    app = UltimatePaster(BG_PATH)
    
    print(">>> 步骤1: 提取豆荚")
    roi1 = app.get_roi_zoomed(POD_PATH, "Select POD")
    if roi1 is not None:
        roi1 = app.match_background(roi1)
        app.interactive_place(roi1) # 进入游戏模式
        
    print("\n>>> 步骤2: 提取种子")
    roi2 = app.get_roi_zoomed(SEED_PATH, "Select SEED")
    if roi2 is not None:
        roi2 = app.match_background(roi2)
        app.interactive_place(roi2) # 进入游戏模式
        
    app.save()