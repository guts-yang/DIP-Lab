# DIP-Lab

《数字图像处理》（2026）课程实验与课程设计仓库。

- 学院：计算机科学与工程学院
- 任课教师：沃焱
- 实验与开发平台：MATLAB、OpenCV（C++ / Python / Java）

## 目录结构

```
DIP-Lab/
├── README.md
├── requirements.txt
├── docs/                          课程原始文档（教师下发，仅参考勿改）
│   ├── task-and-rubric-2026.docx              课程设计任务书及评分标准
│   ├── lab-schedule-and-assessment-2026.pdf   实验及课程考核安排
│   ├── lab-report-template-2026.doc           实验报告模板
│   └── course-design-report-template-2026.doc 课程设计报告模板
├── experiments/                   七次实验
│   ├── exp1-histogram/            实验一 直方图均衡化与规定化
│   ├── exp2-gamma/                实验二 变换与伽马校正
│   ├── exp3-denoising/            实验三 噪声去除
│   ├── exp4-sharpening/           实验四 空间域锐化
│   ├── exp5-frequency-filter/     实验五 频率域低通与高通滤波
│   ├── exp6-restoration/          实验六 图像复原
│   └── exp7-skin-segmentation/    实验七 人脸皮肤颜色分层
└── course-design/                 课程设计（大作业）
    ├── code/
    ├── images/
    ├── report/
    └── slides/
```

每个实验目录统一采用三层结构：

```
expN-xxx/
├── code/           实现脚本
├── images/         输入图像（自备）
│   └── output/     脚本输出结果
├── report/         实验报告
└── README.md       实验说明与运行方式
```

## 快速开始

```bash
pip install -r requirements.txt

# 以实验一为例
cd experiments/exp1-histogram/code
python hist_equalization.py            # 内置合成图像演示
python hist_equalization.py ~/xxx.jpg  # 使用自己的图像
```

所有脚本均支持传入图像路径；不传时使用内置合成图像，可直接运行验证。
结果统一输出到各实验的 `images/output/`，报告素材直接取用即可。

## 实验概览

| 实验 | 目录 | 内容 |
| --- | --- | --- |
| 一 | [exp1-histogram](experiments/exp1-histogram) | 图像读取及色彩、亮度、对比度变化；直方图均衡化与规定化 |
| 二 | [exp2-gamma](experiments/exp2-gamma) | 图像变换；不同参数的伽马校正 |
| 三 | [exp3-denoising](experiments/exp3-denoising) | 加高斯/椒盐噪声；中值滤波与统计排序滤波去噪 |
| 四 | [exp4-sharpening](experiments/exp4-sharpening) | 拉普拉斯锐化；Canny 边缘检测 |
| 五 | [exp5-frequency-filter](experiments/exp5-frequency-filter) | FFT；理想/巴特沃斯/高斯低通与高通滤波 |
| 六 | [exp6-restoration](experiments/exp6-restoration) | 高斯与运动模糊建模；逆滤波与维纳滤波复原 |
| 七 | [exp7-skin-segmentation](experiments/exp7-skin-segmentation) | RGB/YCbCr/HSV 肤色分层与人脸提取 |

## 考核与进度

成绩构成：实验 20% + 雨课堂学习与作业 20% + 课堂考勤 10% + 终结性课程论文（大作业）50%，均为百分制。

- 实验检查：暂定第 16 周，需准备实验报告（打印版）、程序源码、笔记本电脑
- 课程设计答辩：暂定第 17 周，需准备报告、源程序、可执行程序、答辩 PPT
- 分组选题：3 人一组，12 周前填好分组与选题表

详见 [docs/lab-schedule-and-assessment-2026.pdf](docs/lab-schedule-and-assessment-2026.pdf)。

## 课程设计

3 人一组，每人独立完成一份报告。选题方向 6 选 1 或自选题目（仅限传统方法，不使用深度学习）：

1. 手机文档扫描与可读性增强系统
2. 老照片数字修复与彩色增强系统
3. 低照度彩色监控图像增强与复原系统
4. 人脸美颜相机——肤色保护与细节增强
5. 医学影像综合增强与伪彩色显示系统
6. 工业产品表面缺陷检测预处理系统

评分标准：正确性 20%、设计合理性 20%、程序功能 20%、运行及答辩 20%、大作业报告 20%。

详见 [docs/task-and-rubric-2026.docx](docs/task-and-rubric-2026.docx)。

## 报告模板

- 实验报告：[docs/lab-report-template-2026.doc](docs/lab-report-template-2026.doc)
- 课程设计报告：[docs/course-design-report-template-2026.doc](docs/course-design-report-template-2026.doc)

格式要求：正文两端对齐、首行缩进 2 字符、行距固定值 20 磅；图号图名在图下方居中，表号表名在表上方居中；公式编号右对齐。

## 参考资料

1. 数字图像处理（第四版），R.C. Gonzalez，阮秋琦 等译，电子工业出版社，2023.11
2. 数字图像处理，K.R. Castleman，朱志刚 等译，电子工业出版社，2021
