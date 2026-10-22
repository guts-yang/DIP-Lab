# 实验六：数字图像复原

> 底层原理与答辩问答：[PRINCIPLE.md](PRINCIPLE.md) ｜ [PDF 版](../../docs/principle/实验6-原理说明.pdf)

> **底层原理（答辩必看）**：[PRINCIPLE.md](PRINCIPLE.md) —— 图像复原的数学原理与公式推导，含 退化模型、逆滤波、维纳滤波，以及老师常问问题与标准回答。

## 实验内容

1. 对图像进行高斯模糊和运动模糊
2. 采用维纳滤波进行图像复原

## 目录结构

```
exp6-restoration/
├── code/
│   └── restoration.py
├── images/
│   └── output/
└── report/
```

## 运行方式

```bash
cd code
python restoration.py [图像路径]
```

## 实现要点

- 退化模型：`g(x,y) = h(x,y) * f(x,y) + n(x,y)`，频域为 `G = H·F + N`。
- 构造 PSF（点扩散函数）：
  - 高斯模糊：`cv2.GaussianBlur` 作用于冲激，得到高斯型 PSF。
  - 运动模糊：沿指定角度生成线状核并归一化。
- PSF 补零到图像尺寸后 `ifftshift`，使其中心对齐到 `(0,0)`，再与图像频谱相乘。
- 逆滤波：`F = G / H`，对 `|H| < eps` 处截断。对噪声极敏感，容易放大噪声。
- 维纳滤波：`F = [H* / (|H|^2 + K)] · G`，`K` 为噪声与信号功率比估计，能在去模糊与抑噪间折中。

## 输出结果

| 文件 | 说明 |
| --- | --- |
| `01_blurred_gaussian.png` / `01_blurred_motion.png` | 两种模糊结果 |
| `02_inverse_*.png` | 逆滤波复原 |
| `03_wiener_*.png` | 维纳滤波复原（不同 K） |
| `compare_*.png` | 原图/模糊/逆滤波/维纳 对比 |
| `wiener_k_compare_*.png` | 不同 K 值对比 |
| `psnr_report.txt` | PSNR 汇总 |

## 报告建议

- 图 1 原图、高斯模糊图、逆滤波结果、维纳滤波结果对比。
- 图 2 运动模糊及其复原结果。
- 图 3 模糊加噪情况下逆滤波与维纳滤波的对比，说明维纳滤波的抗噪优势。
- 表 1 不同 K 值下的 PSNR 对比，说明 K 的选取原则。
