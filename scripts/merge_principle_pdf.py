#!/usr/bin/env python3
"""把 docs/principle/ 下 7 份原理 PDF 合并为一个总册，带书签与总封面。"""

import os
import sys

import fitz  # PyMuPDF

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "principle")
OUT = os.path.join(SRC, "数字图像处理-实验原理总册.pdf")

PARTS = [
    ("实验1-原理说明.pdf", "实验一 直方图均衡化与规定化"),
    ("实验2-原理说明.pdf", "实验二 变换与伽马校正"),
    ("实验3-原理说明.pdf", "实验三 噪声去除"),
    ("实验4-原理说明.pdf", "实验四 空间域锐化"),
    ("实验5-原理说明.pdf", "实验五 频率域低通与高通滤波"),
    ("实验6-原理说明.pdf", "实验六 图像复原"),
    ("实验7-原理说明.pdf", "实验七 人脸皮肤颜色分层"),
]

# 中文字体（用于总封面，随实验文档使用同一体系）
FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
]


def make_cover():
    """生成总册封面页。"""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # 顶部色带
    page.draw_rect(fitz.Rect(0, 0, 595, 150), color=None, fill=(0.043, 0.239, 0.42))

    font = None
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            font = f
            break

    def put(text, y, size, color=(1, 1, 1), bold=None):
        page.insert_text(
            fitz.Point(297.5, y), text, fontname="china-s" if font else "helv",
            fontfile=font, fontsize=size, color=color,
            align=fitz.TEXT_ALIGN_CENTER,
        )

    # 用 insert_htmlbox 更好控制中文；退化为 insert_textbox
    def box(text, rect, size, color=(0, 0, 0), align="center"):
        page.insert_htmlbox(
            rect,
            f'<p style="text-align:{align};font-size:{size}px;color:'
            f'rgb({int(color[0]*255)},{int(color[1]*255)},{int(color[2]*255)});'
            f'margin:0;">{text}</p>',
            css="* {font-family: sans-serif;}",
        )

    box("数字图像处理", fitz.Rect(60, 45, 535, 95), 34, color=(1, 1, 1))
    box("实验原理总册", fitz.Rect(60, 100, 535, 140), 22, color=(1, 1, 1))

    box("2026 学年 · 计算机科学与工程学院", fitz.Rect(60, 200, 535, 240), 14,
        color=(0.15, 0.15, 0.15))

    items = "".join(f"<li>{t}</li>" for _, t in PARTS)
    page.insert_htmlbox(
        fitz.Rect(110, 280, 485, 620),
        f'<ol style="font-size:14px;line-height:2.1;color:#1a1a1a;">{items}</ol>',
        css="* {font-family: sans-serif;}",
    )

    box("本册汇总七次实验的底层原理、公式推导与答辩问答",
        fitz.Rect(60, 700, 535, 740), 11, color=(0.35, 0.35, 0.35))
    box("公式经 LaTeX 渲染 · 可直接打印",
        fitz.Rect(60, 730, 535, 765), 11, color=(0.35, 0.35, 0.35))

    return doc


def main():
    missing = [f for f, _ in PARTS if not os.path.exists(os.path.join(SRC, f))]
    if missing:
        sys.exit(f"缺少文件: {missing}")

    merged = fitz.open()
    toc = []

    cover = make_cover()
    merged.insert_pdf(cover)
    cover.close()
    toc.append([1, "总封面", 1])

    for fname, title in PARTS:
        src = fitz.open(os.path.join(SRC, fname))
        start = len(merged) + 1
        merged.insert_pdf(src)
        toc.append([1, title, start])
        src.close()
        print(f"  合并 {title}  (起始第 {start} 页)")

    merged.set_toc(toc)
    merged.set_metadata({
        "title": "数字图像处理 实验原理总册",
        "author": "DIP-Lab",
        "subject": "七次实验底层原理汇总",
    })

    # 页码（跳过封面）
    for i in range(1, len(merged)):
        p = merged[i]
        w, h = p.rect.width, p.rect.height
        p.insert_text(
            fitz.Point(w / 2 - 8, h - 20), f"{i}",
            fontsize=8, color=(0.45, 0.45, 0.45),
        )

    merged.save(OUT, garbage=4, deflate=True)
    merged.close()

    size = os.path.getsize(OUT) / 1024 / 1024
    print(f"\n总册 -> {OUT}")
    print(f"共 {len(fitz.open(OUT))} 页，{size:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
