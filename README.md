# Soybean-Image-Processor

用于大豆（豆荚/种子）图像合成与背景清理的交互式小工具。核心流程：
1) 背景清理（可选，自动或手动）
2) 选择豆荚区域并放置
3) 选择种子区域并放置
4) 输出合成结果

## 功能概览

- 背景清理
  - 手动：鼠标框选需要移除的物体，OpenCV inpainting 修复
  - 自动：检测白色牌子 + 标尺
    - 白色牌子：单轮 inpaint
    - 标尺：直接裁掉（从标尺右边往右保留）
- 交互式抠取与放置
  - 从 `pod.jpg`、`seed.jpg` 选择区域
  - 鼠标移动调整位置，滚轮缩放，左键确认
- 背景色差自动匹配（前景与背景色差补偿）

## 目录结构

```
.
├─ images/
│  ├─ bg.png            # 原始背景
│  ├─ bg_cleaned.png    # 清理后的背景（自动生成）
│  ├─ pod.jpg           # 豆荚图
│  └─ seed.jpg          # 种子图
├─ main.py              # 主流程（交互式）
├─ auto_clean.py        # 自动清理背景（可选）
├─ compare_bg.py        # 清理前后对比
├─ CLEANING_GUIDE.md    # 清理算法与调参说明
├─ IMPROVEMENTS.md      # 功能改进记录
└─ README.md
```

## 环境依赖

- Python 3.8+
- 依赖包：opencv-python, numpy

安装示例：

```bash
pip install opencv-python numpy
```

## 快速开始（推荐流程）

1) 自动清理背景（生成 `images/bg_cleaned.png`）

```bash
python auto_clean.py
```

2) 运行主程序进行抠取与放置

```bash
python main.py
```

3) 可选：查看清理前后对比图

```bash
python compare_bg.py
```

## 使用说明

### 主程序：`python main.py`

运行后流程如下：

1. 若检测到 `images/bg_cleaned.png`，会询问是否使用清理后的背景
2. 若不使用清理背景，会询问是否进行手动清理
3. 依次选择豆荚与种子区域并放置
4. 输出合成结果：`result_final_v4.jpg`

#### 交互说明

- 背景清理窗口
  - 鼠标左键拖拽：画矩形标记需要移除的区域
  - `SPACE`：确认并开始修复
  - `ESC`：取消
- 区域选择窗口（豆荚/种子）
  - 鼠标拖拽：选择区域
  - `SPACE` / `ENTER`：确认
- 位置调整窗口
  - 鼠标移动：调整位置
  - 鼠标滚轮：缩放（每次 5%）
  - 鼠标左键：确认并保存位置
  - `ESC`：退出不放置

### 自动清理：`python auto_clean.py`

当前自动清理策略：
- **白色牌子**：单轮 inpaint 修复
- **标尺**：直接裁掉（从标尺右边往右保留）

手动预览模式：

```bash
python auto_clean.py --manual
```

会显示检测区域预览，确认后执行修复。

### 清理对比：`python compare_bg.py`

将原始与清理后的背景并排显示，并输出对比图 `bg_comparison.jpg`。

## 输出文件

- `images/bg_cleaned.png`：清理后的背景（自动生成）
- `result_final_v4.jpg`：最终合成结果
- `bg_comparison.jpg`：清理前后对比图
- `images/mask_debug.png`：自动清理时的掩码调试图
- `images/mask_white_expanded.png`：白色牌子扩张掩码（调试）

## 注意事项

- **自动清理会裁剪图像宽度**：标尺右边保留，左侧全部裁掉。
- 若裁剪过多/过少，可调整 `auto_clean.py` 中的 `crop_pad` 或标尺检测阈值。

## 配置入口

主流程的路径配置在 `main.py` 顶部：

```python
BG_PATH = 'images/bg.png'
POD_PATH = 'images/pod.jpg'
SEED_PATH = 'images/seed.jpg'
OUTPUT_PATH = 'result_final_v4.jpg'
BG_CLEANED_PATH = 'images/bg_cleaned.png'
```

自动清理参数与调参建议请参考 `CLEANING_GUIDE.md`。

## 常见问题

- 找不到图片
  - 请确认 `images/` 下存在 `bg.png`、`pod.jpg`、`seed.jpg`
- 自动清理不理想
  - 尝试 `python auto_clean.py --manual` 先预览
  - 参考 `CLEANING_GUIDE.md` 调整阈值
- 窗口显示过大/过小
  - 程序会按 900px 高度缩放显示，实际处理为原图尺寸

## 相关文档

- `CLEANING_GUIDE.md`：清理算法、调参和排错说明
- `IMPROVEMENTS.md`：功能改进摘要
