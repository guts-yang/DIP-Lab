"""实验四：图像的空间域锐化。

内容：
1. 采用拉普拉斯算子对图像进行锐化
2. 利用 Canny 边缘检测算子进行边缘检测

运行：
    python sharpening.py [图像路径]
输出：
    ../images/output/ 下的锐化与边缘检测结果
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
    img = np.full((400, 400), 128, dtype=np.uint8)
    cv2.circle(img, (200, 200), 110, 210, -1)
    cv2.rectangle(img, (60, 60), (160, 160), 60, -1)
    cv2.line(img, (30, 340), (370, 340), 240, 3)
    cv2.putText(img, "DIP", (130, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.4, 30, 3)
    return cv2.GaussianBlur(img, (7, 7), 1.5)


def load_image(path: str | None) -> np.ndarray:
    if path:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"无法读取图像：{path}")
        return img
    return make_demo_image()


def laplacian_sharpen(img: np.ndarray, kernel_type: str = "4", c: float = 1.0) -> np.ndarray:
    """拉普拉斯锐化：g = f + c * Laplacian(f)。

    kernel_type='4' 使用 4 邻域模板 [0 1 0; 1 -4 1; 0 1 0]
    kernel_type='8' 使用 8 邻域模板 [1 1 1; 1 -8 1; 1 1 1]
    注意：模板中心为负时，应减去拉普拉斯结果，故此处取 -Laplacian 后相加。
    """
    if kernel_type == "8":
        kernel = np.array([[1, 1, 1], [1, -8, 1], [1, 1, 1]], dtype=np.float32)
    else:
        kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)

    lap = cv2.filter2D(img.astype(np.float32), cv2.CV_32F, kernel)
    sharpened = img.astype(np.float32) - c * lap  # 中心为负模板，减拉普拉斯等价于加高频
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def unsharp_mask(img: np.ndarray, ksize: int = 5, amount: float = 1.5) -> np.ndarray:
    """非锐化掩蔽（补充对比）：f + amount * (f - blur(f))。"""
    blurred = cv2.GaussianBlur(img, (ksize, ksize), 0)
    return np.clip(img.astype(np.float32) + amount * (img.astype(np.float32) - blurred.astype(np.float32)), 0, 255).astype(np.uint8)


def canny_edges(img: np.ndarray, threshold1: float, threshold2: float, blur: int = 5) -> np.ndarray:
    """Canny 边缘检测：高斯平滑 -> 梯度 -> 非极大值抑制 -> 双阈值连接。"""
    smoothed = cv2.GaussianBlur(img, (blur, blur), 1.4)
    return cv2.Canny(smoothed, threshold1, threshold2)


def add_label(img: np.ndarray, text: str) -> np.ndarray:
    bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img.copy()
    return cv2.putText(bgr, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)


def main() -> None:
    ensure_output_dir()
    src_path = sys.argv[1] if len(sys.argv) > 1 else None
    src = load_image(src_path)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "01_source.png"), src)

    # 1. 拉普拉斯锐化
    lap4 = cv2.filter2D(src.astype(np.float32), cv2.CV_32F, np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32))
    cv2.imwrite(os.path.join(OUTPUT_DIR, "02_laplacian_response.png"), cv2.normalize(np.abs(lap4), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8))
    sharp4 = laplacian_sharpen(src, "4", c=1.0)
    sharp8 = laplacian_sharpen(src, "8", c=1.0)
    usm = unsharp_mask(src)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "03_sharpen_laplacian4.png"), sharp4)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "04_sharpen_laplacian8.png"), sharp8)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "05_unsharp_mask.png"), usm)

    compare = np.hstack([add_label(src, "source"), add_label(sharp4, "laplacian-4"), add_label(sharp8, "laplacian-8"), add_label(usm, "unsharp")])
    cv2.imwrite(os.path.join(OUTPUT_DIR, "sharpen_compare.png"), compare)

    # 2. Canny 边缘检测（三组阈值对比）
    settings = [(50, 100), (50, 150), (100, 200)]
    tiles = []
    for t1, t2 in settings:
        edges = canny_edges(src, t1, t2)
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"06_canny_{t1}_{t2}.png"), edges)
        tiles.append(add_label(cv2.resize(edges, (300, 300)), f"Canny {t1}-{t2}"))
    cv2.imwrite(os.path.join(OUTPUT_DIR, "canny_grid.png"), np.hstack(tiles))

    # 拉普拉斯 vs Canny 对照
    cv2.imwrite(os.path.join(OUTPUT_DIR, "canny_vs_laplacian.png"),
                np.hstack([add_label(cv2.resize(np.abs(lap4).astype(np.uint8), (300, 300)), "Laplacian"),
                           add_label(cv2.resize(canny_edges(src, 50, 150), (300, 300)), "Canny 50-150")]))

    print(f"结果已输出到：{os.path.abspath(OUTPUT_DIR)}")
    print("  - sharpen_compare.png 拉普拉斯与非锐化掩蔽对比")
    print("  - canny_grid.png 不同双阈值的 Canny 结果")
    print("  - canny_vs_laplacian.png 两种边缘提取方式对照")


if __name__ == "__main__":
    main()
