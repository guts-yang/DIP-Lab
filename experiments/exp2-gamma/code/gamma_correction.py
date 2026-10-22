"""实验二：数字图像变换与伽马校正。

内容：
1. 灰度变换：线性、对数、反色
2. 伽马校正 s = c * r^gamma，对不同 gamma 参数进行对比

运行：
    python gamma_correction.py [图像路径]
输出：
    ../images/output/ 下的各种变换结果
"""

import os
import sys

import cv2
import numpy as np
from matplotlib import pyplot as plt

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "output")
GAMMA_VALUES = [0.4, 0.6, 1.0, 1.5, 2.2, 3.0]


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def make_demo_image() -> np.ndarray:
    """生成一幅偏暗的图像，便于观察伽马校正效果。"""
    h, w = (400, 400)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base = 40 + 80 * np.exp(-(((xx - w / 2) ** 2 + (yy - h / 2) ** 2) / (2 * (w / 5) ** 2)))
    img = np.clip(base + 25 * np.sin(xx / 25.0), 0, 255)
    return img.astype(np.uint8)


def load_image(path: str | None) -> np.ndarray:
    if path:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"无法读取图像：{path}")
        return img
    return make_demo_image()


def gamma_transform(img: np.ndarray, gamma: float, c: float = 1.0) -> np.ndarray:
    """幂律（伽马）变换 s = c * r^gamma。"""
    table = np.array([c * ((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.float32)
    return np.clip(table, 0, 255).astype(np.uint8)[img]


def log_transform(img: np.ndarray, c: float | None = None) -> np.ndarray:
    """对数变换 s = c * log(1 + r)，用于扩展暗部细节。"""
    if c is None:
        c = 255.0 / np.log(1 + img.max())
    return np.clip(c * np.log1p(img.astype(np.float32)), 0, 255).astype(np.uint8)


def negative_transform(img: np.ndarray) -> np.ndarray:
    """灰度反转 s = 255 - r。"""
    return 255 - img


def plot_gamma_curves() -> None:
    r = np.linspace(0, 1, 256)
    plt.figure(figsize=(6, 5))
    for g in GAMMA_VALUES:
        plt.plot(r * 255, (r ** g) * 255, label=f"gamma={g}")
    plt.plot([0, 255], [0, 255], "k--", label="identity")
    plt.xlabel("输入灰度 r")
    plt.ylabel("输出灰度 s")
    plt.title("伽马变换曲线 s = c * r^gamma")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "gamma_curves.png"), dpi=120)
    plt.close()


def main() -> None:
    ensure_output_dir()
    src_path = sys.argv[1] if len(sys.argv) > 1 else None
    src = load_image(src_path)

    cv2.imwrite(os.path.join(OUTPUT_DIR, "01_source.png"), src)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "02_negative.png"), negative_transform(src))
    cv2.imwrite(os.path.join(OUTPUT_DIR, "03_log.png"), log_transform(src))

    tiles = []
    for g in GAMMA_VALUES:
        out = gamma_transform(src, g)
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"gamma_{str(g).replace('.', 'p')}.png"), out)
        # 在缩略图上标注参数
        thumb = cv2.resize(out, (200, 200))
        thumb = cv2.putText(
            cv2.cvtColor(thumb, cv2.COLOR_GRAY2BGR),
            f"g={g}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
        )
        tiles.append(thumb)

    grid = np.vstack([np.hstack(tiles[:3]), np.hstack(tiles[3:])])
    cv2.imwrite(os.path.join(OUTPUT_DIR, "gamma_grid.png"), grid)

    plot_gamma_curves()

    print(f"结果已输出到：{os.path.abspath(OUTPUT_DIR)}")
    print(f"  - gamma_grid.png 不同 gamma（{GAMMA_VALUES}）的对比图")
    print("  - gamma_curves.png 伽马变换曲线")
    print("  - 02_negative.png 反色变换 / 03_log.png 对数变换")


if __name__ == "__main__":
    main()
