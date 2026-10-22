#!/usr/bin/env python3
"""数字图像处理实验展示平台 —— 后端服务。

真实调用各实验脚本处理用户上传的图片，并把结果图返回前端。
启动： /usr/bin/python3 lab-showcase/server.py
"""

import os
import shutil
import subprocess
import sys
import time
import traceback
import uuid

from flask import Flask, jsonify, request, send_from_directory

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPS = os.path.join(ROOT, "experiments")
# 实时运行结果放在独立目录，不覆盖 experiments 里已归档的结果
RUNTIME = os.path.join(ROOT, "lab-showcase", "runtime")
os.makedirs(RUNTIME, exist_ok=True)

# 必须用带 cv2 的解释器
PY = "/usr/bin/python3"

app = Flask(__name__, static_folder=None)

# 实验配置：目录 -> (脚本名, 该实验的关键结果图)
CONF = {
    1: ("exp1-histogram",         "hist_equalization.py"),
    2: ("exp2-gamma",             "gamma_correction.py"),
    3: ("exp3-denoising",         "denoising.py"),
    4: ("exp4-sharpening",        "sharpening.py"),
    5: ("exp5-frequency-filter",  "frequency_filter.py"),
    6: ("exp6-restoration",       "restoration.py"),
    7: ("exp7-skin-segmentation", "skin_segmentation.py"),
}

# 各实验跑完后需要回传的结果图
KEY_FIGS = {
    1: ["compare_source_contrast_equalized_matched.png", "histograms.png",
        "01_source.png", "04_equalized.png", "06_matched.png"],
    2: ["gamma_grid.png", "gamma_curves.png", "01_source.png", "03_log.png"],
    3: ["02_noisy_gaussian.png", "03_gaussian_median_k3.png",
        "02_noisy_salt_pepper.png", "03_salt_pepper_median_k3.png",
        "03_mixed_alpha_trimmed_k3.png", "03_salt_pepper_max_k3.png",
        "02_noisy_mixed.png"],
    4: ["sharpen_compare.png", "canny_grid.png", "canny_vs_laplacian.png",
        "02_laplacian_response.png", "05_unsharp_mask.png", "01_source.png"],
    5: ["02_spectrum.png", "lowpass_grid.png", "highpass_grid.png",
        "butterworth_d0_compare.png", "filters_grid.png", "spectrum_vs_filters.png"],
    6: ["compare_gaussian.png", "compare_gaussian_noisy.png", "compare_motion.png",
        "wiener_k_compare_gaussian.png", "00_source.png"],
    7: ["masks_grid.png", "overlay_grid.png", "03_postprocessed_hsv.png",
        "04_face_candidate_hsv.png", "06_fused_result.png", "05_fused_vote.png"],
}

ALLOWED = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return resp


@app.route("/")
def index():
    return send_from_directory(os.path.join(ROOT, "lab-showcase"), "index.html")


@app.route("/runtime/<path:p>")
def runtime_file(p):
    """提供实时运行结果图。"""
    return send_from_directory(RUNTIME, p)


@app.route("/experiments/<path:p>")
def exp_file(p):
    """提供已归档的实验结果图（静态展示用）。"""
    return send_from_directory(EXPS, p)


@app.route("/api/run", methods=["POST", "OPTIONS"])
def run_exp():
    """接收上传图片，真实运行对应实验脚本，返回结果图。"""
    if request.method == "OPTIONS":
        return ("", 204)

    try:
        eid = int(request.form.get("exp", 0))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="实验编号无效"), 400

    if eid not in CONF:
        return jsonify(ok=False, error=f"不支持的实验 {eid}"), 400

    folder, script = CONF[eid]
    script_path = os.path.join(EXPS, folder, "code", script)
    if not os.path.exists(script_path):
        return jsonify(ok=False, error=f"脚本不存在：{script}"), 500

    # 保存上传图片；未上传则用内置合成图（脚本默认行为）
    img_arg = None
    f = request.files.get("image")
    if f and f.filename:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in ALLOWED:
            return jsonify(ok=False, error=f"不支持的图片格式 {ext}"), 400
        img_arg = os.path.join(RUNTIME, "uploads", f"{uuid.uuid4().hex}{ext}")
        os.makedirs(os.path.dirname(img_arg), exist_ok=True)
        f.save(img_arg)

    # 每个实验用独立任务目录承接输出，避免并发互相覆盖
    task = f"exp{eid}-{uuid.uuid4().hex[:8]}"
    out_dir = os.path.join(RUNTIME, task)
    os.makedirs(out_dir, exist_ok=True)

    # 关键：用环境变量把脚本的输出目录重定向到任务目录
    env = dict(os.environ)
    env["MPLBACKEND"] = "Agg"          # 无显示器时必须
    env["DIP_OUTPUT_DIR"] = out_dir     # 若脚本支持则生效

    cmd = [PY, script_path]
    if img_arg:
        cmd.append(img_arg)

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, cwd=os.path.dirname(script_path), env=env,
            capture_output=True, text=True, timeout=300,
        )
    except subprocess.TimeoutExpired:
        return jsonify(ok=False, error="运行超时（>300s）"), 504
    elapsed = time.time() - t0

    if proc.returncode != 0:
        return jsonify(ok=False, error="脚本运行失败",
                       stderr=proc.stderr[-2000:]), 500

    # 脚本默认写到 images/output，若未响应环境变量则去那里取
    archived = os.path.join(EXPS, folder, "images", "output")
    src_dir = out_dir if os.listdir(out_dir) else archived

    # 实验七是批量模式，结果落在以图片名命名的子目录
    if eid == 7:
        subs = [d for d in os.listdir(src_dir)
                if os.path.isdir(os.path.join(src_dir, d))]
        if subs:
            subs.sort()
            src_dir = os.path.join(src_dir, subs[-1])

    figs = []
    for name in KEY_FIGS.get(eid, []):
        fp = os.path.join(src_dir, name)
        if os.path.exists(fp):
            # 统一拷到任务目录，保证 URL 可访问
            dst = os.path.join(out_dir, name)
            if not os.path.exists(dst):
                shutil.copy2(fp, dst)
            figs.append({"name": name, "url": f"/runtime/{task}/{name}"})

    # 若有 PSNR 报告一并返回
    psnr = None
    for cand in (os.path.join(out_dir, "psnr_report.txt"),
                 os.path.join(archived, "psnr_report.txt")):
        if os.path.exists(cand):
            with open(cand, encoding="utf-8", errors="replace") as fh:
                psnr = fh.read()
            break

    if not figs:
        return jsonify(ok=False, error="未产生结果图",
                       stdout=proc.stdout[-1500:],
                       stderr=proc.stderr[-1500:]), 500

    return jsonify(ok=True, elapsed=round(elapsed, 2),
                   figs=figs, psnr=psnr, task=task,
                   stdout=proc.stdout[-800:])


@app.route("/api/health")
def health():
    return jsonify(ok=True, py=PY)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"实验展示平台启动： http://127.0.0.1:{port}")
    print(f"解释器：{PY}  （需带 cv2）")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
