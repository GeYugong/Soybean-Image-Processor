# 程序改进总结

## 最新改动（2026-01）

- **自动清理逻辑简化**
  - 白色牌子：只保留一个最大连通域，单轮 inpaint
  - 标尺：不再 inpaint，直接裁切标尺右边界以左区域
- **性能优化**
  - 去除多轮 inpaint，速度显著提升
- **输出行为变化**
  - `auto_clean.py` 输出图像宽度会变小（裁掉标尺左侧）

## 现有文件

1. **auto_clean.py**
   - 自动清理背景（白牌单轮 inpaint + 标尺裁切）
2. **compare_bg.py**
   - 清理前后对比
3. **CLEANING_GUIDE.md**
   - 清理流程与参数说明
4. **images/bg_cleaned.png**
   - 自动清理生成的背景图

## 关键实现点（auto_clean.py）

- 白色牌子检测（HSV + 连通域）
- 标尺检测（左侧、纵向、暗像素占比）
- 白牌单轮 Telea inpaint
- 标尺区域直接裁切（保持右侧内容）

## 推荐流程

```
python auto_clean.py
python compare_bg.py
python main.py
```
