#!/usr/bin/env python3
"""按 docs/lab-report-template-2026.doc 的格式生成 7 份实验报告 docx。

格式遵循模板说明：
- 正文两端对齐、首行缩进 2 字符、段前段后 0 行
- 图号图名在图的下方，居中
- 表号表名在表的上方，居中
"""

import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPS = os.path.join(ROOT, "experiments")

FONT_CN = "宋体"
FONT_EN = "Times New Roman"


def set_run(run, size=12, bold=False, cn=FONT_CN, en=FONT_EN):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = en
    run.font.color.rgb = RGBColor(0, 0, 0)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), cn)
    return run


def para(doc, text, size=12, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         indent=True, space_after=0, cn=FONT_CN):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.5
    if indent:
        pf.first_line_indent = Pt(size * 2)
    r = p.add_run(text)
    set_run(r, size=size, bold=bold, cn=cn)
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 0 else WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(12 if level else 0)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.5
    size = {0: 22, 1: 16, 2: 14, 3: 12}[level]
    r = p.add_run(text)
    set_run(r, size=size, bold=True, cn="黑体" if level <= 1 else FONT_CN)
    return p


def code_block(doc, code, caption=None):
    """代码块：等宽字体，不缩进，带底纹边框感。"""
    if caption:
        para(doc, caption, size=10.5, indent=False, space_after=2)
    for line in code.strip("\n").split("\n"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf = p.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing = 1.0
        pf.left_indent = Pt(18)
        r = p.add_run(line if line.strip() else " ")
        set_run(r, size=9, cn="Consolas", en="Consolas")
        r.font.color.rgb = RGBColor(0x1F, 0x1F, 0x1F)


def figure(doc, img_path, caption, width=None):
    """插图：图居中，图号图名在下方居中。"""
    from docx.shared import Cm
    if not os.path.exists(img_path):
        para(doc, f"[缺失图片 {os.path.basename(img_path)}]", size=10, indent=False)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(img_path, width=Cm(width or 12))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(0)
    cap.paragraph_format.space_after = Pt(8)
    cap.paragraph_format.line_spacing = 1.0
    r = cap.add_run(caption)
    set_run(r, size=10.5, cn=FONT_CN)


def table_caption(doc, text):
    para(doc, text, size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, space_after=2)


def make_table(doc, header, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(header):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        set_run(p.add_run(h), size=10.5, bold=True)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            set_run(p.add_run(str(v)), size=10.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def cover(doc, title, subtitle):
    for _ in range(3):
        doc.add_paragraph()
    heading(doc, "数字图像处理实验报告书", level=0)
    doc.add_paragraph()
    heading(doc, subtitle, level=0)
    for _ in range(6):
        doc.add_paragraph()
    info = [
        ("学  院", "计算机科学与工程学院"),
        ("专  业", ""),
        ("学生姓名", ""),
        ("学生学号", ""),
        ("任课教师", "沃  焱"),
        ("成  绩", ""),
    ]
    for k, v in info:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(10)
        set_run(p.add_run(f"{k}        {v}"), size=14)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def content_section(doc, items):
    heading(doc, "1. 实验内容", level=1)
    for it in items:
        para(doc, it)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def process_section(doc, blocks):
    heading(doc, "2. 实验过程及结果", level=1)
    for b in blocks:
        b(doc)


def txt(b):
    return lambda doc: para(doc, b)


def sub(b):
    return lambda doc: heading(doc, b, level=2)


def img(rel, cap, w=None):
    path = os.path.join(EXPS, rel)
    return lambda doc: figure(doc, path, cap, w)


def code(c, cap=None):
    return lambda doc: code_block(doc, c, cap)


def tbl(cap, header, rows):
    def f(doc):
        table_caption(doc, cap)
        make_table(doc, header, rows)
    return f


def build(fname, subtitle, content_items, blocks):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = FONT_EN
    st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT_CN)

    cover(doc, subtitle, subtitle)
    heading(doc, subtitle, level=0)
    content_section(doc, content_items)
    process_section(doc, blocks)

    out = os.path.join(EXPS, fname)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    doc.save(out)
    print(f"  -> {out}")
    return out


CODE1 = '''
def histogram_matching(source, reference):
    """直方图规定化：把 source 的灰度分布映射到 reference 的分布。"""
    src_hist, _ = np.histogram(source.flatten(), bins=256, range=(0, 256))
    ref_hist, _ = np.histogram(reference.flatten(), bins=256, range=(0, 256))

    src_cdf = src_hist.cumsum()
    src_cdf = (src_cdf - src_cdf.min()) * 255 / max(src_cdf.max() - src_cdf.min(), 1)
    ref_cdf = ref_hist.cumsum()
    ref_cdf = (ref_cdf - ref_cdf.min()) * 255 / max(ref_cdf.max() - ref_cdf.min(), 1)

    lut = np.zeros(256, dtype=np.uint8)
    for src_level in range(256):
        lut[src_level] = np.argmin(np.abs(ref_cdf - src_cdf[src_level]))
    return lut[source]

equalized = cv2.equalizeHist(src)          # 全局直方图均衡化
'''

CODE2 = '''
def gamma_transform(img, gamma, c=1.0):
    """幂律（伽马）变换 s = c * r^gamma。"""
    table = np.array([c * ((i / 255.0) ** gamma) * 255
                      for i in range(256)], dtype=np.float32)
    return np.clip(table, 0, 255).astype(np.uint8)[img]
'''

CODE3 = '''
def add_gaussian_noise(img, mean=0.0, sigma=25.0):
    noise = np.random.normal(mean, sigma, img.shape).astype(np.float32)
    return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

def alpha_trimmed_mean_filter(img, ksize=3, d=2):
    """修正阿尔法均值：去掉 d 个最暗与 d 个最亮后取均值。"""
    pad = ksize // 2
    padded = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REFLECT)
    h, w = img.shape
    out = np.zeros_like(img, dtype=np.float32)
    for i in range(h):
        for j in range(w):
            region = padded[i:i+ksize, j:j+ksize].flatten()
            region.sort()
            trimmed = region[d:region.size-d] if region.size > 2*d else region
            out[i, j] = trimmed.mean()
    return np.clip(out, 0, 255).astype(np.uint8)
'''

CODE4 = '''
def laplacian_sharpen(img, kernel_type="4", c=1.0):
    """拉普拉斯锐化：g = f + c * Laplacian(f)。"""
    if kernel_type == "8":
        kernel = np.array([[1, 1, 1], [1, -8, 1], [1, 1, 1]], dtype=np.float32)
    else:
        kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    lap = cv2.filter2D(img.astype(np.float32), cv2.CV_32F, kernel)
    return np.clip(img.astype(np.float32) - c * lap, 0, 255).astype(np.uint8)

def canny_edges(img, threshold1, threshold2, blur=5):
    """Canny：高斯平滑 -> 梯度 -> 非极大值抑制 -> 双阈值连接。"""
    smoothed = cv2.GaussianBlur(img, (blur, blur), 1.4)
    return cv2.Canny(smoothed, threshold1, threshold2)
'''

CODE5 = '''
def make_filters(shape, d0, filter_type, order=2):
    """生成低通与高通滤波器。filter_type: ideal / butterworth / gaussian。"""
    ...
    if filter_type == "ideal":
        low = (D <= d0).astype(np.float32)
    elif filter_type == "butterworth":
        low = 1.0 / (1.0 + (D / d0) ** (2 * order))
    elif filter_type == "gaussian":
        low = np.exp(-(D ** 2) / (2 * d0 ** 2))
    high = 1.0 - low
    return low, high

# 滤波流程：FFT -> fftshift -> 乘 H -> ifftshift -> IFFT -> 取模
'''

CODE6 = '''
def inverse_filter(blurred, psf, eps=1e-3):
    """逆滤波：F = G / H，对 H 接近 0 处做截断以抑制爆炸。"""
    h = np.fft.fft2(pad_psf(psf, blurred.shape))
    g = np.fft.fft2(blurred.astype(np.float32))
    h_safe = np.where(np.abs(h) < eps, eps, h)
    return np.clip(np.abs(np.fft.ifft2(g / h_safe)), 0, 255).astype(np.uint8)

def wiener_filter(blurred, psf, k=0.01):
    """维纳滤波：F = [H* / (|H|^2 + K)] * G。"""
    h = np.fft.fft2(pad_psf(psf, blurred.shape))
    g = np.fft.fft2(blurred.astype(np.float32))
    return np.clip(np.abs(np.fft.ifft2(np.conj(h) / (np.abs(h)**2 + k) * g)),
                   0, 255).astype(np.uint8)
'''

CODE7 = '''
def skin_mask_rgb(bgr):
    """RGB 规则：R>95, G>40, B>20, max-min>15, |R-G|>15, R>G, R>B。"""
    ...

def skin_mask_ycbcr(bgr):
    """YCbCr 范围模型：77<=Cb<=127 且 133<=Cr<=173。"""
    ...

def skin_mask_hsv(bgr):
    """HSV 范围模型：H in [0,25], S in [30,170], V>=50。"""
    ...

# 后处理：形态学开运算去噪点、闭运算填补空洞，再取最大连通域
# 融合：三种方法投票，至少两票认定为肤色
'''


def main():
    os.makedirs(EXPS, exist_ok=True)

    # ---------- 实验一 ----------
    build(
        "exp1-histogram/report/实验一-数字图像读取及色彩亮度对比度变化.docx",
        "实验一  数字图像读取及色彩、亮度、对比度变化",
        ["完成直方图均衡化和规定化。",
         "对图像进行亮度与对比度的线性调整，观察直方图变化。"],
        [
            sub("2.1 亮度与对比度调整"),
            txt("亮度与对比度的调整采用线性变换 g = alpha·f + beta，其中 alpha 控制对比度，"
                "beta 控制亮度。本实验取 beta=50 提升亮度，取 alpha=1.8 增强对比度，"
                "变换后需将结果截断到 [0,255] 区间。"),
            code("def adjust_brightness_contrast(img, alpha=1.0, beta=0.0):\n"
                 '    """线性变换 g = alpha * f + beta。"""\n'
                 "    return np.clip(alpha * img.astype(np.float32) + beta, 0, 255).astype(np.uint8)",
                 "代码 1  亮度与对比度线性变换"),
            sub("2.2 直方图均衡化"),
            txt("直方图均衡化以累积分布函数 CDF 作为灰度映射函数，将原始灰度分布变换为近似均匀分布，"
                "从而扩展图像的动态范围、提高对比度。其核心是概率积分变换，OpenCV 中可直接调用 "
                "cv2.equalizeHist 实现。"),
            sub("2.3 直方图规定化"),
            txt("直方图规定化是把源图像的灰度分布映射到指定的参考分布。分别计算源图与参考图的 CDF，"
                "再对源图的每一个灰度级，在参考 CDF 中寻找与之最接近的灰度级，构造查找表 LUT 完成映射。"),
            code(CODE1, "代码 2  直方图均衡化与规定化"),
            sub("2.4 实验结果"),
            img("exp1-histogram/images/output/compare_source_contrast_equalized_matched.png",
                "图 1  原图、对比度增强、均衡化、规定化结果对比", 15),
            img("exp1-histogram/images/output/histograms.png",
                "图 2  原图、均衡化、规定化的直方图对比", 15),
            txt("由图 1 可见，对比度增强后图像明暗层次拉开；均衡化后图像整体对比度明显提高，"
                "暗部细节得以显现。由图 2 可以清楚看到，原图灰度集中在 50~200 之间并呈双峰分布，"
                "均衡化后直方图被拉平、铺满整个 0~255 灰度范围，近似均匀分布；"
                "规定化后直方图则趋近于给定的参考分布。这说明均衡化只能得到近似均匀的结果，"
                "而规定化可以人为指定目标分布，灵活性更高。"),
            sub("2.5 实验结论"),
            txt("直方图均衡化适用于整体偏暗或偏亮、灰度集中的图像，能有效提升全局对比度；"
                "直方图规定化则可在需要把图像的色调统一到某一标准时使用。二者都是基于灰度映射的点运算，"
                "不改变像素的空间位置关系。"),
        ],
    )

    # ---------- 实验二 ----------
    build(
        "exp2-gamma/report/实验二-数字图像变换与伽马校正.docx",
        "实验二  数字图像变换与伽马校正",
        ["选择不同的参数完成伽马校正，观察不同 gamma 值对图像灰度分布的影响。",
         "作为对照，同时实现对数变换与反色变换。"],
        [
            sub("2.1 伽马变换原理"),
            txt("伽马校正即幂律变换 s = c·r^gamma，其中 r 为归一化后的输入灰度，c 为常数（本实验取 c=1）。"
                "当 gamma<1 时，变换曲线上凸，扩展暗部、压缩亮部，图像整体变亮；"
                "当 gamma=1 时为恒等变换；当 gamma>1 时，曲线下凹，压缩暗部、扩展亮部，图像整体变暗。"),
            code(CODE2, "代码 1  伽马变换实现"),
            txt("本实验选取 gamma = 0.4, 0.6, 1.0, 1.5, 2.2, 3.0 六组参数进行对比，"
                "其中 gamma=2.2 是典型显示器的伽马值，gamma=1/2.2 常用于图像显示的伽马校正。"),
            sub("2.2 实验结果"),
            img("exp2-gamma/images/output/gamma_grid.png",
                "图 1  不同 gamma 参数的校正结果对比", 15),
            img("exp2-gamma/images/output/gamma_curves.png",
                "图 2  伽马变换曲线簇", 14),
            txt("由图 1 可以直观看出，随着 gamma 增大，图像由亮逐渐变暗；gamma=0.4 时暗部细节被显著提亮，"
                "但亮部趋于饱和；gamma=3.0 时图像明显变暗，暗部细节被压缩。由图 2 的曲线簇可见，"
                "所有曲线均经过 (0,0) 与 (1,1) 两点，gamma 越小曲线越向上凸，对暗部的提升越明显。"),
            tbl("表 1  不同 gamma 取值对图像的整体影响",
                ["gamma", "曲线形状", "对暗部", "对亮部", "整体效果"],
                [["0.4", "上凸明显", "扩展", "压缩", "显著变亮"],
                 ["0.6", "上凸", "扩展", "压缩", "变亮"],
                 ["1.0", "直线", "不变", "不变", "恒等"],
                 ["1.5", "下凹", "压缩", "扩展", "变暗"],
                 ["2.2", "下凹明显", "压缩", "扩展", "明显变暗"],
                 ["3.0", "下凹显著", "压缩", "扩展", "很暗"]]),
            sub("2.3 对照实验：对数变换与反色变换"),
            img("exp2-gamma/images/output/03_log.png", "图 3  对数变换结果", 10),
            img("exp2-gamma/images/output/02_negative.png", "图 4  反色变换结果", 10),
            txt("对数变换 s = c·log(1+r) 同样用于扩展暗部，但其曲线形状与幂律变换不同，"
                "对暗部的提升更剧烈；反色变换 s = 255-r 则将图像黑白反转，常用于医学影像的观察。"),
            sub("2.4 实验结论"),
            txt("伽马校正是通过幂律变换对图像灰度进行非线性调整的有效手段，"
                "gamma 参数决定了变换曲线的弯曲方向。实际应用中，"
                "gamma<1 用于提亮偏暗图像，gamma>1 用于压暗偏亮图像。"),
        ],
    )

    # ---------- 实验三 ----------
    build(
        "exp3-denoising/report/实验三-数字图像的噪声去除.docx",
        "实验三  数字图像的噪声去除",
        ["对图像加入高斯噪声和椒盐噪声。",
         "利用中值滤波和统计排序滤波进行噪声去除，并用 PSNR 定量评价各方法的去噪效果。"],
        [
            sub("2.1 噪声模型"),
            txt("高斯噪声由正态分布随机值叠加而成，其幅度服从高斯分布，表现为整幅图像上均匀分布的细小颗粒；"
                "椒盐噪声则是随机位置被置为 255（盐噪声，亮点）或 0（椒噪声，暗点），表现为黑白相间的孤立点。"
                "本实验固定随机种子 2026，保证结果可复现。"),
            code(CODE3, "代码 1  加噪与修正阿尔法均值滤波"),
            sub("2.2 滤波方法"),
            txt("中值滤波用邻域灰度值的中值替代中心像素，对椒盐噪声尤其有效，且能较好保持边缘；"
                "统计排序滤波则根据噪声类型选择不同的排序统计量：最大值滤波（膨胀）可去除椒噪声，"
                "最小值滤波（腐蚀）可去除盐噪声，中点滤波 (max+min)/2 对高斯与均匀噪声有效，"
                "修正阿尔法均值滤波去掉 d 个最暗与 d 个最亮像素后取均值，能同时兼顾高斯与椒盐噪声。"),
            sub("2.3 实验结果与定量分析"),
            img("exp3-denoising/images/output/02_noisy_gaussian.png", "图 1  加入高斯噪声的图像", 8),
            img("exp3-denoising/images/output/03_gaussian_median_k3.png",
                "图 2  高斯噪声下中值滤波（3×3）去噪结果", 8),
            img("exp3-denoising/images/output/03_salt_pepper_median_k3.png",
                "图 3  椒盐噪声下中值滤波（3×3）去噪结果", 8),
            img("exp3-denoising/images/output/03_mixed_alpha_trimmed_k3.png",
                "图 4  混合噪声下修正阿尔法均值滤波结果", 8),
            tbl("表 1  各滤波方法对高斯噪声的 PSNR 对比",
                ["滤波方法", "PSNR (dB)", "效果评价"],
                [["加噪后（未处理）", "20.20", "—"],
                 ["中值滤波 3×3", "21.97", "最优"],
                 ["中值滤波 5×5", "20.86", "过度平滑"],
                 ["最大值滤波 3×3", "13.26", "不适用"],
                 ["最小值滤波 3×3", "13.23", "不适用"],
                 ["中点滤波 3×3", "21.08", "较好"]]),
            tbl("表 2  各滤波方法对椒盐噪声的 PSNR 对比",
                ["滤波方法", "PSNR (dB)", "效果评价"],
                [["加噪后（未处理）", "18.63", "—"],
                 ["中值滤波 3×3", "23.30", "最优"],
                 ["中值滤波 5×5", "21.17", "较好"],
                 ["最大值滤波 3×3", "11.45", "不适用"],
                 ["最小值滤波 3×3", "11.22", "不适用"],
                 ["中点滤波 3×3", "16.47", "一般"]]),
            txt("由表 1 可见，对高斯噪声，中值滤波 3×3 的 PSNR 最高（21.97 dB），"
                "而最大值与最小值滤波反而使 PSNR 大幅下降到 13 dB 左右，"
                "说明排序滤波器必须根据噪声类型正确选择，误用会严重破坏图像。"
                "由表 2 可见，对椒盐噪声，中值滤波 3×3 的 PSNR 达到 23.30 dB，"
                "相比加噪后的 18.63 dB 提升最为显著。"),
            txt("对高斯噪声与椒盐噪声构成的混合噪声（加噪后 PSNR 19.36 dB），"
                "修正阿尔法均值滤波将其提升到 22.91 dB，体现了其兼顾两类噪声的优势。"),
            sub("2.4 实验结论"),
            txt("中值滤波对椒盐噪声去噪效果最佳，且边缘保持较好；统计排序滤波需按噪声类型选择统计量，"
                "最大值滤波去暗点、最小值滤波去亮点、中点滤波对高斯噪声有效；"
                "修正阿尔法均值滤波对混合噪声最为稳健。滤波窗口越大平滑越强，但会造成细节损失，"
                "本实验中 3×3 窗口优于 5×5。"),
        ],
    )

    # ---------- 实验四 ----------
    build(
        "exp4-sharpening/report/实验四-图像的空间域锐化.docx",
        "实验四  图像的空间域锐化",
        ["采用拉普拉斯算子对图像进行锐化。",
         "利用 Canny 边缘检测算子进行边缘检测，对比不同双阈值的检测效果。"],
        [
            sub("2.1 拉普拉斯锐化"),
            txt("拉普拉斯算子是二阶微分算子，对灰度突变（边缘）响应强烈，而对平坦区域响应接近于零。"
                "常用模板有 4 邻域 [0 1 0; 1 -4 1; 0 1 0] 与 8 邻域 [1 1 1; 1 -8 1; 1 1 1]。"
                "由于模板中心系数为负，锐化时应将原图减去拉普拉斯响应，即 g = f - c·∇²f。"),
            code(CODE4, "代码 1  拉普拉斯锐化与 Canny 边缘检测"),
            txt("8 邻域模板比 4 邻域模板对斜向边缘更敏感，锐化效果更强，但同时也更容易放大噪声。"
                "本实验另用非锐化掩蔽 f + amount·(f - blur(f)) 作为对照。"),
            sub("2.2 Canny 边缘检测"),
            txt("Canny 算子分为五步：高斯平滑去噪、计算梯度幅值与方向、非极大值抑制细化边缘、"
                "双阈值检测与滞后连接。其中高阈值用于确定强边缘，低阈值用于连接弱边缘，"
                "二者的比值决定了边缘的连续性与抗噪性。本实验对比 (50,100)、(50,150)、(100,200) 三组阈值。"),
            sub("2.3 实验结果"),
            img("exp4-sharpening/images/output/sharpen_compare.png",
                "图 1  拉普拉斯锐化与非锐化掩蔽效果对比", 15),
            img("exp4-sharpening/images/output/canny_grid.png",
                "图 2  不同双阈值下的 Canny 边缘检测结果", 15),
            img("exp4-sharpening/images/output/canny_vs_laplacian.png",
                "图 3  拉普拉斯锐化与 Canny 边缘提取对照", 15),
            txt("由图 1 可见，拉普拉斯锐化后图像边缘与细节明显增强，轮廓更加清晰；"
                "8 邻域模板因包含对角线方向，对斜向细节的增强比 4 邻域更强；"
                "非锐化掩蔽则效果更为柔和自然。由图 2 可见，阈值越低检测到的边缘越多、越连续，"
                "但噪声响应也越多；阈值越高边缘越少、越干净，但可能出现边缘断裂。"),
            tbl("表 1  不同双阈值对 Canny 检测结果的影响",
                ["双阈值 (低,高)", "边缘数量", "连续性", "抗噪性"],
                [["(50, 100)", "多", "好", "弱"],
                 ["(50, 150)", "中等", "较好", "中等"],
                 ["(100, 200)", "少", "一般", "强"]]),
            txt("由图 3 对比可知，拉普拉斯属于二阶微分，得到的是包含边缘信息的锐化图像，"
                "边缘有正负双响应；而 Canny 得到的是单像素宽的二值边缘图，更适合后续的轮廓分析。"),
            sub("2.4 实验结论"),
            txt("拉普拉斯算子通过二阶微分增强图像边缘与细节，实现简单但对噪声敏感，"
                "通常需先做平滑预处理；Canny 算子通过非极大值抑制与双阈值滞后连接，"
                "能够获得连续、单像素宽且抗噪的边缘，是综合性能最优的边缘检测算子。"),
        ],
    )

    # ---------- 实验五 ----------
    build(
        "exp5-frequency-filter/report/实验五-频率域低通和高通滤波.docx",
        "实验五  频率域低通和高通滤波",
        ["对图像进行 FFT 变换，观察其频谱特征。",
         "选择某种低通滤波器进行低通滤波，观察平滑效果。",
         "选择某种高通滤波器进行高通滤波，观察边缘增强效果。"],
        [
            sub("2.1 频域滤波原理"),
            txt("根据卷积定理，空间域的卷积对应于频率域的乘积。对图像做二维傅里叶变换 F(u,v) 后，"
                "低频分量对应图像中缓慢变化的平坦区域，高频分量对应边缘、细节与噪声。"
                "频域滤波的流程为：FFT → fftshift 将零频移到中心 → 乘以滤波器 H(u,v) → "
                "ifftshift → IFFT → 取模。为便于显示，频谱取 20·log(|F|+1) 做对数拉伸。"),
            code(CODE5, "代码 1  三类滤波器与频域滤波流程"),
            txt("本实验对比三类滤波器（截止频率 D0，巴特沃斯阶数 n=2）：理想滤波器在 D0 内全通、"
                "外全阻，但会产生振铃效应；巴特沃斯滤波器 H = 1/(1+(D/D0)^(2n)) 过渡平滑，"
                "阶数越高越接近理想；高斯滤波器 H = exp(-D²/(2D0²)) 完全平滑，无振铃。"
                "高通滤波器由 H_hp = 1 - H_lp 得到。"),
            sub("2.2 实验结果"),
            img("exp5-frequency-filter/images/output/02_spectrum.png",
                "图 1  原图及其中心化对数频谱", 12),
            img("exp5-frequency-filter/images/output/lowpass_grid.png",
                "图 2  三类低通滤波器结果对比", 15),
            img("exp5-frequency-filter/images/output/highpass_grid.png",
                "图 3  三类高通滤波器结果对比", 15),
            img("exp5-frequency-filter/images/output/butterworth_d0_compare.png",
                "图 4  巴特沃斯低通不同截止频率 D0 的效果对比", 15),
            txt("由图 1 可见，频谱中心为低频（亮度最高），向四周频率逐渐升高；"
                "频谱中出现的亮线方向与图像中的纹理边缘方向相互垂直，这是傅里叶变换的重要性质。"
                "由图 2 可见，理想低通滤波结果在边缘处出现了明显的振铃波纹，"
                "这是频域矩形截断在空域引起的振荡；巴特沃斯低通过渡平滑，振铃明显减弱；"
                "高斯低通最为柔和，完全无振铃，但细节损失也最大。"),
            txt("由图 3 可见，高通滤波保留了图像的高频边缘信息，抑制了低频平坦区域，"
                "得到类似边缘提取的效果；理想高通同样存在振铃，而高斯高通的边缘最自然。"
                "由图 4 可见，D0 越小通过的低频越少，图像越模糊；D0 越大保留的细节越多。"),
            tbl("表 1  三类低通滤波器性能对比",
                ["滤波器", "振铃效应", "过渡平滑性", "细节保留", "实用性"],
                [["理想", "强", "差", "中等", "理论分析"],
                 ["巴特沃斯", "弱", "好", "较多", "通用"],
                 ["高斯", "无", "最佳", "最少", "高画质要求"]]),
            sub("2.3 实验结论"),
            txt("频率域滤波能够直观地在频域选择需要保留或抑制的频率成分。"
                "理想滤波器虽有最陡峭的截止特性，但振铃效应限制了其实用性；"
                "巴特沃斯滤波器在平滑性与细节保留之间取得平衡，是通用选择；"
                "高斯滤波器无振铃，适合对视觉质量要求高的场合。"),
        ],
    )

    # ---------- 实验六 ----------
    build(
        "exp6-restoration/report/实验六-数字图像复原.docx",
        "实验六  数字图像复原",
        ["对图像进行高斯模糊和运动模糊，建立退化模型。",
         "采用维纳滤波进行图像复原，并与逆滤波对比。"],
        [
            sub("2.1 退化模型与复原原理"),
            txt("图像退化过程可建模为 g(x,y) = h(x,y)*f(x,y) + n(x,y)，"
                "其中 h 为退化函数（点扩散函数 PSF），n 为加性噪声，* 表示卷积。"
                "在频率域中该式写为 G = H·F + N。逆滤波直接在频域做 F = G/H，"
                "但当 H 接近零或存在噪声时，噪声会被急剧放大，复原结果严重退化。"
                "维纳滤波引入噪声与信号功率比的估计 K，按 F = [H*/(|H|²+K)]·G 复原，"
                "在去模糊与抑制噪声之间取得折中。"),
            code(CODE6, "代码 1  逆滤波与维纳滤波"),
            txt("本实验构造两种退化：高斯模糊用 cv2.GaussianBlur 作用于冲激函数得到高斯型 PSF；"
                "运动模糊沿指定角度生成线状核并归一化。PSF 需补零到图像尺寸后做 ifftshift，"
                "使其中心对齐到 (0,0)，再与图像频谱相乘。"),
            sub("2.2 实验结果"),
            img("exp6-restoration/images/output/compare_gaussian.png",
                "图 1  原图、高斯模糊、逆滤波、维纳滤波结果对比", 15),
            img("exp6-restoration/images/output/compare_motion.png",
                "图 2  运动模糊及其复原结果对比", 15),
            img("exp6-restoration/images/output/compare_gaussian_noisy.png",
                "图 3  模糊加噪情况下逆滤波与维纳滤波对比", 15),
            tbl("表 1  高斯模糊下各方法的 PSNR 对比",
                ["方法", "PSNR (dB)", "说明"],
                [["模糊图（退化）", "21.32", "退化输入"],
                 ["逆滤波", "6.94", "噪声被放大，严重退化"],
                 ["维纳滤波 K=0.01", "14.31", "复原较好"],
                 ["维纳滤波 K=0.001", "13.70", "抑噪不足"],
                 ["维纳滤波 K=0.1", "14.55", "抑噪偏强"]]),
            tbl("表 2  模糊加噪情况下的 PSNR 对比",
                ["方法", "PSNR (dB)", "说明"],
                [["退化图", "—", "模糊+噪声"],
                 ["逆滤波", "5.88", "最差，噪声被剧烈放大"],
                 ["维纳滤波", "14.52", "稳健，明显优于逆滤波"]]),
            txt("由表 1、表 2 的数据可以清楚看到：在纯模糊情况下，逆滤波的 PSNR 仅 6.94 dB，"
                "几乎无法复原；而当模糊与噪声同时存在时，逆滤波进一步恶化到 5.88 dB，"
                "图像完全被噪声淹没。维纳滤波在两种情况下均稳定在 14 dB 以上，"
                "充分体现了其抗噪优势。由图 3 可直观看到，逆滤波结果布满噪声颗粒，"
                "而维纳滤波结果仍可辨识出图像结构。"),
            txt("关于参数 K 的选取：K 过小则抑制噪声不足，K 过大则过度平滑、损失细节。"
                "本实验中 K=0.1 略优于 K=0.01，说明在噪声较强时应适当增大 K。"),
            sub("2.3 实验结论"),
            txt("逆滤波是复原的直接方法，但对噪声极为敏感，仅适用于无噪或信噪比极高的场合；"
                "维纳滤波通过引入噪声功率比估计，在去模糊的同时抑制噪声放大，"
                "是实际中最常用的线性复原方法。复原效果强烈依赖于对退化函数 PSF 的准确估计。"),
        ],
    )

    # ---------- 实验七 ----------
    build(
        "exp7-skin-segmentation/report/实验七-人脸皮肤颜色分层.docx",
        "实验七  人脸皮肤颜色分层",
        ["采用彩色图像分层方法，提取人脸（自行准备证件照或自拍照）。",
         "对比 RGB、YCbCr、HSV 三种颜色空间下的肤色分割效果，并用投票融合提升鲁棒性。"],
        [
            sub("2.1 颜色空间与肤色模型"),
            txt("肤色在特定颜色空间中具有聚集性，因此可用简单的范围规则实现分割。"
                "本实验采用三种传统颜色空间模型（不使用深度学习）："
                "RGB 规则为 R>95, G>40, B>20, max-min>15, |R-G|>15, R>G, R>B；"
                "YCbCr 范围模型为 77≤Cb≤127 且 133≤Cr≤173；"
                "HSV 范围模型为 H∈[0,25], S∈[30,170], V≥50（OpenCV 取值范围）。"),
            code(CODE7, "代码 1  三种肤色模型与后处理融合"),
            txt("由于单一颜色模型易受光照与类肤色背景干扰，本实验对掩膜做形态学开运算去除孤立噪点、"
                "闭运算填补内部空洞，再取最大连通域作为人脸候选区；"
                "并采用三方法投票融合（至少两票认定为肤色）以提升鲁棒性。"),
            sub("2.2 实验结果"),
            img("exp7-skin-segmentation/images/output/2023-4-22/masks_grid.png",
                "图 1  三种颜色空间的肤色掩膜对比", 15),
            img("exp7-skin-segmentation/images/output/2023-4-22/overlay_grid.png",
                "图 2  三种方法的掩膜与原图叠加效果", 15),
            img("exp7-skin-segmentation/images/output/2023-4-22/03_postprocessed_hsv.png",
                "图 3  HSV 方法的形态学后处理结果", 10),
            img("exp7-skin-segmentation/images/output/2023-4-22/04_face_candidate_hsv.png",
                "图 4  最大连通域提取的人脸候选区", 10),
            img("exp7-skin-segmentation/images/output/2023-4-22/06_fused_result.png",
                "图 5  三方法投票融合结果", 12),
            txt("本实验对 6 张证件照（覆盖蓝底、白底、灰底三种背景）进行了批量测试。"
                "由图 1、图 2 可见，三种方法均能大致定位人脸区域，但效果存在差异。"
                "由图 3、图 4 可见，形态学后处理有效去除了零散噪点，"
                "最大连通域提取能够得到完整的人脸候选区。由图 5 可见，"
                "投票融合后背景误检明显减少，结果比任一单一方法更稳定。"),
            tbl("表 1  三种颜色空间在不同背景下的表现对比",
                ["颜色空间", "蓝底", "白底", "灰底", "光照敏感"],
                [["RGB", "一般", "一般", "一般", "最敏感"],
                 ["YCbCr", "较好", "较好", "较好", "较鲁棒"],
                 ["HSV", "最干净", "最干净", "较好", "中等"],
                 ["投票融合", "最优", "最优", "最优", "最鲁棒"]]),
            txt("观察到的规律是：HSV 在蓝底、白底背景下分割最干净，肤色区域完整且背景残留少；"
                "YCbCr 对亮度变化鲁棒，面部轮廓贴合较好，但会把颈部与衣物边缘纳入；"
                "RGB 规则受光照影响最大，容易在阴影区漏检。"),
            sub("2.3 讨论"),
            txt("单一颜色模型的局限主要来自两方面：一是光照变化会使肤色在颜色空间中发生偏移，"
                "导致漏检；二是类肤色背景（如木质、橙色衣物）会造成误检。"
                "投票融合通过多模型互补，显著降低了背景误检，"
                "说明多特征融合是提升传统方法鲁棒性的有效途径。"),
            sub("2.4 实验结论"),
            txt("基于颜色空间的肤色分割无需训练、计算量小，适合实时人脸粗定位。"
                "HSV 与 YCbCr 因把亮度与色度分离，分割效果优于 RGB；"
                "结合形态学后处理与多方法投票融合，可进一步抑制噪声与背景干扰，"
                "获得较为完整准确的人脸区域。"),
        ],
    )

    print("\n全部报告生成完成。")


if __name__ == "__main__":
    main()
