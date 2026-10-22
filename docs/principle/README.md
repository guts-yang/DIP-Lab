# 实验原理说明（PDF）

各实验 `PRINCIPLE.md` 的 PDF 版本，公式已用 LaTeX 渲染排版，可直接打印或提交。

| PDF | 对应实验 |
| --- | --- |
| [实验1-原理说明.pdf](实验1-原理说明.pdf) | [实验一 直方图均衡化与规定化](../../experiments/exp1-histogram) |
| [实验2-原理说明.pdf](实验2-原理说明.pdf) | [实验二 变换与伽马校正](../../experiments/exp2-gamma) |
| [实验3-原理说明.pdf](实验3-原理说明.pdf) | [实验三 噪声去除](../../experiments/exp3-denoising) |
| [实验4-原理说明.pdf](实验4-原理说明.pdf) | [实验四 空间域锐化](../../experiments/exp4-sharpening) |
| [实验5-原理说明.pdf](实验5-原理说明.pdf) | [实验五 频率域滤波](../../experiments/exp5-frequency-filter) |
| [实验6-原理说明.pdf](实验6-原理说明.pdf) | [实验六 图像复原](../../experiments/exp6-restoration) |
| [实验7-原理说明.pdf](实验7-原理说明.pdf) | [实验七 肤色分割](../../experiments/exp7-skin-segmentation) |

## 重新生成

修改 `PRINCIPLE.md` 后执行：

```bash
npm install          # 安装公式渲染依赖（katex）
python3 scripts/md_to_pdf.py
```

脚本读取 `experiments/expN-*/PRINCIPLE.md`，Markdown 与 LaTeX 经渲染后由本机 Chrome 打印为 A4 PDF，输出到本目录。
内容为离线生成，不依赖网络。
