# DIP-Lab

《数字图像处理》（2026）课程实验仓库，含七个实验与统一的 Streamlit 展示平台。

- 学院：计算机科学与工程学院
- 任课教师：沃焱
- 实验与开发平台：MATLAB、OpenCV（C++ / Python / Java）

## 在线体验

本仓库已配置为可直接部署到 [Streamlit Community Cloud](https://share.streamlit.io)：

- 入口文件：`app.py`
- 依赖：`requirements.txt`（使用 `opencv-python-headless`，无需系统 GUI 库）
- 部署：在 Streamlit Cloud 选择本仓库、分支 `main`、主文件 `app.py` 即可

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开 http://localhost:8501 ，七个实验各占一个栏目，可上传图像并实时调节参数。

## 目录结构

```
DIP-Lab/
├── app.py                      Streamlit 展示平台（界面与调度，不含算法）
├── requirements.txt            依赖（opencv-python-headless 适配云端）
├── .streamlit/config.toml      云端主题配置
├── data/
│   ├── standard/               标准测试图（9 张，公开素材）
│   └── raw/                    人脸图像（公开数据集，证件照已 gitignore）
├── experiments/                七次实验
│   ├── exp1-histogram/         实验一 直方图均衡化与规定化
│   ├── exp2-gamma/             实验二 变换与伽马校正
│   ├── exp3-denoising/         实验三 噪声去除
│   ├── exp4-sharpening/        实验四 空间域锐化
│   ├── exp5-frequency-filter/  实验五 频率域低通与高通滤波
│   ├── exp6-restoration/       实验六 图像复原
│   └── exp7-skin-segmentation/ 实验七 人脸皮肤颜色分层
└── docs/                       课程原始文档与原理说明 PDF
```

每个实验目录统一采用三层结构：

```
expN-xxx/
├── code/           实现脚本（算法唯一来源，被 app.py 直接复用）
├── images/output/  脚本输出的归档结果
├── report/         实验报告
└── README.md       实验说明与运行方式
```

## 设计说明

`app.py` 不重复实现任何算法，它通过 `importlib` 加载 `experiments/expN-*/code/` 下的脚本并调用其中的函数，
同时用 `DIP_OUTPUT_DIR` 环境变量把实时产物重定向到系统临时目录，避免污染 `experiments/` 中的归档结果。
因此算法只维护一份，改脚本即改展示。

单独运行某个实验（结果写入该实验的 `images/output/`）：

```bash
python experiments/exp1-histogram/code/hist_equalization.py
python experiments/exp1-histogram/code/hist_equalization.py data/standard/lena.jpg
```

## 隐私说明

`data/raw/` 下的真实证件照已通过 `.gitignore` 排除（`20*.jpg`、`id_*`、`证件照*` 等规则），
实验七改用公开人脸数据集图像，仓库公开后不会泄露个人信息。
