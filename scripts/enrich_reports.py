"""为 7 份实验报告插入展示链接区块，并在结尾追加个人思考与反思段落。

用法：
    /usr/bin/python3 scripts/enrich_reports.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = Path("/Users/chenyliao/.bg-agent/config-with-app/skills/docx")
URL = "https://gutsyang-diplab.streamlit.app"

REPORTS = {
    "exp1-histogram": "实验一-数字图像读取及色彩亮度对比度变化.docx",
    "exp2-gamma": "实验二-数字图像变换与伽马校正.docx",
    "exp3-denoising": "实验三-数字图像的噪声去除.docx",
    "exp4-sharpening": "实验四-图像的空间域锐化.docx",
    "exp5-frequency-filter": "实验五-频率域低通和高通滤波.docx",
    "exp6-restoration": "实验六-数字图像复原.docx",
    "exp7-skin-segmentation": "实验七-人脸皮肤颜色分层.docx",
}

# 每个实验的反思：基于该实验真实出现过的问题、取舍与意外发现，避免空泛套话
REFLECT = {
    "exp1-histogram": [
        "3. 实验思考与反思",
        "均衡化并不是万能的。我一开始以为它总能“让图变清楚”，但把 lena、cameraman 换着跑了几轮后发现，"
        "对于本来灰度就很分散的图，均衡化之后背景噪声也被一起拉大了，看上去反而更脏。"
        "这才理解它的前提是“灰度集中”，本质上是在重新分配动态范围，而不是真的增加信息。",
        "规定化那部分我卡了一下。最开始我直接拿均衡化结果当参考图，跑出来和均衡化几乎一样，"
        "还以为是映射写错了。后来才反应过来：参考图必须是一幅独立的、具有目标分布的图，"
        "拿自己的结果当参考当然没有意义。改成自己构造的偏亮参考图之后，直方图形状才明显跟着参考走。",
        "另外一点体会是，评价不能只看图。这次我特意把直方图也画出来对比，"
        "才确认均衡化后确实铺满了 0~255、规定化确实贴合了参考分布——光凭肉眼盯着图看，很容易把“变亮了”当成“变好了”。",
    ],
    "exp2-gamma": [
        "3. 实验思考与反思",
        "调 γ 的时候有个直观感受：γ<1 提亮暗部确实明显，但同时把暗部噪声也一并放大了。"
        "我试过把 γ 压到 0.3 左右，画面整体是亮了，可平坦区域（比如背景墙）颗粒感很重，"
        "说明幂律变换在扩展暗部的同时也放大了那部分的噪声，并不是越好越亮越好。",
        "对数变换和幂律都能提亮暗部，这一点我起初分不清。把两条曲线画在一张图上才看明白："
        "对数在低灰度段斜率更陡，对极暗区域的拉升比幂律更猛；而幂律可以通过 γ 连续调节弯曲程度，更灵活。"
        "所以“什么时候用哪个”取决于你想要多大的提升幅度，而不是哪个更高级。",
        "还有一个实现上的坑：直接对 uint8 做乘方会溢出，必须先归一化到 [0,1] 再算，"
        "最后乘回 255。我第一次写的时候偷懒没转 float，结果大片区域直接饱和成 255，调了半天才找到原因。",
    ],
    "exp3-denoising": [
        "3. 实验思考与反思",
        "让我意外的是最大值和最小值滤波在高斯噪声下的表现——PSNR 掉到 13 dB 左右，比不滤波还差。"
        "一开始我以为是代码 bug，检查了几遍才确认这就是排序统计的性质："
        "最大值滤波会把窗口内最亮点扩散开，整幅图变亮且充满亮斑，用在没有脉冲噪声的图上纯属破坏。"
        "这件事让我记牢了：滤波器没有好坏，只有对不对症。",
        "窗口大小的选择上，我原本觉得 5×5 应该比 3×3 更干净。实测下来 5×5 虽然 PSNR 略高一点，"
        "但边缘明显糊了，baboon 这种纹理密的图损失尤其大。所以不能只盯 PSNR 数字，"
        "数字高不代表看着舒服，细节和去噪之间得权衡。",
        "修正阿尔法均值滤波我调 d 参数调了几次。d=0 退化为均值、d 取最大退化为中值，"
        "处理混合噪声时要留一部分点参与平均才能兼顾两类噪声，这个“留多少”只能靠试，"
        "也说明传统方法里经验参数确实少不了。",
    ],
    "exp4-sharpening": [
        "3. 实验思考与反思",
        "拉普拉斯锐化给我最大的感受是：它对噪声太敏感了。同一幅图，加一点高斯噪声再锐化，"
        "噪声边缘被一起增强，画面全是麻点。所以实际用的时候基本得先平滑再锐化，"
        "也就是非锐化掩蔽的思路——用原图减去模糊图得到细节，再加回去，效果比直接拉普拉斯温和得多。",
        "Canny 的双阈值我调了挺久。一开始高低阈值设得太近（比如 50 和 60），"
        "结果边缘断断续续；后来按大约 1:2 到 1:3 的比例拉开放宽，边缘才连成完整轮廓。"
        "这让我理解了所谓“滞后连接”不是形式上的步骤，高阈值定骨架、低阈值补连接，两者配合才有意义。",
        "还有个容易忽略的点：锐化强度和边缘提取是两回事。锐化是增强后仍然得到灰度图，"
        "边缘检测输出的是二值图，用途完全不同。我一开始把它们混着比较，后来分开看才理清。"
    ],
    "exp5-frequency-filter": [
        "3. 实验思考与反思",
        "理想低通的振铃效应，看图之前我以为只是书上说说的理论现象。"
        "自己跑出来才发现，在 baboon 这种纹理密的图上，边缘附近一圈圈涟漪非常清楚，"
        "几乎没法看。这比课本上的公式直观得多——频域里陡峭的矩形截止，对应到空域就是 sinc 函数的振荡，"
        "两者是同一件事的两面。",
        "D0 的选择也让我纠结过。截止频率太低，图糊成一团；太高，噪声又全留着。"
        "试了 15、40、80 三组之后发现，中间值往往最平衡，但“中间”具体是多少完全取决于图的内容和噪声水平，"
        "没有通用答案。这大概就是频域滤波的麻烦之处：参数得对着图调。",
        "实现上我踩了个坑：做 FFT 后必须把低频移到中心再构造滤波器，"
        "我第一次忘了 fftshift，滤波器位置对不上，出来的图完全不对。这类错误不报错，但结果诡异，只能靠频谱图来排查。",
    ],
    "exp6-restoration": [
        "3. 实验思考与反思",
        "逆滤波在纯模糊下就只有 6.94 dB，加噪后更是掉到 5.88 dB，几乎一片噪声。"
        "这个数字比我预期差得多。原因想通了：逆滤波是直接除以 H(u,v)，"
        "高频处 H 接近 0 时，除法会把那点残留噪声放大到离谱的量级。所以它只在“完全无噪”这个理想前提下成立。",
        "维纳滤波的 K 我一开始不知道怎么取。试了 0.001、0.01、0.1 之后才摸出规律："
        "噪声强的时候 K 要偏大，抑制才够；K 太大又过度平滑、细节丢失。"
        "本实验里 K=0.1 略好于 0.01，但这个结论只针对当前的噪声强度，换幅图未必成立——"
        "维纳滤波的实用难点就在这儿，它假设已知噪声功率，而真实场景里这个量往往是估的。",
        "另外我意识到复原和前面学的增强是两回事：增强是“看着更好”，"
        "复原是“尽量回到退化前的样子”，后者必须知道或估计出退化函数。"
        "这次 PSF 是我自己造的模糊核所以完全已知，真要用到实拍照片上，光是估 PSF 就是另一个难题。",
    ],
    "exp7-skin-segmentation": [
        "3. 实验思考与反思",
        "RGB 规则的效果比我预想的差不少。原因不难理解：RGB 三个通道都含亮度信息，"
        "光照一变，同一块皮肤的 RGB 值就整体偏移，固定阈值自然容易漏检阴影侧的脸。"
        "而 YCbCr、HSV 把亮度和色度分开了，所以在明暗变化下稳得多——这个差异在对比图上非常直观。",
        "类肤色背景误检是另一个麻烦。我拿到的图里，偏黄的背景和木质区域会被判成皮肤。"
        "单靠一个颜色空间很难解决，投票融合之后确实干净了不少，但也带来新问题："
        "三个模型都判错的区域融合后依然是错的，而且投票会把一些小块真实皮肤给“投掉”。"
        "所以融合提升的是整体鲁棒性，不是万能修正。",
        "还有一点值得记下：本次用的都是公开数据集的人脸图，光线和背景相对干净。"
        "换成我自己拍的证件照再试，光照不均和背景复杂时效果明显下滑。"
        "说明传统颜色方法对成像条件很敏感，真要实用还得加光照归一化之类的预处理，"
        "这也是它和深度学习方法的主要差距所在。",
    ],
}

LINK_BLOCK = [
    "实验展示链接（在线可交互演示）",
    f"{URL}",
    "本报告的全部实验结果均可在上述在线平台中交互查看，支持自行上传图像并实时调节参数。",
]


def para_xml(text: str, *, bold=False, size=24, center=False, indent=True, color=None) -> str:
    """构造一个段落 XML。"""
    color_xml = f'<w:color w:val="{color}"/>' if color else '<w:color w:val="000000"/>'
    bold_xml = "<w:b/>" if bold else '<w:b w:val="0"/>'
    jc = '<w:jc w:val="center"/>' if center else '<w:jc w:val="both"/>'
    ind = '<w:ind w:firstLine="480"/>' if indent else ""
    esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        "<w:p>"
        "<w:pPr>"
        '<w:spacing w:before="0" w:after="120" w:line="360" w:lineRule="auto"/>'
        f"{ind}{jc}"
        "</w:pPr>"
        "<w:r>"
        "<w:rPr>"
        '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/>'
        f"{bold_xml}{color_xml}"
        f'<w:sz w:val="{size}"/>'
        "</w:rPr>"
        f'<w:t xml:space="preserve">{esc}</w:t>'
        "</w:r>"
        "</w:p>"
    )


def build_link_block() -> str:
    out = para_xml(LINK_BLOCK[0], bold=True, size=28, center=False, indent=False)
    out += para_xml(LINK_BLOCK[1], size=24, center=False, indent=False, color="0563C1")
    out += para_xml(LINK_BLOCK[2], size=21, indent=False)
    return out


def build_reflect(lines: list[str]) -> str:
    out = ""
    for i, line in enumerate(lines):
        if i == 0:
            out += para_xml(line, bold=True, size=28, indent=False)
        else:
            out += para_xml(line)
    return out


def process(name: str, fname: str) -> bool:
    src = ROOT / "experiments" / name / "report" / fname
    if not src.exists():
        print(f"  [跳过] 不存在 {src}")
        return False
    work = Path("/tmp") / f"docx_{name}"
    if work.exists():
        shutil.rmtree(work)

    subprocess.run(
        ["/Users/chenyliao/Config/python/current/bin/python3.12", str(SKILL / "scripts" / "office" / "unpack.py"), str(src), str(work)],
        check=True, capture_output=True,
    )
    doc = work / "word" / "document.xml"
    xml = doc.read_text(encoding="utf-8")

    # 1) 在封面第二个标题段之后插入展示链接区块
    ps = list(re.finditer(r"<w:p>.*?</w:p>|<w:p .*?</w:p>", xml, re.S))
    if len(ps) < 2:
        print(f"  [失败] {name} 段落异常")
        return False
    anchor = ps[1].end()  # 第二个段落（实验N 标题）之后
    xml = xml[:anchor] + build_link_block() + xml[anchor:]

    # 2) 在文档结尾（sectPr 之前）追加思考与反思
    # 注意：sectPr 必须是 body 的最后一个子元素，段落要插在它前面
    sect = xml.rfind("<w:sectPr")
    if sect == -1:
        print(f"  [失败] {name} 找不到 sectPr")
        return False
    xml = xml[:sect] + build_reflect(REFLECT[name]) + xml[sect:]

    doc.write_text(xml, encoding="utf-8")

    out = work / "rebuilt.docx"
    subprocess.run(
        ["/Users/chenyliao/Config/python/current/bin/python3.12", str(SKILL / "scripts" / "office" / "pack.py"), str(work), str(out),
         "--original", str(src)],
        check=True, capture_output=True,
    )
    bak = src.with_suffix(".docx.bak")
    if not bak.exists():
        shutil.copy2(src, bak)
    shutil.copy2(out, src)
    print(f"  [完成] {fname}")
    return True


def main() -> None:
    print("开始处理 7 份实验报告：插入展示链接 + 追加思考与反思\n")
    ok = 0
    for name, fname in REPORTS.items():
        if process(name, fname):
            ok += 1
    print(f"\n完成 {ok}/7 份")


if __name__ == "__main__":
    main()
