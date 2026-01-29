# Soybean-Image-Processor

用于大豆（豆荚/种子）图像合成与背景清理的交互式工具。流程完全以人工操作为核心，保证结果可控：
1) 清理背景（手动框选）
2) 选择豆荚区域并放置
3) 选择种子区域并放置
4) 输出最终合成图

---

## 功能简介

- **背景清理（手动）**
  - 在背景图上框选要移除的对象
  - 单轮 inpaint 修复
  - 清理完成后可选竖线裁切（保留右侧）
- **交互式放置**
  - 从豆荚/种子图中框选区域
  - 鼠标移动调整位置，滚轮缩放，左键确认

---

## 目录结构

```
.
├─ images/
│  ├─ bg/               # 背景图（多组）
│  ├─ pod/              # 豆荚图（多组）
│  └─ seed/             # 种子图（多组）
├─ main.py              # 交互式合成（支持参数化）
├─ auto_clean.py        # 自动清理（可选）
├─ batch_process.py     # 批处理（按编号成组）
├─ compare_bg.py        # 清理前后对比
├─ CLEANING_GUIDE.md
├─ IMPROVEMENTS.md
├─ REEDIT_GUIDE.md
└─ README.md
```

---

## 环境依赖

- Python 3.8+
- opencv-python
- numpy

安装：

```bash
pip install opencv-python numpy
```

---

## 批量处理（多组）

三组图片分别放在以下目录，文件名中 **4 位编号**一致视为一组：

```
images/bg/   GY2025HHN-0001.jpg
images/pod/  GY2025-0001.jpg
images/seed/ GY-0001.jpg
```

运行：
```bash
python batch_process.py
```

### 每组流程
1) 背景窗口：框选需要移除区域
2) 豆荚窗口：框选并放置
3) 种子窗口：框选并放置
4) 保存输出

### 植株颜色参考（新增）
在放置豆荚/种子前，会先弹出背景图，请你框选一块“植株本体颜色”区域。
该颜色用于校正豆荚/籽粒色差，使其更接近单株颜色。

### 背景清理操作
- **拖拽鼠标**：画矩形
- **SPACE**：确认修复
- **ESC**：取消本次清理

### 可选裁切
清理结束后会弹出裁切窗口：
- 鼠标移动显示竖线
- **左键点击**确认裁切（保留右侧）
- **SPACE**跳过裁切

### 输出目录
```
outputs/
├─ bg_cleaned/   # 清理后的背景
└─ final/        # 最终合成图
```

---

## 单组处理

```bash
python main.py
```

或指定路径：

```bash
python main.py \
  --bg <bg_img> \
  --pod <pod_img> \
  --seed <seed_img> \
  --out <output> \
  --clean-bg \
  --cleaned-out <bg_cleaned>
```

---

## 注意事项

- 批处理是全交互式，每组都会弹窗。
- 需要重做某一组时，参考 `REEDIT_GUIDE.md`。

---

## 相关文档

- `CLEANING_GUIDE.md` — 清理细节与排错
- `IMPROVEMENTS.md` — 变更摘要
- `REEDIT_GUIDE.md` — 重做说明
- `STEP_BY_STEP.md` — 新手操作流程
