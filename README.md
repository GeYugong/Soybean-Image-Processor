# Soybean-Image-Processor

🌱 **大豆图像处理工具** - 用于大豆（豆荚/种子）图像合成与背景清理的交互式工具。

流程完全以人工操作为核心，保证结果可控：
1) 清理背景（手动框选）
2) 选择豆荚区域并放置
3) 选择种子区域并放置
4) 输出最终合成图

---

## 📥 下载使用

### 方式一：下载发行版（推荐，无需安装 Python）

1. 前往 [Releases 页面](https://github.com/GeYugong/Soybean-Image-Processor/releases)
2. 下载最新版本的 `Soybean-Tool.zip`
3. 解压后双击 `batch_process.exe` 即可运行

### 方式二：从源码运行

```bash
git clone https://github.com/GeYugong/Soybean-Image-Processor.git
cd Soybean-Image-Processor
pip install opencv-python numpy
python batch_process.py
```

---

## ✨ 功能简介

- **背景清理（手动）**
  - 在背景图上框选要移除的对象（标尺、标牌等）
  - 单轮 inpaint 修复
  - 清理完成后可选竖线裁切（保留右侧）
- **交互式放置**
  - 从豆荚/种子图中框选区域
  - 鼠标移动调整位置，滚轮缩放，左键确认
- **颜色校正**
  - 框选植株本体颜色作为参考
  - 自动校正豆荚/种子色差

---

## 📁 目录结构

```
.
├─ images/
│  ├─ bg/               # 背景图（植株）
│  ├─ pod/              # 豆荚图
│  └─ seed/             # 种子图
├─ outputs/
│  ├─ bg_cleaned/       # 清理后的背景
│  └─ final/            # 最终合成图
├─ main.py              # 交互式合成（支持参数化）
├─ batch_process.py     # 批处理（按编号成组）
├─ batch_tool.py        # 打包工具
├─ auto_clean.py        # 自动清理（可选）
└─ compare_bg.py        # 清理前后对比
```

---

## 🖥️ 环境依赖

- Python 3.8+
- opencv-python
- numpy

安装：

```bash
pip install opencv-python numpy
```

---

## 🚀 批量处理（多组）

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

### ⌨️ 快捷键说明

| 按键 | 功能 |
|------|------|
| `SPACE` / `ENTER` | 确认当前步骤 |
| `ESC` | 退出/取消当前窗口 |
| `R` | 重做当前步骤 |
| `S` | 跳过当前步骤 |
| `右键` | 撤销上一个框选 |
| `滚轮` | 缩放（放置阶段） |
| `左键点击` | 确认放置位置 |

### 可选裁切
清理结束后会弹出裁切窗口：
- 鼠标移动显示竖线
- **左键点击**确认裁切（保留右侧）
- **SPACE**跳过裁切

### 📤 输出目录
```
outputs/
├─ bg_cleaned/   # 清理后的背景
└─ final/        # 最终合成图
```

---

## 🔧 单组处理

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

## ⚠️ 注意事项

- 批处理是全交互式，每组都会弹窗
- 需要重做某一组时，参考 `REEDIT_GUIDE.md`
- 使用发行版（exe）无需安装 Python 环境

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [STEP_BY_STEP.md](STEP_BY_STEP.md) | 新手操作流程 |
| [CLEANING_GUIDE.md](CLEANING_GUIDE.md) | 清理细节与排错 |
| [REEDIT_GUIDE.md](REEDIT_GUIDE.md) | 重做说明 |
| [IMPROVEMENTS.md](IMPROVEMENTS.md) | 变更摘要 |

---

## 📝 License

MIT License
