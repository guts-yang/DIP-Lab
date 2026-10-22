"""实验五：频率域低通和高通滤波。

内容：
1. 对图像进行 FFT 变换并显示频谱
2. 选择某种低通滤波器（理想 / 巴特沃斯 / 高斯）进行低通滤波
3. 选择某种高通滤波器进行高通滤波

运行：
    python frequency_filter.py [图像路径]
输出：
    ../images/output/ 下的频谱图与滤波结果
"""
from __future__ import annotations


import glob
import os
import sys

import cv2
import numpy as np

OUTPUT_DIR = os.environ.get("DIP_OUTPUT_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "output")
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")
STANDARD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "standard")


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def make_demo_image() -> np.ndarray:
    img = np.full((400, 400), 120, dtype=np.uint8)
    cv2.circle(img, (200, 200), 120, 235, -1)
    cv2.rectangle(img, (40, 40), (150, 150), 40, -1)
    cv2.line(img, (0, 300), (399, 300), 250, 2)
    # 叠加细密纹理，使频谱中的高频成分明显
    yy, xx = np.mgrid[0:400, 0:400]
    texture = (60 * np.sin(xx / 3.0)).astype(np.int16)
    img = np.clip(img.astype(np.int16) + texture, 0, 255).astype(np.uint8)
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


def fft_spectrum(img: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """返回中心化的频谱（对数拉伸后便于显示）与 FFT 结果。"""
    f = np.fft.fft2(img.astype(np.float32))
    fshift = np.fft.fftshift(f)
    magnitude = 20 * np.log(np.abs(fshift) + 1)
    spectrum = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return spectrum, fshift


def make_filters(shape: tuple[int, int], d0: float, filter_type: str, order: int = 2) -> tuple[np.ndarray, np.ndarray]:
    """生成低通与高通滤波器。filter_type: ideal / butterworth / gaussian。"""
    rows, cols = shape
    cy, cx = rows // 2, cols // 2
    yy, xx = np.mgrid[0:rows, 0:cols]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2).astype(np.float32)

    if filter_type == "ideal":
        low = (dist <= d0).astype(np.float32)
    elif filter_type == "butterworth":
        low = 1.0 / (1.0 + (dist / d0) ** (2 * order))
    elif filter_type == "gaussian":
        low = np.exp(-(dist ** 2) / (2 * d0 ** 2))
    else:
        raise ValueError(f"未知滤波器类型：{filter_type}")

    return low, 1.0 - low


def apply_filter(fshift: np.ndarray, h: np.ndarray) -> np.ndarray:
    """频域滤波并反变换回空域。"""
    filtered = fshift * h
    ishift = np.fft.ifftshift(filtered)
    img_back = np.fft.ifft2(ishift)
    return np.clip(np.abs(img_back), 0, 255).astype(np.uint8)


def add_label(img: np.ndarray, text: str) -> np.ndarray:
    bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img.copy()
    return cv2.putText(bgr, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)


def main() -> None:
    ensure_output_dir()
    src_path = sys.argv[1] if len(sys.argv) > 1 else None
    src = load_image(src_path)
    src = cv2.resize(src, (400, 400))
    cv2.imwrite(os.path.join(OUTPUT_DIR, "01_source.png"), src)

    # 1. FFT 与频谱
    spectrum, fshift = fft_spectrum(src)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "02_spectrum.png"), spectrum)

    d0 = 40.0
    low_tiles, high_tiles, filter_tiles = [], [], []
    for ftype in ("ideal", "butterworth", "gaussian"):
        low, high = make_filters(src.shape, d0, ftype, order=2)
        low_img = apply_filter(fshift, low)
        high_img = apply_filter(fshift, high)

        cv2.imwrite(os.path.join(OUTPUT_DIR, f"03_lowpass_{ftype}.png"), low_img)
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"04_highpass_{ftype}.png"), high_img)

        low_tiles.append(add_label(cv2.resize(low_img, (260, 260)), f"LP {ftype}"))
        high_tiles.append(add_label(cv2.resize(high_img, (260, 260)), f"HP {ftype}"))
        filter_tiles.append(add_label(cv2.resize((low * 255).astype(np.uint8), (260, 260)), f"H {ftype}"))

    cv2.imwrite(os.path.join(OUTPUT_DIR, "lowpass_grid.png"), np.hstack(low_tiles))
    cv2.imwrite(os.path.join(OUTPUT_DIR, "highpass_grid.png"), np.hstack(high_tiles))
    cv2.imwrite(os.path.join(OUTPUT_DIR, "filters_grid.png"), np.hstack(filter_tiles))
    cv2.imwrite(os.path.join(OUTPUT_DIR, "spectrum_vs_filters.png"),
                np.vstack([np.hstack([add_label(cv2.resize(src, (260, 260)), "source"),
                                      add_label(cv2.resize(spectrum, (260, 260)), "spectrum"),
                                      add_label(cv2.resize((make_filters(src.shape, d0, "gaussian")[0] * 255).astype(np.uint8), (260, 260)), "Gauss LP")]),
                           np.hstack(low_tiles)]))

    # 不同截止频率对比（巴特沃斯低通）
    radius_tiles = []
    for d in (15, 40, 80):
        low, _ = make_filters(src.shape, float(d), "butterworth", order=2)
        radius_tiles.append(add_label(cv2.resize(apply_filter(fshift, low), (260, 260)), f"D0={d}"))
    cv2.imwrite(os.path.join(OUTPUT_DIR, "butterworth_d0_compare.png"), np.hstack(radius_tiles))

    print(f"结果已输出到：{os.path.abspath(OUTPUT_DIR)}")
    print("  - 02_spectrum.png 中心化对数频谱")
    print("  - lowpass_grid.png / highpass_grid.png 三类低通与高通对比")
    print("  - butterworth_d0_compare.png 不同截止频率效果")


if __name__ == "__main__":
    main()
