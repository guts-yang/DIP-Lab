# 实验五：频率域低通和高通滤波

> **底层原理（答辩必看）**：[PRINCIPLE.md](PRINCIPLE.md) —— 频率域滤波的数学原理与公式推导，含 傅里叶变换、卷积定理、三类滤波器，以及老师常问问题与标准回答。

## 实验内容

1. 对图像进行 FFT 变换
2. 选择某种低通滤波器进行低通滤波
3. 选择某种高通滤波器进行高通滤波

## 目录结构

```
exp5-frequency-filter/
├── code/
│   └── frequency_filter.py
├── images/
│   └── output/
└── report/
```

## 运行方式

```bash
cd code
python frequency_filter.py [图像路径]
```

## 实现要点

- `numpy.fft.fft2` 做二维傅里叶变换，`fftshift` 将零频移到中心，取 `20*log(|F|+1)` 做对数拉伸以便显示频谱。
- 三类滤波器（截止频率 `D0`，巴特沃斯阶数 `n=2`）：
  - 理想（ideal）：`D(u,v) <= D0` 置 1，其余置 0，会产生振铃效应。
  - 巴特沃斯（butterworth）：`1 / (1 + (D/D0)^(2n))`，过渡平滑，阶数越高越接近理想。
  - 高斯（gaussian）：`exp(-D^2 / (2*D0^2))`，无振铃。
- 高通滤波器由 `H_hp = 1 - H_lp` 得到。
- 滤波流程：`FFT → fftshift → 乘 H → ifftshift → IFFT → 取模`。

## 输出结果

| 文件 | 说明 |
| --- | --- |
| `02_spectrum.png` | 中心化对数频谱 |
| `03_lowpass_<type>.png` | 三类低通滤波结果 |
| `04_highpass_<type>.png` | 三类高通滤波结果 |
| `lowpass_grid.png` / `highpass_grid.png` | 低通/高通横向对比 |
| `filters_grid.png` | 滤波器模板可视化 |
| `butterworth_d0_compare.png` | 不同截止频率效果 |
| `spectrum_vs_filters.png` | 原图、频谱、滤波器、结果综合图 |

## 报告建议

- 图 1 原图与频谱图，说明频谱中亮线的方向与图像纹理方向的关系。
- 图 2 三类低通滤波器结果，重点对比理想低通的振铃效应。
- 图 3 三类高通滤波器结果（边缘增强效果）。
- 表 1 不同截止频率 `D0` 下的平滑程度对比。
