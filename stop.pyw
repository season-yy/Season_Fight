# -*- coding: utf-8 -*-
"""Season_Fight 停止服务（无控制台窗口）"""
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PID_FILE = BASE_DIR / "data" / "server.pid"
CREATE_NO_WINDOW = 0x08000000


def read_server_pid():
    """读取启动器记录的后端进程 PID。"""
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def stop_server():
    """只停止 Season Fight 启动器记录的后端进程。"""
    pid = read_server_pid()
    if pid is None:
        return False, "没有找到 Season Fight 正在运行的记录。"

    try:
        result = subprocess.run(
            ["taskkill", "/F", "/PID", str(pid), "/T"],
            creationflags=CREATE_NO_WINDOW,
            capture_output=True,
            timeout=5,
        )
    except Exception as exc:
        return False, f"停止失败：{exc}"

    if result.returncode != 0:
        return False, "未能停止 Season Fight；它可能已经退出。"

    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass
    return True, "Season Fight 已停止。"


def show_message(message):
    """无控制台模式下，用系统消息框告知处理结果。"""
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, "Season Fight", 0x40)
    except Exception:
        pass

# 杀掉所有 pythonw.exe 进程（启动的是它）
if __name__ == "__main__":
    _, message = stop_server()
    show_message(message)
