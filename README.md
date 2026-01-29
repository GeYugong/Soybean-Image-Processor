# Soybean-Image-Processor

用于大豆（豆荚/种子）图像合成与背景清理的交互式工具。核心流程：
1) 背景清理（手动框选）
2) 选择豆荚区域并放置
3) 选择种子区域并放置
4) 输出合成结果

## 功能概览

- 背景清理（手动框选 + inpaint 修复）
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
├─ auto_clean.py        # 自动清理背景（可选）
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

### 运行时交互流程

- 程序启动后会询问**从第几组开始**（例如输入 5）
- 如果某组已经做过（有输出文件），会询问是否**覆盖重做**
- 每一组处理顺序：
  1) 打开背景图，手动框选要移除区域
  2) 打开豆荚图，框选并放置
  3) 打开种子图，框选并放置
  4) 保存结果

### 背景清理操作说明

1) 背景窗口弹出后，用鼠标左键拖拽画矩形，覆盖需要移除的物体（标尺/白牌等）。
2) 可以画多个矩形，逐个标记。
3) 按 `SPACE` 确认开始修复并进入下一步；按 `ESC` 取消本次清理。
4) 窗口按高度 900px 缩放显示，实际处理为原图尺寸。

### 输出目录

```
outputs/
├─ bg_cleaned/   # 手动清理后的背景
└─ final/        # 人工放置后的最终合成
```

## 单组处理

### 手动清理 + 合成

```bash
python main.py
```

或参数化指定输入/输出：

```bash
python main.py --bg <bg_img> --pod <pod_img> --seed <seed_img> --out <output> --clean-bg --cleaned-out <bg_cleaned>
```

## 输出文件

- `outputs/bg_cleaned/<编号>_bg_cleaned.jpg`
- `outputs/final/<编号>_final.jpg`

## 注意事项

- 批处理是完全交互式（每组都会弹窗）。
- 若想跳过背景清理，可去掉 `--clean-bg` 并直接使用已清理背景。

## 相关文档

- `CLEANING_GUIDE.md`
- `IMPROVEMENTS.md`
- `REEDIT_GUIDE.md`
