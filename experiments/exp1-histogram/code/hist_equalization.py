"""实验一：数字图像读取及色彩、亮度、对比度变化。

内容：
1. 读取图像，进行色彩 / 亮度 / 对比度变化
2. 直方图均衡化（全局）
3. 直方图规定化（匹配到指定参考直方图）

运行：
    python hist_equalization.py           # 使用内置合成图像演示
    python hist_equalization.py <图像路径>  # 使用指定图像
输出：
    ../images/output/ 下的对比图与直方图
"""
from __future__ import annotations


import glob
import os
import sys

import cv2
import numpy as np
from matplotlib import pyplot as plt

# 中文字体配置：优先使用 macOS 系统中文字体，避免图例中文显示为方框
import platform as _platform
if _platform.system() == "Darwin":
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti TC", "Arial Unicode MS", "STHeiti"]
elif _platform.system() == "Windows":
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
else:
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei"]
plt.rcParams["axes.unicode_minus"] = False


OUTPUT_DIR = os.environ.get("DIP_OUTPUT_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "output")
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")
STANDARD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "standard")
DEFAULT_SIZE = (400, 400)


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def make_demo_image() -> np.ndarray:
    """生成一幅偏暗、低对比度的合成灰度图，用于无输入图像时的演示。"""
    h, w = DEFAULT_SIZE
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base = 60 + 40 * np.sin(xx / 40.0) + 30 * np.cos(yy / 55.0)
    circle = (((xx - w / 2) ** 2 + (yy - h / 2) ** 2) < (w / 4) ** 2) * 45
    img = np.clip(base + circle, 0, 255).astype(np.uint8)
    return img


def _scan(directory: str) -> list[str]:
    """扫描目录下所有图像（排除 output 目录），匹配大小写扩展名。"""
    found: list[str] = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff"):
        for d in (directory,):
            found += [f for f in glob.glob(os.path.join(d, ext)) if "output" not in f]
            found += [f for f in glob.glob(os.path.join(d, ext.upper())) if "output" not in f]
    return sorted(set(found))


def load_image(path: str | None = None) -> np.ndarray:
    """按 data/standard -> 本实验 images/ -> 合成图 的优先级读取输入。"""
    if path:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"无法读取图像：{path}")
        return img
    for directory in (STANDARD_DIR, IMAGE_DIR):
        files = _scan(directory)
        if files:
            img = cv2.imread(files[0], cv2.IMREAD_GRAYSCALE)
            if img is not None:
                print(f"自动使用标准图：{os.path.basename(files[0])}")
                return img
    print("未找到标准图，使用内置合成示意图演示。")
    return make_demo_image()


def adjust_brightness_contrast(img: np.ndarray, alpha: float = 1.0, beta: float = 0.0) -> np.ndarray:
    """线性变换 g = alpha * f + beta，alpha 控制对比度，beta 控制亮度。"""
    return np.clip(alpha * img.astype(np.float32) + beta, 0, 255).astype(np.uint8)


def equalize_histogram(img: np.ndarray) -> np.ndarray:
    """全局直方图均衡化。"""
    return cv2.equalizeHist(img)


def histogram_matching(source: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """直方图规定化：把 source 的灰度分布映射到 reference 的分布。"""
    src_hist, _ = np.histogram(source.flatten(), bins=256, range=(0, 256))
    ref_hist, _ = np.histogram(reference.flatten(), bins=256, range=(0, 256))

    src_cdf = src_hist.cumsum()
    src_cdf = (src_cdf - src_cdf.min()) * 255 / max(src_cdf.max() - src_cdf.min(), 1)
    ref_cdf = ref_hist.cumsum()
    ref_cdf = (ref_cdf - ref_cdf.min()) * 255 / max(ref_cdf.max() - ref_cdf.min(), 1)

    # 对源图像每个灰度级，在参考 CDF 中找到最接近的灰度级
    lut = np.zeros(256, dtype=np.uint8)
    ref_values = ref_cdf
    for src_level in range(256):
        lut[src_level] = np.argmin(np.abs(ref_values - src_cdf[src_level]))
    return lut[source]


def make_reference_histogram() -> np.ndarray:
    """构造一幅具有指定（偏亮且集中）直方图的参考图像。"""
    h, w = DEFAULT_SIZE
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ref = np.clip(150 + 60 * np.sin(xx / 30.0) + 40 * (yy / h), 0, 255)
    return ref.astype(np.uint8)


def plot_histograms(images: dict[str, np.ndarray], filename: str) -> None:
    plt.figure(figsize=(12, 4))
    for i, (title, img) in enumerate(images.items(), start=1):
        plt.subplot(1, len(images), i)
        plt.hist(img.flatten(), bins=256, range=(0, 256), color="steelblue")
        plt.title(title)
        plt.xlim(0, 255)
        plt.xlabel("灰度级")
        if i == 1:
            plt.ylabel("像素数")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=120)
    plt.close()


def main() -> None:
    ensure_output_dir()
    src_path = sys.argv[1] if len(sys.argv) > 1 else None
    src = load_image(src_path)

    # 1. 亮度 / 对比度变化
    bright = adjust_brightness_contrast(src, alpha=1.0, beta=50)
    contrast = adjust_brightness_contrast(src, alpha=1.8, beta=0)

    # 2. 直方图均衡化
    equalized = equalize_histogram(src)

    # 3. 直方图规定化
    reference = make_reference_histogram()
    matched = histogram_matching(src, reference)

    # 保存结果图
    for name, img in {
        "01_source.png": src,
        "02_brightness_beta50.png": bright,
        "03_contrast_alpha18.png": contrast,
        "04_equalized.png": equalized,
        "05_reference.png": reference,
        "06_matched.png": matched,
    }.items():
        cv2.imwrite(os.path.join(OUTPUT_DIR, name), img)

    # 拼接对比图
    compare = np.hstack([src, contrast, equalized, matched])
    cv2.imwrite(os.path.join(OUTPUT_DIR, "compare_source_contrast_equalized_matched.png"), compare)

    # 保存直方图
    plot_histograms({"原图": src, "均衡化": equalized, "规定化": matched}, "histograms.png")

    print(f"结果已输出到：{os.path.abspath(OUTPUT_DIR)}")
    print("  - 01_source.png 原图")
    print("  - 02_brightness_beta50.png 亮度提升（beta=50）")
    print("  - 03_contrast_alpha18.png 对比度增强（alpha=1.8）")
    print("  - 04_equalized.png 直方图均衡化")
    print("  - 05_reference.png 规定化参考图")
    print("  - 06_matched.png 直方图规定化结果")
    print("  - histograms.png 三者直方图对比")


if __name__ == "__main__":
    main()
