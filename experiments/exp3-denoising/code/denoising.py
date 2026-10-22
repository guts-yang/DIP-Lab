"""实验三：数字图像的噪声去除。

内容：
1. 对图像加入高斯噪声和椒盐噪声
2. 用中值滤波、统计排序滤波（最大值 / 最小值 / 中点 / 修正阿尔法均值）去噪

运行：
    python denoising.py [图像路径]
输出：
    ../images/output/ 下的加噪与去噪结果，以及 PSNR 对比
"""
from __future__ import annotations


import glob
import os
import sys

import cv2
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "output")
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")
STANDARD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "standard")


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def make_demo_image() -> np.ndarray:
    h, w = (400, 400)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base = 128 + 60 * np.sin(xx / 35.0) * np.cos(yy / 35.0)
    blocks = (((xx // 80) + (yy // 80)) % 2) * 70
    img = np.clip(base + blocks, 0, 255)
    return img.astype(np.uint8)


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


def add_gaussian_noise(img: np.ndarray, mean: float = 0.0, sigma: float = 25.0) -> np.ndarray:
    noise = np.random.normal(mean, sigma, img.shape).astype(np.float32)
    return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def add_salt_pepper_noise(img: np.ndarray, amount: float = 0.05, salt_vs_pepper: float = 0.5) -> np.ndarray:
    """amount 为噪声总比例，salt_vs_pepper 为盐噪声在其中占比。"""
    out = img.copy()
    total = int(amount * img.size)
    # 盐噪声
    coords = np.random.choice(img.size, int(total * salt_vs_pepper), replace=False)
    out.flat[coords] = 255
    # 椒噪声
    coords = np.random.choice(img.size, total - int(total * salt_vs_pepper), replace=False)
    out.flat[coords] = 0
    return out


def psnr(original: np.ndarray, processed: np.ndarray) -> float:
    mse = np.mean((original.astype(np.float32) - processed.astype(np.float32)) ** 2)
    if mse == 0:
        return float("inf")
    return 10 * np.log10(255.0 ** 2 / mse)


def median_filter(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    return cv2.medianBlur(img, ksize)


def max_filter(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    """统计排序滤波——最大值滤波，去除椒（暗）噪声。"""
    return cv2.dilate(img, np.ones((ksize, ksize), np.uint8))


def min_filter(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    """统计排序滤波——最小值滤波，去除盐（亮）噪声。"""
    return cv2.erode(img, np.ones((ksize, ksize), np.uint8))


def midpoint_filter(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    """统计排序滤波——中点滤波 (max + min) / 2，对高斯与均匀噪声有效。"""
    return cv2.addWeighted(max_filter(img, ksize), 0.5, min_filter(img, ksize), 0.5, 0)


def alpha_trimmed_mean_filter(img: np.ndarray, ksize: int = 3, d: int = 2) -> np.ndarray:
    """修正阿尔法均值滤波：去掉 d 个最暗与 d 个最亮像素后取均值，兼顾高斯与椒盐噪声。"""
    pad = ksize // 2
    padded = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REFLECT)
    h, w = img.shape
    out = np.zeros_like(img, dtype=np.float32)
    for i in range(h):
        for j in range(w):
            region = padded[i:i + ksize, j:j + ksize].flatten()
            region.sort()
            trimmed = region[d:region.size - d] if region.size > 2 * d else region
            out[i, j] = trimmed.mean()
    return np.clip(out, 0, 255).astype(np.uint8)


def main() -> None:
    ensure_output_dir()
    np.random.seed(2026)
    src_path = sys.argv[1] if len(sys.argv) > 1 else None
    src = load_image(src_path)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "01_source.png"), src)

    report_lines = []
    for noise_name, noisy in {
        "gaussian": add_gaussian_noise(src, sigma=25),
        "salt_pepper": add_salt_pepper_noise(src, amount=0.05),
    }.items():
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"02_noisy_{noise_name}.png"), noisy)
        report_lines.append(f"[{noise_name}] 加噪后 PSNR = {psnr(src, noisy):.2f} dB")

        results = {
            "median_k3": median_filter(noisy, 3),
            "median_k5": median_filter(noisy, 5),
            "max_k3": max_filter(noisy, 3),
            "min_k3": min_filter(noisy, 3),
            "midpoint_k3": midpoint_filter(noisy, 3),
        }
        for name, out in results.items():
            cv2.imwrite(os.path.join(OUTPUT_DIR, f"03_{noise_name}_{name}.png"), out)
            report_lines.append(f"  - {name}: PSNR = {psnr(src, out):.2f} dB")

    # 修正阿尔法均值单独演示（对混合噪声）
    mixed = add_salt_pepper_noise(add_gaussian_noise(src, sigma=15), amount=0.03)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "02_noisy_mixed.png"), mixed)
    trimmed = alpha_trimmed_mean_filter(mixed, ksize=3, d=2)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "03_mixed_alpha_trimmed_k3.png"), trimmed)
    report_lines.append(f"[mixed] 加噪后 PSNR = {psnr(src, mixed):.2f} dB")
    report_lines.append(f"  - alpha_trimmed_k3: PSNR = {psnr(src, trimmed):.2f} dB")

    with open(os.path.join(OUTPUT_DIR, "psnr_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"结果已输出到：{os.path.abspath(OUTPUT_DIR)}")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()
