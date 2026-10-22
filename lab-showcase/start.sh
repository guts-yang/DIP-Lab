#!/bin/bash
# 启动数字图像处理实验展示平台
# 用法： bash start.sh  （默认端口 8765）
cd "$(dirname "$0")/.." || exit 1
PORT="${1:-8765}"
echo "启动实验展示平台..."
echo "解释器：/usr/bin/python3（需带 cv2）"
echo "访问： http://127.0.0.1:${PORT}"
MPLBACKEND=Agg /usr/bin/python3 lab-showcase/server.py "${PORT}"
