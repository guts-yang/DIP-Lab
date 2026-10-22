"""实验六：数字图像复原。

内容：
1. 对图像施加高斯模糊和运动模糊
2. 采用维纳滤波进行图像复原（含逆滤波对比）

运行：
    python restoration.py [图像路径]
输出：
    ../images/output/ 下的模糊与复原结果，以及 PSNR 对比
"""
from __future__ import annotations


import os
import sys

import cv2
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "output")


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def make_demo_image() -> np.ndarray:
    img = np.full((400, 400), 130, dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (350, 350), 200, 2)
    cv2.circle(img, (200, 200), 90, 60, -1)
    cv2.line(img, (50, 300), (350, 300), 250, 3)
    cv2.putText(img, "RESTORE", (95, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.9, 240, 2)
    return img


def load_image(path: str | None) -> np.ndarray:
    if path:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"无法读取图像：{path}")
        return img
    return make_demo_image()


def psnr(original: np.ndarray, processed: np.ndarray) -> float:
    mse = np.mean((original.astype(np.float32) - processed.astype(np.float32)) ** 2)
    if mse == 0:
        return float("inf")
    return 10 * np.log10(255.0 ** 2 / mse)


def gaussian_blur(img: np.ndarray, ksize: int = 15, sigma: float = 3.0) -> tuple[np.ndarray, np.ndarray]:
    """高斯模糊，同时返回对应的点扩散函数 PSF（归一化）。"""
    psf = np.zeros((ksize, ksize), dtype=np.float32)
    psf[ksize // 2, ksize // 2] = 1.0
    psf = cv2.GaussianBlur(psf, (ksize, ksize), sigma)
    blurred = cv2.filter2D(img.astype(np.float32), cv2.CV_32F, psf)
    return np.clip(blurred, 0, 255).astype(np.uint8), psf


def motion_blur(img: np.ndarray, length: int = 20, angle: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """运动模糊，返回模糊图与 PSF（线状核）。"""
    psf = np.zeros((length, length), dtype=np.float32)
    center = length // 2
    rad = np.deg2rad(angle)
    for i in range(length):
        offset = i - center
        y = int(center + offset * np.sin(rad))
        x = int(center + offset * np.cos(rad))
        if 0 <= y < length and 0 <= x < length:
            psf[y, x] = 1.0
    psf /= psf.sum()
    blurred = cv2.filter2D(img.astype(np.float32), cv2.CV_32F, psf)
    return np.clip(blurred, 0, 255).astype(np.uint8), psf


def pad_psf(psf: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """把 PSF 补零到图像尺寸，并循环移位使中心位于 (0,0)，便于频域相乘。"""
    h, w = shape
    padded = np.zeros((h, w), dtype=np.float32)
    ph, pw = psf.shape
    padded[:ph, :pw] = psf
    return np.fft.ifftshift(padded)


def inverse_filter(blurred: np.ndarray, psf: np.ndarray, eps: float = 1e-3) -> np.ndarray:
    """逆滤波：F = G / H，对 H 接近 0 处做截断以抑制爆炸。"""
    h = np.fft.fft2(pad_psf(psf, blurred.shape))
    g = np.fft.fft2(blurred.astype(np.float32))
    h_safe = np.where(np.abs(h) < eps, eps, h)
    restored = np.fft.ifft2(g / h_safe)
    return np.clip(np.abs(restored), 0, 255).astype(np.uint8)


def wiener_filter(blurred: np.ndarray, psf: np.ndarray, k: float = 0.01) -> np.ndarray:
    """维纳滤波：F = [H* / (|H|^2 + K)] * G，K 为噪声对信号功率比的估计。"""
    h = np.fft.fft2(pad_psf(psf, blurred.shape))
    g = np.fft.fft2(blurred.astype(np.float32))
    h_conj = np.conj(h)
    restored = np.fft.ifft2(h_conj / (np.abs(h) ** 2 + k) * g)
    return np.clip(np.abs(restored), 0, 255).astype(np.uint8)


def add_label(img: np.ndarray, text: str) -> np.ndarray:
    bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img.copy()
    return cv2.putText(bgr, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)


def process(src: np.ndarray, tag: str, psf: np.ndarray, blurred: np.ndarray, k: float, lines: list[str]) -> None:
    cv2.imwrite(os.path.join(OUTPUT_DIR, f"01_blurred_{tag}.png"), blurred)
    inv = inverse_filter(blurred, psf)
    wie = wiener_filter(blurred, psf, k)
    cv2.imwrite(os.path.join(OUTPUT_DIR, f"02_inverse_{tag}.png"), inv)
    cv2.imwrite(os.path.join(OUTPUT_DIR, f"03_wiener_{tag}_k{str(k).replace('.', 'p')}.png"), wie)

    cv2.imwrite(os.path.join(OUTPUT_DIR, f"compare_{tag}.png"),
                np.hstack([add_label(src, "source"), add_label(blurred, "blurred"),
                           add_label(inv, "inverse"), add_label(wie, f"wiener k={k}")]))

    lines.append(f"[{tag}] 模糊 PSNR = {psnr(src, blurred):.2f} dB")
    lines.append(f"  - 逆滤波复原 PSNR = {psnr(src, inv):.2f} dB")
    lines.append(f"  - 维纳滤波(K={k})复原 PSNR = {psnr(src, wie):.2f} dB")

    # 不同 K 值对比
    k_tiles = []
    for kk in (0.001, 0.01, 0.1):
        out = wiener_filter(blurred, psf, kk)
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"03_wiener_{tag}_k{str(kk).replace('.', 'p')}.png"), out)
        k_tiles.append(add_label(out, f"K={kk}"))
        lines.append(f"  - 维纳滤波(K={kk})复原 PSNR = {psnr(src, out):.2f} dB")
    cv2.imwrite(os.path.join(OUTPUT_DIR, f"wiener_k_compare_{tag}.png"), np.hstack(k_tiles))


def main() -> None:
    ensure_output_dir()
    src_path = sys.argv[1] if len(sys.argv) > 1 else None
    src = load_image(src_path)
    src = cv2.resize(src, (400, 400))
    cv2.imwrite(os.path.join(OUTPUT_DIR, "00_source.png"), src)

    lines: list[str] = []

    # 1. 高斯模糊复原
    g_blur, g_psf = gaussian_blur(src, ksize=15, sigma=3.0)
    process(src, "gaussian", g_psf, g_blur, 0.01, lines)

    # 2. 运动模糊复原
    m_blur, m_psf = motion_blur(src, length=20, angle=0.0)
    process(src, "motion", m_psf, m_blur, 0.01, lines)

    # 3. 模糊 + 噪声，考察维纳滤波的抗噪性
    noisy_blur = np.clip(g_blur.astype(np.float32) + np.random.normal(0, 5, g_blur.shape), 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "01_blurred_gaussian_noisy.png"), noisy_blur)
    inv_n = inverse_filter(noisy_blur, g_psf)
    wie_n = wiener_filter(noisy_blur, g_psf, 0.05)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "02_inverse_gaussian_noisy.png"), inv_n)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "03_wiener_gaussian_noisy.png"), wie_n)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "compare_gaussian_noisy.png"),
                np.hstack([add_label(src, "source"), add_label(noisy_blur, "blur+noise"),
                           add_label(inv_n, "inverse"), add_label(wie_n, "wiener k=0.05")]))
    lines.append("[gaussian+noise] 逆滤波在有噪时明显退化，维纳滤波更稳健")
    lines.append(f"  - 逆滤波 PSNR = {psnr(src, inv_n):.2f} dB")
    lines.append(f"  - 维纳滤波 PSNR = {psnr(src, wie_n):.2f} dB")

    with open(os.path.join(OUTPUT_DIR, "psnr_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"结果已输出到：{os.path.abspath(OUTPUT_DIR)}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
