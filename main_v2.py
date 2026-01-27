import cv2
import numpy as np

# === 配置区域 ===
BG_PATH = 'images/bg.png'      # 图4 (背景)
POD_PATH = 'images/pod.jpg'    # 图2 (豆荚)
SEED_PATH = 'images/seed.jpg'  # 图3 (籽粒)
OUTPUT_PATH = 'result_scientific.jpg'

class ScientificPaster:
    def __init__(self, bg_path):
        self.bg = cv2.imread(bg_path)
        if self.bg is None:
            raise FileNotFoundError(f"找不到背景图: {bg_path}")
        # 计算背景图的基准黑色值（取左上角 50x50 区域的均值作为参考）
        # 假设左上角是纯黑背景
        self.bg_black_ref = np.mean(self.bg[0:50, 0:50], axis=(0, 1))
        print(f"主图背景基准值 (BGR): {self.bg_black_ref}")

    def get_roi_zoomed(self, img_path, win_name="Select Region"):
        """ 修复版框选：自动缩放以适应屏幕，返回高清切片 """
        src = cv2.imread(img_path)
        if src is None:
            raise FileNotFoundError(f"找不到图片: {img_path}")
        
        h, w = src.shape[:2]
        target_h = 800.0 # 屏幕显示高度限制
        scale = target_h / h if h > target_h else 1.0
        
        if scale < 1.0:
            src_display = cv2.resize(src, (int(w * scale), int(target_h)))
        else:
            src_display = src.copy()

        print(f"请在窗口 [{win_name}] 中框选你要展示的矩形区域，按 SPACE 或 ENTER 确认。")
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        roi_rect = cv2.selectROI(win_name, src_display, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow(win_name)
        
        x_s, y_s, w_s, h_s = roi_rect
        if w_s == 0 or h_s == 0: return None
        
        # 映射回原图坐标
        real_x, real_y = int(x_s / scale), int(y_s / scale)
        real_w, real_h = int(w_s / scale), int(h_s / scale)
        
        return src[real_y:real_y+real_h, real_x:real_x+real_w]

    def match_background_color(self, roi):
        """ 
        色差调整算法：
        计算 ROI 边缘（认为是背景）的颜色，将其平移对齐到主图的背景颜色。
        """
        # 1. 采样 ROI 的背景颜色 (取 ROI 左上角 20x20 的区域)
        # 注意：这里假设你框选的时候，左上角是黑背景
        roi_bg_ref = np.mean(roi[0:20, 0:20], axis=(0, 1))
        
        # 2. 计算差值 (Diff) = 主图背景 - ROI背景
        diff = self.bg_black_ref - roi_bg_ref
        
        # 3. 将差值应用到整个 ROI
        # 使用 float防止溢出，最后转回 uint8
        res = roi.astype(np.float32) + diff
        
        # 4. 截断到 0-255 范围
        res = np.clip(res, 0, 255).astype(np.uint8)
        
        print(f"色差校正: ROI背景 {roi_bg_ref} -> 修正偏移 {diff}")
        return res

    def paste_inset(self, inset_img, prompt="Click to Paste"):
        """ 交互式粘贴矩形插图 """
        # 这里设定插图的一个固定宽度，比如主图宽度的 1/3，保持比例
        # 参考图中插图大概占宽度的 30% - 40%
        bg_h, bg_w = self.bg.shape[:2]
        target_w = int(bg_w * 0.35) 
        
        h, w = inset_img.shape[:2]
        scale = target_w / w
        new_w, new_h = int(w * scale), int(h * scale)
        
        inset_resized = cv2.resize(inset_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        print(f"请在背景图上点击 [{prompt}] 的位置 (点击左上角)...")
        
        click_pos = [0, 0]
        def on_mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                click_pos[0], click_pos[1] = x, y

        win_name = "Positioning (Press SPACE to Confirm)"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        # 同样缩放背景图以便显示
        display_scale = 800.0 / bg_h if bg_h > 800 else 1.0
        bg_display = cv2.resize(self.bg, (int(bg_w*display_scale), int(bg_h*display_scale)))
        
        # 因为我们在缩放图上点击，需要换算坐标
        def on_mouse_scaled(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                real_x = int(x / display_scale)
                real_y = int(y / display_scale)
                click_pos[0], click_pos[1] = real_x, real_y

        cv2.setMouseCallback(win_name, on_mouse_scaled)
        
        while True:
            # 这是一个简单的预览图
            preview = self.bg.copy()
            x, y = click_pos
            
            # 边界检查
            if y + new_h < bg_h and x + new_w < bg_w:
                # 直接覆盖像素 (也就是我们要的矩形插图效果)
                preview[y:y+new_h, x:x+new_w] = inset_resized
                # 画个白框装饰一下（可选，类似参考图的效果）
                # cv2.rectangle(preview, (x, y), (x+new_w, y+new_h), (255, 255, 255), 2)
            
            # 缩小显示以便预览
            preview_display = cv2.resize(preview, (int(bg_w*display_scale), int(bg_h*display_scale)))
            cv2.imshow(win_name, preview_display)
            
            key = cv2.waitKey(20) & 0xFF
            if key == 32 or key == 13: # Space or Enter
                break
        
        cv2.destroyWindow(win_name)
        
        # 最终确认粘贴
        x, y = click_pos
        if y + new_h < bg_h and x + new_w < bg_w:
            self.bg[y:y+new_h, x:x+new_w] = inset_resized
            print("粘贴成功！")
        else:
            print("位置超出边界，未粘贴。")

    def save(self):
        cv2.imwrite(OUTPUT_PATH, self.bg)
        print(f"完成！图片已保存为: {OUTPUT_PATH}")

# === 主流程 ===
if __name__ == "__main__":
    processor = ScientificPaster(BG_PATH)
    
    # 1. 豆荚 (Pod)
    print(">>> 步骤 1/2: 框选豆荚")
    roi_pod = processor.get_roi_zoomed(POD_PATH, "Select POD Region")
    if roi_pod is not None:
        # 校正背景色
        roi_pod = processor.match_background_color(roi_pod)
        # 粘贴
        processor.paste_inset(roi_pod, "Set Pod Position")

    # 2. 籽粒 (Seed)
    print("\n>>> 步骤 2/2: 框选籽粒")
    roi_seed = processor.get_roi_zoomed(SEED_PATH, "Select SEED Region")
    if roi_seed is not None:
        roi_seed = processor.match_background_color(roi_seed)
        processor.paste_inset(roi_seed, "Set Seed Position")

    processor.save()