# -*- coding: utf-8 -*-
"""Season_Fight 停止服务（无控制台窗口）"""
import subprocess
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHONW = BASE_DIR / "venv" / "Scripts" / "pythonw.exe"

# 杀掉所有 pythonw.exe 进程（启动的是它）
try:
    subprocess.run(["taskkill", "/F", "/IM", "pythonw.exe", "/T"],
                   creationflags=0x08000000,
                   capture_output=True, timeout=5)
except Exception as e:
    print(f"停止失败：{e}", file=sys.stderr)

# 提示
try:
    subprocess.Popen(["cmd", "/c", "echo Season_Fight 已停止 ✓& pause"],
                   creationflags=0x08000000)
except Exception:
    pass