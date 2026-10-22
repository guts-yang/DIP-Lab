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
from __future__ import annotations


import glob
import os
import sys

import cv2
import numpy as np

# 输入目录优先级：data/raw（统一原始图库） > 本实验 images/
_HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(_HERE, "..", "images", "output")
IMAGE_DIR = os.path.join(_HERE, "..", "images")
RAW_DIR = os.path.join(_HERE, "..", "..", "..", "data", "raw")
DEFAULT_SIZE = 400


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


def _scan(directory: str) -> list[str]:
    """扫描目录下所有图像文件（排除 output 目录），按名称排序。
    同时匹配大小写扩展名，避免漏掉 .JPG 等大写后缀。
    """
    found: list[str] = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
        found += [f for f in glob.glob(os.path.join(directory, ext)) if "output" not in f]
        found += [f for f in glob.glob(os.path.join(directory, ext.upper())) if "output" not in f]
    # 去重后排序
    return sorted(set(found))


def find_input_image(path: str | None) -> np.ndarray:
    """按 data/raw -> images/ -> 合成图 的优先级确定输入。"""
    if path:
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(f"无法读取图像：{path}")
        return img
    for directory in (RAW_DIR, IMAGE_DIR):
        files = _scan(directory)
        if files:
            img = cv2.imread(files[0])
            if img is not None:
                print(f"自动使用图像：{files[0]}")
                return img
    print("未找到输入照片，使用内置合成示意图演示。")
    return make_demo_image()


def resize_keep_aspect(bgr: np.ndarray, size: int = DEFAULT_SIZE) -> np.ndarray:
    """等比缩放到指定边长，短边补白，避免人脸被拉伸变形。"""
    h, w = bgr.shape[:2]
    scale = size / max(h, w)
    nh, nw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    resized = cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.full((size, size, 3), 255, dtype=np.uint8)
    y0, x0 = (size - nh) // 2, (size - nw) // 2
    canvas[y0:y0 + nh, x0:x0 + nw] = resized
    return canvas


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


def process(src: np.ndarray, tag: str, out_dir: str) -> None:
    """对单张图执行三种颜色空间分割 + 形态学后处理 + 投票融合。"""
    results = {
        "rgb": skin_mask_rgb(src),
        "ycbcr": skin_mask_ycbcr(src),
        "hsv": skin_mask_hsv(src),
    }

    mask_tiles, overlay_tiles = [], []
    for name, mask in results.items():
        cv2.imwrite(os.path.join(out_dir, f"01_mask_{name}.png"), mask)
        cv2.imwrite(os.path.join(out_dir, f"02_overlay_{name}.png"), overlay(src, mask))
        cleaned = postprocess(mask)
        cv2.imwrite(os.path.join(out_dir, f"03_postprocessed_{name}.png"), cleaned)
        cv2.imwrite(os.path.join(out_dir, f"04_face_candidate_{name}.png"), overlay(src, cleaned))
        mask_tiles.append(add_label(cv2.cvtColor(cv2.resize(mask, (200, 200)), cv2.COLOR_GRAY2BGR), name))
        overlay_tiles.append(add_label(cv2.resize(overlay(src, cleaned), (200, 200)), f"{name} face"))

    cv2.imwrite(os.path.join(out_dir, "masks_grid.png"),
                np.hstack([add_label(cv2.resize(src, (200, 200)), "source")] + mask_tiles))
    cv2.imwrite(os.path.join(out_dir, "overlay_grid.png"),
                np.hstack([add_label(cv2.resize(src, (200, 200)), "source")] + overlay_tiles))

    # 三方法投票融合，提升鲁棒性
    vote = sum((m > 0).astype(np.uint8) for m in results.values())
    fused = (vote >= 2).astype(np.uint8) * 255
    fused = postprocess(fused)
    cv2.imwrite(os.path.join(out_dir, "05_fused_vote.png"), fused)
    cv2.imwrite(os.path.join(out_dir, "06_fused_result.png"), overlay(src, fused))
    print(f"  [{tag}] 完成，输出 {len(os.listdir(out_dir))} 个文件")


def main() -> None:
    ensure_output_dir()
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    # 批量模式：传入目录则处理目录下所有图像
    if arg and os.path.isdir(arg):
        files = _scan(arg)
        if not files:
            print(f"目录中没有可用图像：{arg}")
            return
        print(f"批量处理 {len(files)} 张图像，来源：{arg}")
        for f in files:
            img = cv2.imread(f)
            if img is None:
                continue
            tag = os.path.splitext(os.path.basename(f))[0]
            out_dir = os.path.join(OUTPUT_DIR, tag)
            os.makedirs(out_dir, exist_ok=True)
            process(resize_keep_aspect(img, DEFAULT_SIZE), tag, out_dir)
        print(f"\n批量结果已输出到：{os.path.abspath(OUTPUT_DIR)}/<图片名>/")
        return

    # 单图模式
    src = find_input_image(arg)
    src = resize_keep_aspect(src, DEFAULT_SIZE)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "00_source.png"), src)
    process(src, "single", OUTPUT_DIR)
    print(f"\n结果已输出到：{os.path.abspath(OUTPUT_DIR)}")
    print("  - masks_grid.png 三种颜色空间的肤色掩膜对比")
    print("  - overlay_grid.png 形态学后处理与最大连通域提取结果")
    print("  - 05_fused_vote.png / 06_fused_result.png 三方法投票融合结果")
    print("\n提示：传入目录可批量处理，如 python skin_segmentation.py ../../../../data/raw")


if __name__ == "__main__":
    main()
