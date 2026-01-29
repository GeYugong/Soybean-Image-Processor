# Soybean-Image-Processor

用于大豆（豆荚/种子）图像合成与背景清理的交互式工具。核心流程：
1) 背景清理（自动）
2) 选择豆荚区域并放置
3) 选择种子区域并放置
4) 输出合成结果

## 功能概览

- 背景清理
  - 自动：检测白色牌子 + 标尺
    - 白色牌子：单轮 inpaint
    - 标尺：从标尺右边开始裁切（保留右侧）
- 交互式抠取与放置
  - 从豆荚/种子图选择区域
  - 鼠标移动调整位置，滚轮缩放，左键确认
- 背景色差自动匹配（前景与背景色差补偿）

## 目录结构

```
.
├─ images/
│  ├─ bg/               # 背景图（多组）
│  ├─ pod/              # 豆荚图（多组）
│  └─ seed/             # 种子图（多组）
├─ main.py              # 交互式合成（支持参数化）
├─ auto_clean.py        # 自动清理背景
├─ batch_process.py     # 批量处理（按编号成组）
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

## 批量处理（多组）

三组图片分别放在以下目录，编号一致视为一组：

```
images/bg/   GY2025HHN-0001.jpg
images/pod/  GY2025-0001.jpg
images/seed/ GY-0001.jpg
```

批量处理：

```bash
python batch_process.py
```

输出目录：

```
outputs/
├─ bg_cleaned/   # 自动清理后的背景
└─ final/        # 人工放置后的最终合成
```

## 单组处理

### 自动清理背景

```bash
python auto_clean.py
```

### 交互式合成

```bash
python main.py
```

或参数化指定输入/输出：

```bash
python main.py --cleaned <cleaned_bg> --pod <pod_img> --seed <seed_img> --out <output>
```

## 输出文件

- `outputs/bg_cleaned/<编号>_bg_cleaned.jpg`
- `outputs/final/<编号>_final.jpg`
- `images/mask_debug.png`：自动清理掩码调试图
- `images/mask_white_expanded.png`：白色牌子扩张掩码（调试）

## 注意事项

- 自动清理会裁剪图像宽度（标尺左侧被裁掉）。
- 若裁剪过多/过少，可调整 `auto_clean.py` 中标尺检测阈值和裁剪偏移。

## 相关文档

- `CLEANING_GUIDE.md`
- `IMPROVEMENTS.md`
