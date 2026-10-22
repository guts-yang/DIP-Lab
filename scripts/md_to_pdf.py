#!/usr/bin/env python3
"""把各实验的 PRINCIPLE.md 渲染为 PDF，统一输出到 docs/principle/。

流程：Markdown -> HTML（LaTeX 用 KaTeX 预渲染） -> Chrome headless 打印为 PDF。
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "docs", "principle")
NODE = "/Users/chenyliao/Config/bin/node"
KATEX_JS = os.path.join(ROOT, "node_modules", "katex", "dist", "katex.min.js")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

EXPS = [
    ("exp1-histogram", "实验一 直方图均衡化与规定化"),
    ("exp2-gamma", "实验二 变换与伽马校正"),
    ("exp3-denoising", "实验三 噪声去除"),
    ("exp4-sharpening", "实验四 空间域锐化"),
    ("exp5-frequency-filter", "实验五 频率域滤波"),
    ("exp6-restoration", "实验六 图像复原"),
    ("exp7-skin-segmentation", "实验七 肤色分割"),
]

CSS = """
@page { size: A4; margin: 17mm 15mm 17mm 15mm; }
* { box-sizing: border-box; }
body {
  font-family: "STHeiti", "Hiragino Sans GB", "PingFang SC", sans-serif;
  font-size: 10.5pt; line-height: 1.72; color: #1a1a1a; margin: 0 auto;
}
h1 {
  font-size: 20pt; text-align: center; color: #0b3d6b;
  border-bottom: 2.5px solid #0b3d6b; padding-bottom: 10px;
  margin: 0 0 20px 0; page-break-after: avoid;
}
h2 {
  font-size: 14.5px; color: #0b3d6b; margin: 20px 0 9px 0;
  padding: 5px 0 5px 10px; border-left: 5px solid #0b3d6b;
  background: #f2f6fa; page-break-after: avoid;
}
h3 { font-size: 12.5px; color: #14507f; margin: 15px 0 6px 0; page-break-after: avoid; }
h4 { font-size: 11.5px; color: #333; margin: 12px 0 5px 0; page-break-after: avoid; }
p { margin: 7px 0; text-align: justify; }
ul, ol { margin: 7px 0; padding-left: 22px; }
li { margin: 3px 0; }
blockquote {
  margin: 9px 0; padding: 8px 13px; background: #fbf8ec;
  border-left: 4px solid #d4a017; color: #4a3c10; page-break-inside: avoid;
}
blockquote p { margin: 2px 0; }
code {
  font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 9pt;
  background: #f4f4f4; padding: 1px 5px; border-radius: 3px; color: #c7254e;
}
pre {
  background: #f7f8fa; border: 1px solid #dfe3e8; border-left: 3px solid #0b3d6b;
  padding: 9px 12px; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word;
  page-break-inside: avoid; margin: 10px 0;
}
pre code { background: none; padding: 0; color: #24292e; font-size: 8.5pt; }
table { border-collapse: collapse; width: 100%; margin: 11px 0; font-size: 9.5pt;
        page-break-inside: avoid; }
th, td { border: 1px solid #c3ccd6; padding: 5px 8px; text-align: left; }
th { background: #0b3d6b; color: #fff; font-weight: 600; }
tr:nth-child(even) td { background: #f6f8fa; }
hr { border: none; border-top: 1px dashed #c3ccd6; margin: 16px 0; }
strong { color: #0b3d6b; }
a { color: #0b3d6b; text-decoration: none; }
.eq-block { text-align: center; margin: 12px 0; page-break-inside: avoid;
            overflow-x: hidden; }
.eq-inline { display: inline; }
.katex { font-size: 1.05em; }
.katex-display { display: inline-block; margin: 0; text-align: center; }
.eq-raw { color: #a00; font-family: monospace; font-size: 9pt; }
"""


def katex_batch(pairs):
    """批量用 KaTeX 渲染：pairs=[(tex, display)]，返回 [html|None]。"""
    if not pairs:
        return []
    script = r"""
const katex = require('KATEX_PATH');
const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const out = input.map(function (item) {
  try {
    return katex.renderToString(item.tex, {
      displayMode: item.display,
      throwOnError: true,
      strict: false,
      trust: false,
      output: 'html'
    });
  } catch (e) {
    return null;
  }
});
console.log(JSON.stringify(out));
""".replace("KATEX_PATH", KATEX_JS)

    tmpf = os.path.join(tempfile.gettempdir(), "katex_batch.js")
    with open(tmpf, "w", encoding="utf-8") as f:
        f.write(script)

    payload = json.dumps([{"tex": t, "display": d} for t, d in pairs])
    r = subprocess.run([NODE, tmpf], input=payload, capture_output=True,
                       text=True, timeout=120)
    if r.returncode != 0:
        print("KaTeX 错误:", r.stderr[:300])
        return [None] * len(pairs)
    try:
        return json.loads(r.stdout)
    except Exception:
        return [None] * len(pairs)


def protect_math(text):
    slots = {}

    def save(tex, display):
        i = len(slots)
        slots[i] = (tex, display)
        return f"\x00MATH{i}\x00"

    text = re.sub(r"\$\$(.+?)\$\$", lambda m: save(m.group(1), True), text, flags=re.S)
    text = re.sub(r"(?<!\$)\$([^$\n]+?)\$(?!\$)", lambda m: save(m.group(1), False), text)
    return text, slots


def md_to_html(md_path, katex_css):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    text, slots = protect_math(text)

    body = markdown.markdown(
        text, extensions=["extra", "tables", "fenced_code", "sane_lists"]
    )

    # 批量渲染公式
    order = list(slots.keys())
    rendered = {}
    if order:
        res = katex_batch([slots[i] for i in order])
        for i, html in zip(order, res):
            rendered[i] = html

    def repl(m):
        i = int(m.group(1))
        if i not in slots:
            return m.group(0)
        tex, display = slots[i]
        h = rendered.get(i)
        if not h:
            esc = tex.replace("<", "&lt;").replace(">", "&gt;")
            cls = "eq-block" if display else "eq-inline"
            return f'<span class="{cls} eq-raw">${esc}$</span>'
        if display:
            return f'<div class="eq-block">{h}</div>'
        return f'<span class="eq-inline">{h}</span>'

    body = re.sub(r"\x00MATH(\d+)\x00", repl, body)
    nraw = body.count("eq-raw")

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>原理说明</title>
<style>{katex_css}</style>
<style>{CSS}</style></head>
<body>
{body}
</body></html>""", nraw


def html_to_pdf(html_path, pdf_path):
    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=8000",
        f"--print-to-pdf={pdf_path}",
        f"file://{html_path}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f"Chrome 失败: {r.stderr[:300]}")
    return os.path.exists(pdf_path)


def main():
    if not os.path.exists(CHROME):
        sys.exit("未找到 Google Chrome")
    if not os.path.exists(KATEX_JS):
        sys.exit("未找到 KaTeX，请先 npm install katex")
    os.makedirs(OUT_DIR, exist_ok=True)

    css_file = os.path.join(ROOT, "node_modules", "katex", "dist", "katex.min.css")
    with open(css_file, "r", encoding="utf-8") as f:
        katex_css = f.read()

    ok, failed = [], []
    tmp = tempfile.mkdtemp()
    try:
        for folder, title in EXPS:
            md = os.path.join(ROOT, "experiments", folder, "PRINCIPLE.md")
            if not os.path.exists(md):
                failed.append((folder, "缺少 PRINCIPLE.md"))
                continue
            num = folder.split("-")[0].replace("exp", "")
            pdf_name = f"实验{num}-原理说明.pdf"
            pdf = os.path.join(OUT_DIR, pdf_name)
            html = os.path.join(tmp, f"{folder}.html")
            try:
                h, nraw = md_to_html(md, katex_css)
                with open(html, "w", encoding="utf-8") as f:
                    f.write(h)
                html_to_pdf(html, pdf)
                size = os.path.getsize(pdf) / 1024
                if size < 5:
                    raise RuntimeError("PDF 过小")
                flag = f"  [未渲染:{nraw}]" if nraw else "  [公式全部渲染]"
                ok.append((pdf_name, size))
                print(f"  OK  {pdf_name}  ({size:.0f} KB){flag}")
            except Exception as e:
                failed.append((folder, str(e)))
                print(f"  FAIL {folder}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n完成 {len(ok)}，失败 {len(failed)} -> {OUT_DIR}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
