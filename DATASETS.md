# 数据集与开源资源

## 当前状态

七个实验脚本已全部跑通。

- **已下载标准图**：`data/standard/` 下 9 张经典标准测试图，各实验默认自动读取。
- **已放入证件照**：`data/raw/` 下 6 张真实证件照，实验七默认读取。
- 不传参数时脚本自动优先用标准图/证件照，无需手动指定。

## 已下载的标准测试图（data/standard/）

共 9 张，来自 OpenCV 官方样本库与公开镜像，覆盖各实验需求：

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

各实验默认取目录下的第一张（`baboon.jpg`，纹理密集，频域效果最明显）。
如需换图，直接传路径：`python xxx.py ../../../../data/standard/lena.jpg`

## 各实验推荐图像

| 实验 | 推荐图像类型 | 说明 |
| --- | --- | --- |
| 一 直方图 | 偏暗、低对比度照片 | 均衡化前后差异明显 |
| 二 伽马校正 | 曝光不足或过曝照片 | 不同 gamma 参数效果差异大 |
| 三 去噪 | 平滑区域较多的灰度图 | 便于观察噪声与滤波效果 |
| 四 锐化 | 边缘丰富的图（建筑、纹理） | 便于对比 Canny 与拉普拉斯 |
| 五 频域滤波 | 含周期纹理/网纹的图 | 频谱中出现明显离散亮点 |
| 六 复原 | 文字、清晰边缘的图 | 模糊与复原对比直观 |
| 七 肤色分层 | 证件照、自拍照 | 任务书要求自备 |

## 经典标准测试图像（可直接下载）

数字图像处理课程最常用的标准图，多数已内置在 OpenCV / scikit-image 中：

- Lena、Barbara、Peppers、Cameraman、House、Jetplane、Lake、Livingroom、Pirate、Walkbridge、Woman Blonde、Woman Darkhair
- 经典数据集合集：[imageprocessingplace.com](https://www.imageprocessingplace.com/downloads_V3/root_downloads/image_databases.htm)
- USC-SIPI 图像数据库：[sipi.usc.edu/database](https://sipi.usc.edu/database/)（含 Misc、Aerials、Textures 等）

OpenCV 已内置部分，可直接调用：

```python
import cv2
img = cv2.imread(cv2.samples.findFile("lena.jpg"), cv2.IMREAD_GRAYSCALE)  # 需 opencv-python 含 samples
```

scikit-image 内置：

```python
from skimage import data
img = data.camera()      # Cameraman
img = data.astronaut()   # 彩色
img = data.brick()       # 纹理，适合实验五
```

## 公开数据集平台

- [Kaggle Datasets](https://www.kaggle.com/datasets) 搜索 `image denoising`、`image restoration`、`skin detection`
- [Papers with Code Datasets](https://paperswithcode.com/datasets) 按任务检索学术数据集
- [UCI Machine Learning Repository](https://archive.ics.uci.edu/) Skin Segmentation 数据集（肤色分类经典数据）

## 下载建议

1. 优先用 scikit-image / OpenCV 内置图，零配置最快。
2. 学术数据集注意许可协议，多数仅允许研究用途。
3. 下载后放入对应实验的 `images/` 目录（不要放 `images/output/`，该目录为脚本输出，会被覆盖）。
4. 大文件不要提交到 Git，`.gitignore` 已预留数据集忽略规则（默认注释），如需启用取消注释即可。

## 使用方式

```
cd experiments/exp1-histogram/code
python hist_equalization.py ../../exp1-histogram/images/你的图.jpg
```

实验七支持自动查找，把照片放进 `exp7-skin-segmentation/images/` 后直接运行即可。
