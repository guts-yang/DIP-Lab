# 实验二：数字图像变换与伽马校正

## 实验内容

选择不同的参数完成伽马校正。

## 目录结构

```
exp2-gamma/
├── code/
│   └── gamma_correction.py
├── images/
│   └── output/
└── report/
```

## 运行方式

```bash
cd code
python gamma_correction.py [图像路径]
```

## 实现要点

- 幂律变换 `s = c * r^gamma`，脚本默认取 `c = 1`。
- `gamma < 1`：扩展暗部、压缩亮部，图像整体变亮。
- `gamma = 1`：恒等变换。
- `gamma > 1`：压缩暗部、扩展亮部，图像整体变暗。
- 附带对数变换 `s = c * log(1 + r)` 与反色变换 `s = 255 - r` 作对照。

脚本默认对比 `gamma = 0.4, 0.6, 1.0, 1.5, 2.2, 3.0`。

## 输出结果

| 文件 | 说明 |
| --- | --- |
| `01_source.png` | 原图 |
| `02_negative.png` | 反色变换 |
| `03_log.png` | 对数变换 |
| `gamma_*.png` | 单个 gamma 值的结果 |
| `gamma_grid.png` | 各 gamma 值拼接对比 |
| `gamma_curves.png` | 伽马变换曲线 |

## 报告建议

- 图 1 不同 gamma 参数的校正结果拼接图。
- 图 2 伽马变换曲线簇，说明参数对灰度映射的影响。
- 表 1 不同 gamma 下图像均值/方差等统计指标对比。
