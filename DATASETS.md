# 数据集与开源资源

## 标准测试图（data/standard/）

9 张经典公开测试图，来自 OpenCV 官方样本库与公开镜像，可自由用于教学：

| 文件 | 尺寸 | 特点 | 适用实验 |
| --- | --- | --- | --- |
| `lena.jpg` | 512x512 | 经典人像，平滑+细节 | 通用 |
| `baboon.jpg` | 512x512 | 纹理极丰富 | 频域、锐化、去噪 |
| `cameraman.png` | 256x256 | 经典灰度，边缘清晰 | 锐化、边缘 |
| `sudoku.png` | 558x563 | 含数字文字 | 复原（文字可读性） |
| `home.jpg` | 512x384 | 场景图 | 通用 |
| `messi5.jpg` | 548x342 | 人物场景 | 通用 |
| `fruits.jpg` | 512x480 | 彩色丰富 | 彩色处理 |
| `box.png` | 324x223 | 几何结构 | 边缘、频域 |
| `smarties.png` | 413x356 | 圆形色块 | 分割、彩色 |

## 人脸图像（data/raw/）

实验七使用 **10 张公开人脸数据集图像**（`face_01` ~ `face_12`），来源 [randomuser.me](https://randomuser.me)
公开肖像 API（CC 授权，非真实个人证件照）。

```bash
python experiments/exp7-skin-segmentation/code/skin_segmentation.py data/raw
```

## 本人证件照（data/myself/）

你本人的 6 张证件照已恢复到 `data/myself/`（从 Git 历史 `1b9b66c` 提取），仅供本地实验使用。
该目录已整体加入 `.gitignore`，**不会被提交到任何远端**，仓库公开后也不会泄露。

本地用它做实验七：

```bash
python experiments/exp7-skin-segmentation/code/skin_segmentation.py data/myself
```

`app.py` 默认读取 `data/raw/`（公开数据集）而非 `data/myself/`，
所以 Streamlit Cloud 上展示的始终是公开图像；只有你本地手动指定时才会用到本人照片。

## 隐私规则

真实的个人证件照**不入库**。`.gitignore` 已排除以下模式：

```
data/myself/                 ← 整个目录
data/raw/20*.JPG
data/raw/20*.jpg
data/raw/20*.jpeg
data/raw/20*.png
data/raw/id_*
data/raw/证件照*
```

如需在本地用自己的照片做实验，把文件放进 `data/myself/` 或 `data/raw/` 即可，Git 会自动忽略，不会被提交。
