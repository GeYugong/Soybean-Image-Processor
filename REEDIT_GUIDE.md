# 重新编辑指南

当你在批处理过程中发现某一组图片效果不满意，可以按下面方式重新编辑：

## 方法一：只重做某一个编号（推荐）

1) 删除这组旧结果（可选）：
```
outputs/bg_cleaned/<编号>_bg_cleaned.jpg
outputs/final/<编号>_final.jpg
```

2) 仅处理指定编号：
```
python batch_process.py --only-id <编号>
```

示例：
```
python batch_process.py --only-id 0012
```

## 方法二：重做多个指定编号

```
python batch_process.py --ids 0003,0007,0011
```

## 方法三：从某个编号继续（跳过之前已完成的）

```
python batch_process.py --start-id 0010
```

## 方法四：强制覆盖已完成结果

如果不删除旧文件，也可以强制覆盖：

```
python batch_process.py --force
```

## 程序内解决方案（已实现）

- `--only-id`：仅重做单个编号
- `--ids`：重做多个编号
- `--start-id`：从指定编号开始继续
- `--force`：强制覆盖已完成结果

使用这些参数可以让你快速回到“不满意的那一组”并重新手动框选背景、豆荚和种子。
