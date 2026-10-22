# 实验四：图像的空间域锐化

## 实验内容

1. 采用拉普拉斯算子对图像进行锐化
2. 利用 Canny 边缘检测算子进行边缘检测

## 目录结构

```
exp4-sharpening/
├── code/
│   └── sharpening.py
├── images/
│   └── output/
└── report/
```

## 运行方式

```bash
cd code
python sharpening.py [图像路径]
```

## 实现要点

- 拉普拉斯算子是二阶微分算子，对灰度突变（边缘）响应强烈。
  - 4 邻域模板 `[0 1 0; 1 -4 1; 0 1 0]`
  - 8 邻域模板 `[1 1 1; 1 -8 1; 1 1 1]`
  - 模板中心为负，锐化时用原图减去拉普拉斯响应（脚本中 `f - c*Lap`）。
- 非锐化掩蔽：`f + amount * (f - blur(f))`，作为对照。
- Canny 流程：高斯平滑 → 计算梯度幅值与方向 → 非极大值抑制 → 双阈值滞后连接。
- 双阈值：高阈值确定强边缘，低阈值连接弱边缘，脚本对比 `(50,100)`、`(50,150)`、`(100,200)`。

## 输出结果

| 文件 | 说明 |
| --- | --- |
| `02_laplacian_response.png` | 拉普拉斯响应（绝对值拉伸显示） |
| `03_sharpen_laplacian4.png` | 4 邻域模板锐化 |
| `04_sharpen_laplacian8.png` | 8 邻域模板锐化 |
| `05_unsharp_mask.png` | 非锐化掩蔽 |
| `sharpen_compare.png` | 锐化方法横向对比 |
| `06_canny_*.png` | 各阈值 Canny 结果 |
| `canny_grid.png` | Canny 阈值对比拼接图 |
| `canny_vs_laplacian.png` | 拉普拉斯与 Canny 对照 |

## 报告建议

- 图 1 原图与拉普拉斯锐化结果对比；图 2 两种模板锐化效果差异。
- 图 3 不同双阈值的 Canny 边缘图，说明阈值对边缘连续性与噪声的影响。
- 表 1 不同阈值的边缘像素数对比。
