#!/usr/bin/env python3
"""批量验证 7 个实验的实时运行接口。"""
import json
import os
import sys
import urllib.request
import uuid

BASE = "http://127.0.0.1:8765"
IMG = sys.argv[1] if len(sys.argv) > 1 else "data/standard/cameraman.png"


def post(eid, img=None):
    """用 multipart/form-data 调用 /api/run。"""
    b = uuid.uuid4().hex
    body = b""
    body += f"--{b}\r\nContent-Disposition: form-data; name=\"exp\"\r\n\r\n{eid}\r\n".encode()
    if img and os.path.exists(img):
        fn = os.path.basename(img)
        with open(img, "rb") as f:
            data = f.read()
        body += (f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; "
                 f"filename=\"{fn}\"\r\nContent-Type: image/png\r\n\r\n").encode()
        body += data + b"\r\n"
    body += f"--{b}--\r\n".encode()

    req = urllib.request.Request(
        BASE + "/api/run", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


ok = 0
for i in range(1, 8):
    try:
        j = post(i, IMG)
        if j.get("ok"):
            ok += 1
            n = len(j.get("figs", []))
            p = "有PSNR" if j.get("psnr") else ""
            print(f"实验{i}: ok  图{n}张  耗时{j['elapsed']}s  {p}")
        else:
            print(f"实验{i}: 失败  {j.get('error')}")
            if j.get("stderr"):
                print("    stderr:", j["stderr"][:300])
    except Exception as e:
        print(f"实验{i}: 异常 {e}")

print(f"\n通过 {ok}/7")
