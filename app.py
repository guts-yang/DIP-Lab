"""数字图像处理实验统一展示平台（Streamlit）。

七个实验各自一个栏目，支持上传图像实时处理。
每个栏目的算法直接复用 experiments/expN-*/code/ 下的核心脚本，
本文件只负责界面与调度，不重复实现算法。

本地运行：
    streamlit run app.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

# 输出目录接管：设置该环境变量后，各实验脚本会把结果写到实时目录，
# 而不会覆盖 experiments/ 下的归档结果。
os.environ.setdefault("MPLBACKEND", "Agg")
_RUNTIME = Path(tempfile.gettempdir()) / "dip_runtime"
_RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ["DIP_OUTPUT_DIR"] = str(_RUNTIME)

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import cv2  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import numpy as np  # noqa: E402
import streamlit as st  # noqa: E402
from matplotlib import pyplot as plt  # noqa: E402

# Linux 容器缺少中文字体时静默回退，避免绘图抛错
plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "DejaVu Sans", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

EXP = {
    "exp1": ROOT / "experiments" / "exp1-histogram" / "code",
    "exp2": ROOT / "experiments" / "exp2-gamma" / "code",
    "exp3": ROOT / "experiments" / "exp3-denoising" / "code",
    "exp4": ROOT / "experiments" / "exp4-sharpening" / "code",
    "exp5": ROOT / "experiments" / "exp5-frequency-filter" / "code",
    "exp6": ROOT / "experiments" / "exp6-restoration" / "code",
    "exp7": ROOT / "experiments" / "exp7-skin-segmentation" / "code",
}
for p in EXP.values():
    sys.path.insert(0, str(p))

STANDARD_DIR = ROOT / "data" / "standard"
RAW_DIR = ROOT / "data" / "raw"

st.set_page_config(page_title="数字图像处理实验平台", layout="wide")


def load_mod(name: str, script: str):
    """导入实验脚本，并把其输出目录重定向到独立的实时目录。"""
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, EXP[name] / script)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    mod.OUTPUT_DIR = str(_RUNTIME / name)
    os.makedirs(mod.OUTPUT_DIR, exist_ok=True)
    return mod


@st.cache_resource
def mods():
    return {
        "exp1": load_mod("exp1", "hist_equalization.py"),
        "exp2": load_mod("exp2", "gamma_correction.py"),
        "exp3": load_mod("exp3", "denoising.py"),
        "exp4": load_mod("exp4", "sharpening.py"),
        "exp5": load_mod("exp5", "frequency_filter.py"),
        "exp6": load_mod("exp6", "restoration.py"),
        "exp7": load_mod("exp7", "skin_segmentation.py"),
    }


M = mods()


def to_bgr(upload) -> np.ndarray:
    """把上传文件解码为 BGR 图。"""
    data = np.frombuffer(upload.read(), np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码该图像")
    return img


def gray(upload) -> np.ndarray:
    bgr = to_bgr(upload)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)


def default_gray(mod) -> np.ndarray:
    """无上传时使用标准测试图。"""
    files = sorted(STANDARD_DIR.glob("*.[jp][pn]g")) + sorted(STANDARD_DIR.glob("*.JPG"))
    if files:
        img = cv2.imread(str(files[0]), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            return img
    return mod.make_demo_image()


def default_bgr(mod) -> np.ndarray:
    files = sorted(RAW_DIR.glob("*.jpg")) + sorted(RAW_DIR.glob("*.JPG"))
    if files:
        img = cv2.imread(str(files[0]))
        if img is not None:
            return img
    return mod.make_demo_image()


def show(img, caption: str = ""):
    """统一显示：BGR 转 RGB 后交给 Streamlit。"""
    if img.ndim == 2:
        st.image(img, caption=caption, use_container_width=True, clamp=True)
    else:
        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption=caption, use_container_width=True)


def grid(images: list, cols: int = 3):
    for i in range(0, len(images), cols):
        row = st.columns(cols)
        for c, (img, cap) in zip(row, images[i : i + cols]):
            with c:
                show(img, cap)


PRINCIPLE = {
    "exp1": "灰度变换 g=αf+β；均衡化把直方图展平到 0-255 提升对比度；规定化把分布匹配到参考直方图。",
    "exp2": "幂律变换 s=c·r^γ。γ<1 提亮暗部，γ>1 压暗；配合反色、对数变换。",
    "exp3": "排序统计滤波：中值抑椒盐、最大值抑胡椒、最小值抑盐粒、中点抑高斯、修正阿尔法均值应对混合噪声。",
    "exp4": "二阶导数拉普拉斯锐化（4/8邻域）、非锐化掩蔽；Canny 梯度边缘检测（双阈值）。",
    "exp5": "频域滤波：理想/巴特沃斯/高斯三类低通与高通。理想有振铃，高斯最柔和。",
    "exp6": "退化模型 g=Hf+n。逆滤波对噪声极敏感；维纳滤波最小均方误差，抗噪稳健。",
    "exp7": "彩色分层：RGB 规则、YCbCr 椭圆模型、HSV 范围模型，形态学后处理 + 投票融合。",
}

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["实验一 直方图", "实验二 伽马变换", "实验三 噪声去除", "实验四 锐化",
     "实验五 频域滤波", "实验六 图像复原", "实验七 肤色分割"]
)

# ---------------------------------------------------------------- 实验一
with tab1:
    st.subheader("实验一：数字图像读取及色彩、亮度、对比度变化")
    st.caption(PRINCIPLE["exp1"])
    m = M["exp1"]
    up = st.file_uploader("上传图像（可选，留空用标准图）", type=["jpg", "png", "jpeg", "bmp"], key="u1")
    src = gray(up) if up else default_gray(m)
    c1, c2 = st.columns(2)
    alpha = c1.slider("对比度 α", 0.2, 3.0, 1.8, 0.1)
    beta = c2.slider("亮度 β", -100, 100, 50, 5)

    adj = m.adjust_brightness_contrast(src, alpha, beta)
    eq = m.equalize_histogram(src)
    ref = m.make_reference_histogram()
    mat = m.histogram_matching(src, ref)

    grid([(src, "原图"), (adj, f"α={alpha}, β={beta}"), (eq, "均衡化"), (mat, "规定化")], 4)
    fig, ax = plt.subplots(1, 3, figsize=(12, 3))
    for a, (t, im) in zip(ax, [("原图", src), ("均衡化", eq), ("规定化", mat)]):
        a.hist(im.flatten(), bins=256, range=(0, 256), color="steelblue")
        a.set_title(t)
        a.set_xlim(0, 255)
    st.pyplot(fig)

# ---------------------------------------------------------------- 实验二
with tab2:
    st.subheader("实验二：数字图像变换与伽马校正")
    st.caption(PRINCIPLE["exp2"])
    m = M["exp2"]
    up = st.file_uploader("上传图像（可选）", type=["jpg", "png", "jpeg", "bmp"], key="u2")
    src = gray(up) if up else default_gray(m)
    gamma = st.slider("γ（伽马值）", 0.1, 4.0, 1.0, 0.1)
    c = st.slider("常数 c", 0.2, 3.0, 1.0, 0.1)

    grid([
        (src, "原图"),
        (m.gamma_transform(src, gamma, c), f"γ={gamma}, c={c}"),
        (m.negative_transform(src), "反色"),
        (m.log_transform(src), "对数变换"),
    ], 4)
    if st.button("查看伽马曲线族", key="b2"):
        m.OUTPUT_DIR = str(_RUNTIME / "exp2")
        m.plot_gamma_curves()
        show(cv2.imread(str(_RUNTIME / "exp2" / "gamma_curves.png")), "幂律变换曲线")

# ---------------------------------------------------------------- 实验三
with tab3:
    st.subheader("实验三：噪声去除")
    st.caption(PRINCIPLE["exp3"])
    m = M["exp3"]
    up = st.file_uploader("上传图像（可选）", type=["jpg", "png", "jpeg", "bmp"], key="u3")
    src = gray(up) if up else default_gray(m)
    ntype = st.selectbox("噪声类型", ["gaussian 高斯", "salt_pepper 椒盐", "mixed 混合"])
    sigma = st.slider("高斯噪声 σ", 5, 60, 25, 5)
    amount = st.slider("椒盐噪声比例", 0.01, 0.20, 0.05, 0.01)
    ksize = st.selectbox("滤波窗口", [3, 5], index=0)

    if ntype.startswith("gaussian"):
        noisy = m.add_gaussian_noise(src, sigma=sigma)
    elif ntype.startswith("salt"):
        noisy = m.add_salt_pepper_noise(src, amount=amount)
    else:
        noisy = m.add_salt_pepper_noise(m.add_gaussian_noise(src, sigma=sigma), amount=amount)

    res = {
        "中值": m.median_filter(noisy, ksize),
        "最大值": m.max_filter(noisy, ksize),
        "最小值": m.min_filter(noisy, ksize),
        "中点": m.midpoint_filter(noisy, ksize),
        "修正阿尔法均值": m.alpha_trimmed_mean_filter(noisy, ksize, 2),
    }
    grid([(src, "原图"), (noisy, f"加噪 {m.psnr(src, noisy):.2f} dB")] + list(res.items()), 4)
    st.dataframe(
        {"方法": ["加噪图"] + list(res.keys()),
         "PSNR(dB)": [f"{m.psnr(src, noisy):.2f}"] + [f"{m.psnr(src, v):.2f}" for v in res.values()]},
        hide_index=True,
    )

# ---------------------------------------------------------------- 实验四
with tab4:
    st.subheader("实验四：图像的空间域锐化")
    st.caption(PRINCIPLE["exp4"])
    m = M["exp4"]
    up = st.file_uploader("上传图像（可选）", type=["jpg", "png", "jpeg", "bmp"], key="u4")
    src = gray(up) if up else default_gray(m)
    c1, c2 = st.columns(2)
    kt = c1.selectbox("拉普拉斯模板", ["4", "8"])
    strength = c2.slider("锐化强度 c", 0.2, 3.0, 1.0, 0.1)
    t1 = st.slider("Canny 低阈值", 10, 200, 50, 10)
    t2 = st.slider("Canny 高阈值", 20, 300, 150, 10)

    grid([
        (src, "原图"),
        (m.laplacian_sharpen(src, kt, strength), f"拉普拉斯 {kt}邻域 c={strength}"),
        (m.unsharp_mask(src, 5, 1.5), "非锐化掩蔽"),
        (m.canny_edges(src, t1, max(t2, t1 + 1)), f"Canny [{t1},{t2}]"),
    ], 4)

# ---------------------------------------------------------------- 实验五
with tab5:
    st.subheader("实验五：频率域低通与高通滤波")
    st.caption(PRINCIPLE["exp5"])
    m = M["exp5"]
    up = st.file_uploader("上传图像（可选）", type=["jpg", "png", "jpeg", "bmp"], key="u5")
    src = cv2.resize(gray(up) if up else default_gray(m), (400, 400))
    d0 = st.slider("截止频率 D0", 5, 150, 40, 5)
    ftype = st.selectbox("滤波器类型", ["ideal 理想", "butterworth 巴特沃斯", "gaussian 高斯"])
    ft = ftype.split()[0]
    order = st.slider("巴特沃斯阶数", 1, 5, 2)

    spec, fshift = m.fft_spectrum(src)
    low, high = m.make_filters(src.shape, float(d0), ft, order)
    grid([
        (src, "原图"), (spec, "频谱"),
        (m.apply_filter(fshift, low), f"低通 {ft} D0={d0}"),
        (m.apply_filter(fshift, high), f"高通 {ft} D0={d0}"),
    ], 4)

# ---------------------------------------------------------------- 实验六
with tab6:
    st.subheader("实验六：图像复原")
    st.caption(PRINCIPLE["exp6"])
    m = M["exp6"]
    up = st.file_uploader("上传图像（可选）", type=["jpg", "png", "jpeg", "bmp"], key="u6")
    src = cv2.resize(gray(up) if up else default_gray(m), (400, 400))
    btype = st.selectbox("退化类型", ["gaussian 高斯模糊", "motion 运动模糊"])
    k = st.slider("维纳滤波 K", 0.001, 0.5, 0.01, 0.001, format="%.3f")
    add_noise = st.checkbox("叠加噪声（考察抗噪性）", value=True)
    nsigma = st.slider("噪声 σ", 1, 30, 5, 1)

    if btype.startswith("gaussian"):
        blur, psf = m.gaussian_blur(src, 15, 3.0)
    else:
        blur, psf = m.motion_blur(src, 20, 0.0)
    if add_noise:
        blur = np.clip(blur.astype(np.float32) + np.random.normal(0, nsigma, blur.shape), 0, 255).astype(np.uint8)

    inv = m.inverse_filter(blur, psf)
    wie = m.wiener_filter(blur, psf, k)
    grid([(src, "原图"), (blur, "退化图"),
          (inv, f"逆滤波 {m.psnr(src, inv):.2f} dB"),
          (wie, f"维纳滤波 K={k} {m.psnr(src, wie):.2f} dB")], 4)

# ---------------------------------------------------------------- 实验七
with tab7:
    st.subheader("实验七：人脸皮肤颜色分层")
    st.caption(PRINCIPLE["exp7"])
    st.info("本栏目使用公开的人脸数据集图像，不含任何真实证件照。")
    m = M["exp7"]
    up = st.file_uploader("上传人脸图（可选）", type=["jpg", "png", "jpeg", "bmp"], key="u7")
    raw = to_bgr(up) if up else default_bgr(m)
    src = m.resize_keep_aspect(raw, 400)

    masks = {
        "RGB": m.skin_mask_rgb(src),
        "YCbCr": m.skin_mask_ycbcr(src),
        "HSV": m.skin_mask_hsv(src),
    }
    vote = sum((v > 0).astype(np.uint8) for v in masks.values())
    fused = m.postprocess((vote >= 2).astype(np.uint8) * 255)

    grid([(src, "原图")] + [(m.overlay(src, m.postprocess(v)), f"{k} 掩膜+后处理") for k, v in masks.items()]
         + [(m.overlay(src, fused), "三方法投票融合")], 5)
    st.dataframe(
        {"颜色空间": list(masks.keys()), "肤色像素占比": [f"{100 * (v > 0).mean():.1f}%" for v in masks.values()]}
        | {"融合": [f"{100 * (fused > 0).mean():.1f}%"] * len(masks)},
        hide_index=True,
    )
