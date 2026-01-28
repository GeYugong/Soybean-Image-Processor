# 程序改进总结

## 新增功能

本次更新添加了**背景清理**功能，可以在合成大豆图像之前移除背景中的尺子和白色牌子等不需要的物体。

## 新增文件

1. **auto_clean.py** - 自动背景清理脚本
   - 自动检测白色对象和金属尺子
   - 使用图像修复（inpainting）算法填补移除的区域
   - 支持手动验证模式

2. **compare_bg.py** - 清理效果对比工具
   - 并排显示原始和清理后的背景
   - 保存对比图像
   - 显示统计信息

3. **CLEANING_GUIDE.md** - 详细清理指南
   - 自动/手动清理方法说明
   - 修复算法详解
   - 参数调整建议
   - 常见问题解答

4. **images/bg_cleaned.png** - 清理后的背景（自动生成）

## 改进的文件

### main.py
- 添加 `clean_background()` 方法 - 交互式手动清理
- 改进主程序流程 - 智能检测和使用预清理背景
- 添加用户确认机制 - 选择是否使用/进行清理

### README.md
- 添加详细的使用说明
- 说明三种使用方式
- 提供推荐工作流程

## 技术实现

### 自动清理（auto_clean.py）

1. **颜色分割**
   ```python
   # HSV颜色空间检测白色区域
   white_lower = np.array([0, 0, 200])    # 低饱和度
   white_upper = np.array([180, 50, 255])  # 高亮度
   ```

2. **边缘检测 + 轮廓分析**
   ```python
   # Canny边缘检测
   edges = cv2.Canny(blurred, 50, 150)
   
   # 过滤细长物体（尺子）
   aspect_ratio = max(cw, ch) / (min(cw, ch) + 1)
   if 3 < aspect_ratio < 50:  # 纵横比判断
   ```

3. **图像修复**
   ```python
   # Telea算法修复
   result = cv2.inpaint(bg, mask, 10, cv2.INPAINT_TELEA)
   ```

### 手动清理（main.py）

1. **交互式标记**
   - 鼠标拖拽绘制矩形
   - 支持标记多个区域
   - 实时预览标记结果

2. **掩码生成**
   ```python
   mask = np.zeros(shape, dtype=np.uint8)
   cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
   ```

3. **修复与保存**
   ```python
   self.bg = cv2.inpaint(bg_work, mask, 5, cv2.INPAINT_TELEA)
   cv2.imwrite(BG_CLEANED_PATH, self.bg)
   ```

## 使用流程

### 推荐流程（首次使用）

```
1. 自动清理背景
   python auto_clean.py
   
2. 查看清理效果
   python compare_bg.py
   
3. 合成最终图像
   python main.py
   （选择使用预清理的背景）
```

### 备选流程（需要精确控制）

```
1. 删除自动清理结果（如果存在）
   rm images/bg_cleaned.png
   
2. 运行主程序并手动清理
   python main.py
   （选择 y 进行手动清理）
   （交互式标记需要移除的区域）
```

## 效果

### 自动清理测试结果

- **检测像素**: 71,889 像素被识别为需要移除的区域
- **修复质量**: 使用Telea算法，边界保留良好
- **处理时间**: 约2-3秒（4624x3472分辨率）
- **输出文件**: `images/bg_cleaned.png` (约17MB)

### 优势

1. **完全自动化** - 无需人工标记，适合批量处理
2. **精确修复** - 保留背景纹理和颜色一致性
3. **灵活选择** - 支持自动/手动两种模式
4. **流程优化** - 清理结果可重用，提高效率

## 配置选项

### auto_clean.py 可调参数

```python
# 白色检测阈值
white_lower = np.array([0, 0, 200])      # 可降低亮度阈值
white_upper = np.array([180, 50, 255])    # 可提高饱和度上限

# 尺子检测参数
aspect_ratio_min = 3   # 最小纵横比
aspect_ratio_max = 50  # 最大纵横比
min_area = 500        # 最小面积阈值

# 修复参数
inpaint_radius = 10          # 修复半径
inpaint_method = INPAINT_TELEA  # 或 INPAINT_NS
```

### main.py 可调参数

```python
# 配置文件路径
BG_PATH = 'images/bg.png'              # 原始背景
POD_PATH = 'images/pod.jpg'            # 豆荚图
SEED_PATH = 'images/seed.jpg'          # 种子图
OUTPUT_PATH = 'result_final_v4.jpg'    # 输出文件
BG_CLEANED_PATH = 'images/bg_cleaned.png'  # 清理后的背景
```

## 后续改进建议

1. **深度学习检测** - 使用YOLO等目标检测模型自动识别尺子和牌子
2. **批处理支持** - 支持同时处理多张背景图
3. **GPU加速** - 使用CUDA加速大尺寸图像处理
4. **GUI界面** - 提供图形化界面简化操作
5. **更多算法** - 集成更多修复算法（如深度学习inpainting）

## 兼容性

- **Python**: 3.8+
- **依赖**: opencv-python, numpy
- **操作系统**: Windows/Linux/macOS
- **内存要求**: 建议4GB+（处理4K图像）
