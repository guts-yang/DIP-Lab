# 实验一：数字图像读取及色彩、亮度、对比度变化

## 实验内容

1. 完成直方图均衡化
2. 完成直方图规定化

## 目录结构

```
exp1-histogram/
├── code/
│   └── hist_equalization.py    实现脚本
├── images/                     输入图像（自备）
│   └── output/                 脚本输出结果
└── report/                     实验报告（按模板撰写）
```

## 运行方式

```bash
pip install opencv-python numpy matplotlib
cd code
python hist_equalization.py            # 使用内置合成图像演示
python hist_equalization.py <图像路径>  # 使用自己的图像
```

## 实现要点

- 亮度/对比度调整：线性变换 `g = alpha * f + beta`，`alpha` 控制对比度，`beta` 控制亮度。
- 直方图均衡化：用累积分布函数 CDF 做灰度映射，`cv2.equalizeHist`。
- 直方图规定化：分别计算源图与参考图的 CDF，对源图每个灰度级在参考 CDF 中查找最接近的灰度级，构造查找表 LUT 映射。

## 输出结果

| 文件 | 说明 |
| --- | --- |
| `01_source.png` | 原图 |
| `02_brightness_beta50.png` | 亮度提升 |
| `03_contrast_alpha18.png` | 对比度增强 |
| `04_equalized.png` | 直方图均衡化结果 |
| `05_reference.png` | 规定化参考图 |
| `06_matched.png` | 直方图规定化结果 |
| `histograms.png` | 三者直方图对比 |
| `compare_*.png` | 横向拼接对比图 |

## 报告建议

- 图 1 原图及其直方图；图 2 均衡化结果及其直方图；图 3 规定化结果及其直方图。
- 对比均衡化与规定化的差异：均衡化得到近似均匀直方图，规定化使结果直方图趋近给定参考分布。
