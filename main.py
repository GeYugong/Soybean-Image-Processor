import cv2
import numpy as np
import os

# === 配置区域 ===
# 图片路径
BG_PATH = 'images/bg.png'      # 你的背景图 (图4)
POD_PATH = 'images/pod.jpg'    # 豆荚原图 (图2)
SEED_PATH = 'images/seed.jpg'  # 种子原图 (图3)
OUTPUT_PATH = 'result_final.jpg'

class ImageProcessor:
    def __init__(self, bg_path):
        self.bg = cv2.imread(bg_path)
        if self.bg is None:
            raise FileNotFoundError(f"找不到背景图: {bg_path}")
        self.bg_display = self.bg.copy() # 用于显示的副本

    # def get_roi_interactive(self, img_path, win_name="Select ROI"):
    #     """ 交互式提取：弹窗让用户框选要抠的物体 """
    #     src = cv2.imread(img_path)
    #     if src is None:
    #         raise FileNotFoundError(f"找不到图片: {img_path}")
        
    #     print(f"请在弹出的窗口中框选 [{win_name}]，选好后按 ENTER 或 空格 确认。")
    #     # cv2.selectROI 允许你用鼠标画框
    #     x, y, w, h = cv2.selectROI(win_name, src, showCrosshair=True, fromCenter=False)
    #     cv2.destroyWindow(win_name)
        
    #     if w == 0 or h == 0:
    #         return None # 用户取消了
        
    #     return src[y:y+h, x:x+w]

    def get_roi_interactive(self, img_path, win_name="Select ROI"):
        """ 
        交互式提取（修复版）：自动缩小图片以适应屏幕，
        选完后自动映射回原图坐标。
        """
        src = cv2.imread(img_path)
        if src is None:
            raise FileNotFoundError(f"找不到图片: {img_path}")
        
        # --- 新增逻辑：计算缩放比例 ---
        h, w = src.shape[:2]
        # 设定一个屏幕能显示的最大高度（例如 800 像素）
        target_h = 800.0 
        
        if h > target_h:
            scale = target_h / h
            new_w = int(w * scale)
            new_h = int(target_h)
            # 生成一张缩略图用于显示
            src_display = cv2.resize(src, (new_w, new_h))
        else:
            scale = 1.0
            src_display = src.copy()

        print(f"为了适应屏幕，显示缩放比例: {scale:.2f}")
        print(f"请在弹出的窗口中框选 [{win_name}]，选好后按 ENTER 或 空格 确认。")
        
        # 这一行很关键：把窗口设为可调整大小（虽然 selectROI 有时会忽略这个，但加上保险）
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL) 
        
        # 在【缩略图】上进行框选
        # x, y, w, h 是在缩略图上的坐标
        roi_rect = cv2.selectROI(win_name, src_display, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow(win_name)
        
        x_small, y_small, w_small, h_small = roi_rect
        
        if w_small == 0 or h_small == 0:
            return None # 用户取消了
        
        # --- 新增逻辑：坐标映射回原图 ---
        # 比如你在 0.5 倍的图上选了 100px，在原图其实是 200px
        real_x = int(x_small / scale)
        real_y = int(y_small / scale)
        real_w = int(w_small / scale)
        real_h = int(h_small / scale)
        
        # 返回原图的高清切片
        return src[real_y : real_y + real_h, real_x : real_x + real_w]

    def remove_black_background(self, roi):
        """ 自动去除黑色背景 """
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        # 阈值策略：亮度(V)非常低的确认为背景
        # 你可以根据实际情况调整这里的 60. 如果抠多了就调小，抠少了就调大
        lower = np.array([0, 0, 0])
        upper = np.array([180, 255, 60]) 
        mask = cv2.inRange(hsv, lower, upper)
        
        # 反转：我们要非黑色的部分
        mask_inv = cv2.bitwise_not(mask)
        
        # 简单平滑处理，去掉边缘锯齿
        mask_inv = cv2.GaussianBlur(mask_inv, (3, 3), 0)
        return roi, mask_inv

    def color_transfer(self, source_roi, source_mask):
        """ 色彩迁移：让源物体的色调去匹配背景 """
        # 计算背景的均值（排除纯黑区域）
        bg_gray = cv2.cvtColor(self.bg, cv2.COLOR_BGR2GRAY)
        bg_mean = cv2.mean(self.bg, mask=(bg_gray > 10).astype(np.uint8))[:3]
        
        # 计算源物体的均值
        src_mean = cv2.mean(source_roi, mask=source_mask)[:3]
        
        # 简单的增益补偿: Target / Source
        # 我们稍微降低一点亮度 (0.9)，通常会让拼贴更自然，不那么“跳”
        gain = np.array(bg_mean) / (np.array(src_mean) + 1e-5) * 0.9
        
        res = np.multiply(source_roi.astype(float), gain)
        res = np.clip(res, 0, 255).astype(np.uint8)
        return res

    def paste_interactive(self, element, mask, scale=1.0):
        """ 交互式粘贴：点哪里贴哪里 """
        # 1. 缩放
        h, w = element.shape[:2]
        new_w, new_h = int(w * scale), int(h * scale)
        element_resized = cv2.resize(element, (new_w, new_h))
        mask_resized = cv2.resize(mask, (new_w, new_h))
        
        print("请在背景图上点击你想放置的位置 (点击后按任意键确认位置)...")
        
        # 定义鼠标回调函数来获取点击位置
        click_pos = [0, 0]
        def on_mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                click_pos[0], click_pos[1] = x, y
                print(f"选中位置: {x}, {y}")

        temp_bg = self.bg.copy()
        win_name = "Click to Paste (Press Any Key to Confirm)"
        cv2.namedWindow(win_name)
        cv2.setMouseCallback(win_name, on_mouse)
        
        while True:
            display = temp_bg.copy()
            # 实时画个框显示大概位置
            cv2.rectangle(display, (click_pos[0], click_pos[1]), 
                          (click_pos[0]+new_w, click_pos[1]+new_h), (0, 255, 0), 2)
            cv2.imshow(win_name, display)
            if cv2.waitKey(20) & 0xFF != 255: # 按任意键退出
                break
        cv2.destroyWindow(win_name)
        
        # 开始融合
        x, y = click_pos
        # 边界保护
        if y + new_h > self.bg.shape[0] or x + new_w > self.bg.shape[1]:
            print("错误：位置超出边界，无法粘贴")
            return

        roi_bg = self.bg[y:y+new_h, x:x+new_w]
        
        # Mask融合算法
        mask_3ch = cv2.merge([mask_resized, mask_resized, mask_resized])
        # mask > 0 的地方用前景，否则用背景
        result_roi = np.where(mask_3ch > 0, element_resized, roi_bg)
        
        self.bg[y:y+new_h, x:x+new_w] = result_roi
        print("粘贴完成！")

    def save(self):
        cv2.imwrite(OUTPUT_PATH, self.bg)
        print(f"最终图片已保存至: {OUTPUT_PATH}")

# === 主流程 ===
if __name__ == "__main__":
    processor = ImageProcessor(BG_PATH)
    
    # 1. 处理豆荚
    print(">>> 步骤1: 提取豆荚")
    pod_roi = processor.get_roi_interactive(POD_PATH, "Select POD (Draw a rect)")
    if pod_roi is not None:
        pod_roi, pod_mask = processor.remove_black_background(pod_roi)
        pod_roi = processor.color_transfer(pod_roi, pod_mask)
        # scale=0.8 表示缩放大小，你可以根据实际效果改这个数字
        processor.paste_interactive(pod_roi, pod_mask, scale=1.0) 

    # 2. 处理种子 (逻辑完全一样)
    print("\n>>> 步骤2: 提取种子")
    seed_roi = processor.get_roi_interactive(SEED_PATH, "Select SEED")
    if seed_roi is not None:
        seed_roi, seed_mask = processor.remove_black_background(seed_roi)
        seed_roi = processor.color_transfer(seed_roi, seed_mask)
        processor.paste_interactive(seed_roi, seed_mask, scale=1.0)

    # 3. 保存
    processor.save()