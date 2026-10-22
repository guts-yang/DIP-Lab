"""实验七：人脸皮肤颜色分层。

内容：采用彩色图像分层方法，提取人脸皮肤区域
参考任务书说明：可自行准备证件照或自拍照放入 ../images/ 作为输入

方法（均为传统方法，不使用深度学习）：
1. RGB 颜色规则
2. YCbCr 颜色空间椭圆/范围模型
3. HSV 颜色空间范围模型
4. 可选：肤色区域形态学后处理 + 连通域筛选得到人脸候选区

运行：
    python skin_segmentation.py [图像路径]
输出：
    ../images/output/ 下的肤色掩膜与叠加结果
"""

import glob
import os
import sys

import cv2
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "output")
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def make_demo_image() -> np.ndarray:
    """生成一张近似肤色的椭圆人脸示意图，用于无输入时的演示。"""
    img = np.full((400, 400, 3), 200, dtype=np.uint8)
    cv2.ellipse(img, (200, 210), (95, 125), 0, 0, 360, (150, 190, 225), -1)  # BGR 近似肤色
    cv2.circle(img, (165, 175), 12, (60, 60, 60), -1)
    cv2.circle(img, (240, 175), 12, (60, 60, 60), -1)
    cv2.ellipse(img, (200, 250), (35, 18), 0, 0, 180, (80, 90, 140), 2)
    cv2.rectangle(img, (0, 330), (399, 399), (90, 70, 60), -1)  # 非肤色衣物
    return img


def find_input_image(path: str | None) -> np.ndarray:
    if path:
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(f"无法读取图像：{path}")
        return img
    # 自动在 images/ 下查找用户放入的照片（排除 output 目录）
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
        files = [f for f in glob.glob(os.path.join(IMAGE_DIR, ext)) if "output" not in f]
        if files:
            img = cv2.imread(files[0])
            if img is not None:
                print(f"自动使用图像：{files[0]}")
                return img
    print("未找到输入照片，使用内置合成示意图演示。")
    return make_demo_image()


def skin_mask_rgb(bgr: np.ndarray) -> np.ndarray:
    """RGB 规则：R>95, G>40, B>20, max-min>15, |R-G|>15, R>G, R>B。"""
    b, g, r = cv2.split(bgr.astype(np.int16))
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    mask = ((r > 95) & (g > 40) & (b > 20) &
            ((mx - mn) > 15) & (np.abs(r - g) > 15) & (r > g) & (r > b))
    return mask.astype(np.uint8) * 255


def skin_mask_ycbcr(bgr: np.ndarray) -> np.ndarray:
    """YCbCr 范围模型：77<=Cb<=127 且 133<=Cr<=173（常用经验区间）。"""
    ycrcb = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    _, cr, cb = cv2.split(ycrcb)
    mask = ((cb >= 77) & (cb <= 127) & (cr >= 133) & (cr <= 173))
    return mask.astype(np.uint8) * 255


def skin_mask_hsv(bgr: np.ndarray) -> np.ndarray:
    """HSV 范围模型：H in [0,25]，S in [30,170]，V in [50,255]（OpenCV H 取 0-179）。"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    mask = ((h <= 25) & (s >= 30) & (s <= 170) & (v >= 50))
    return mask.astype(np.uint8) * 255


def postprocess(mask: np.ndarray) -> np.ndarray:
    """形态学开闭运算去噪点，再取最大连通域作为人脸候选。"""
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
    if num_labels <= 1:
        return cleaned
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return (labels == largest).astype(np.uint8) * 255


def add_label(img: np.ndarray, text: str) -> np.ndarray:
    out = img.copy()
    return cv2.putText(out, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)


def overlay(bgr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return cv2.bitwise_and(bgr, bgr, mask=mask)


def main() -> None:
    ensure_output_dir()
    src_path = sys.argv[1] if len(sys.argv) > 1 else None
    src = find_input_image(src_path)
    src = cv2.resize(src, (400, 400))
    cv2.imwrite(os.path.join(OUTPUT_DIR, "00_source.png"), src)

    results = {
        "rgb": skin_mask_rgb(src),
        "ycbcr": skin_mask_ycbcr(src),
        "hsv": skin_mask_hsv(src),
    }

    mask_tiles, overlay_tiles = [], []
    for name, mask in results.items():
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"01_mask_{name}.png"), mask)
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"02_overlay_{name}.png"), overlay(src, mask))
        cleaned = postprocess(mask)
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"03_postprocessed_{name}.png"), cleaned)
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"04_face_candidate_{name}.png"), overlay(src, cleaned))
        mask_tiles.append(add_label(cv2.cvtColor(cv2.resize(mask, (200, 200)), cv2.COLOR_GRAY2BGR), name))
        overlay_tiles.append(add_label(cv2.resize(overlay(src, cleaned), (200, 200)), f"{name} face"))

    cv2.imwrite(os.path.join(OUTPUT_DIR, "masks_grid.png"),
                np.hstack([add_label(cv2.resize(src, (200, 200)), "source")] + mask_tiles))
    cv2.imwrite(os.path.join(OUTPUT_DIR, "overlay_grid.png"),
                np.hstack([add_label(cv2.resize(src, (200, 200)), "source")] + overlay_tiles))

    # 三方法投票融合，提升鲁棒性
    vote = sum((m > 0).astype(np.uint8) for m in results.values())
    fused = (vote >= 2).astype(np.uint8) * 255
    fused = postprocess(fused)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "05_fused_vote.png"), fused)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "06_fused_result.png"), overlay(src, fused))

    print(f"结果已输出到：{os.path.abspath(OUTPUT_DIR)}")
    print("  - masks_grid.png 三种颜色空间的肤色掩膜对比")
    print("  - overlay_grid.png 形态学后处理与最大连通域提取结果")
    print("  - 05_fused_vote.png / 06_fused_result.png 三方法投票融合结果")


if __name__ == "__main__":
    main()
