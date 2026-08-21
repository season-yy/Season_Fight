# -*- coding: utf-8 -*-
"""
Season_Fight 一键启动器（无控制台窗口）
- 检测端口是否已运行
- 用 pythonw.exe 后台启动 Flask 服务
- 用 Edge --app 模式打开独立窗口（无地址栏）
- 自动确保桌面有快捷方式
"""
import os
import sys
import subprocess
import time
import socket
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHONW = BASE_DIR / "venv" / "Scripts" / "pythonw.exe"
APP_PY = BASE_DIR / "app.py"
PORT = 1224


def is_port_in_use(port):
    """检测端口是否被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def start_backend():
    """启动 Flask 后端（用 pythonw.exe 无控制台）"""
    if not PYTHONW.exists():
        show_msgbox("错误", "Python 虚拟环境未安装！\n\n请先双击 start.bat 安装依赖")
        sys.exit(1)

    if is_port_in_use(PORT):
        return True  # 已在运行

    # 用 subprocess 启动 pythonw.exe（无控制台窗口）
    try:
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            [str(PYTHONW), str(APP_PY)],
            cwd=str(BASE_DIR),
            creationflags=CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        show_msgbox("错误", f"启动后端失败：{e}")
        return False

    # 等待服务启动
    for _ in range(20):
        time.sleep(0.5)
        if is_port_in_use(PORT):
            return True

    show_msgbox("错误", "后端启动超时，请查看端口 1224 是否被占用")
    return False


def open_edge():
    """用 Edge --app 模式打开独立窗口（无地址栏）"""
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]

    for edge in edge_paths:
        if os.path.exists(edge):
            try:
                subprocess.Popen(
                    [edge, "--app=http://localhost:1224",
                     "--window-size=480,820",
                     "--window-position=300,80"],
                    creationflags=0x08000000,
                )
                return
            except Exception:
                # --app 失败，尝试 URI scheme
                os.startfile("microsoft-edge:http://localhost:1224")
                return

    # 兜底：默认浏览器
    import webbrowser
    webbrowser.open("http://localhost:1224")


def ensure_desktop_shortcut():
    r"""自动确保桌面（D:\desk）有 Season_Fight 快捷方式"""
    # 用户实际桌面在 D:\desk
    desktop = Path(r"D:\desk")

    tmp_vbs = BASE_DIR / "_create_shortcut.vbs"
    base_escaped = str(BASE_DIR).replace("\\", "\\\\")
    icon_path = str(BASE_DIR / "static" / "favicon.ico").replace("\\", "\\\\")
    target = str(BASE_DIR / "start_app.pyw").replace("\\", "\\\\")

    cscript = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32" / "cscript.exe"

    if not desktop.exists():
        return

    lnk = desktop / "Season_Fight.lnk"
    if lnk.exists():
        return

    lnk_escaped = str(lnk).replace("\\", "\\\\")
    full_vbs = f'''
Dim lnk
Set lnk = CreateObject("WScript.Shell").CreateShortcut("{lnk_escaped}")
lnk.TargetPath = "{target}"
lnk.WorkingDirectory = "{base_escaped}"
lnk.IconLocation = "{icon_path}"
lnk.Description = "Season_Fight"
lnk.WindowStyle = 7
lnk.Save
'''
    tmp_vbs.write_text(full_vbs, encoding="utf-8")
    try:
        subprocess.run([str(cscript), "//nologo", str(tmp_vbs)],
                       creationflags=0x08000000, timeout=5,
                       capture_output=True)
    except Exception:
        pass

    try:
        tmp_vbs.unlink()
    except Exception:
        pass


def show_msgbox(title, msg):
    """简单的消息框（用 cscript 弹窗）"""
    import tempfile
    tmp = BASE_DIR / "_msg.vbs"
    tmp.write_text(f'MsgBox "{msg}", 48, "{title}"', encoding="utf-8")
    try:
        cscript = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32" / "cscript.exe"
        subprocess.run([str(cscript), "//nologo", str(tmp)],
                       creationflags=0x08000000, timeout=5)
    except Exception:
        pass
    finally:
        try:
            tmp.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    # 1. 确保桌面快捷方式
    ensure_desktop_shortcut()

    # 2. 启动后端
    if start_backend():
        # 3. 打开浏览器
        open_edge()