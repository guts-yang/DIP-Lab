# 实验七：人脸皮肤颜色分层

## 实验内容

采用彩色图像分层方法，提取人脸（任务书提示：可自行准备证件照或自拍照）。

## 目录结构

```
exp7-skin-segmentation/
├── code/
│   └── skin_segmentation.py
├── images/              放入自备照片（jpg/png/bmp）
│   └── output/          脚本输出结果
└── report/
```

## 运行方式

```bash
cd code
python skin_segmentation.py [图像路径]
```

若不指定路径，脚本会自动在 `../images/` 下查找第一张照片；若都没有，则用内置合成示意图演示。
建议把自己的证件照或自拍照放到 `images/` 目录后再运行。

## 实现要点

三种传统颜色空间分层方法（不使用深度学习）：

- RGB 规则：`R>95, G>40, B>20, max-min>15, |R-G|>15, R>G, R>B`。
- YCbCr 范围模型：`77 <= Cb <= 127` 且 `133 <= Cr <= 173`。
- HSV 范围模型：OpenCV 中 `H in [0,25]`，`S in [30,170]`，`V >= 50`。

后处理：形态学开运算去噪点、闭运算填补空洞，再取最大连通域作为人脸候选区。
另提供三方法投票融合（至少两票认定为肤色），提升鲁棒性。

## 输出结果

| 文件 | 说明 |
| --- | --- |
| `01_mask_<method>.png` | 各方法肤色掩膜 |
| `02_overlay_<method>.png` | 掩膜与原图叠加 |
| `03_postprocessed_<method>.png` | 形态学后处理结果 |
| `04_face_candidate_<method>.png` | 最大连通域提取的人脸候选 |
| `masks_grid.png` / `overlay_grid.png` | 三种方法对比 |
| `05_fused_vote.png` / `06_fused_result.png` | 投票融合结果 |

## 报告建议

- 图 1 原图与三种颜色空间掩膜对比。
- 图 2 形态学后处理与最大连通域提取结果。
- 表 1 三种方法在不同光照/背景下的表现对比（可用多张照片测试）。
- 讨论：单一颜色模型的局限（光照敏感、类肤色背景干扰），以及融合策略的改进效果。
