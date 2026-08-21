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
PID_FILE = BASE_DIR / "data" / "server.pid"
APP_WINDOW_TITLE = "Season_Fight · 学习监督"


def is_port_in_use(port):
    """检测端口是否被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def save_server_pid(pid):
    """记录本启动器创建的后端进程，供停止器精准关闭。"""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid), encoding="utf-8")


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
        process = subprocess.Popen(
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
            save_server_pid(process.pid)
            return True

    show_msgbox("错误", "后端启动超时，请查看端口 1224 是否被占用")
    return False


def focus_existing_app_window():
    """找到已打开的 Season Fight 窗口并将其恢复到前台。"""
    if os.name != "nt":
        return False

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        found = False

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def visit_window(hwnd, _):
            nonlocal found
            if not user32.IsWindowVisible(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True

            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, len(title))
            if title.value != APP_WINDOW_TITLE:
                return True

            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
            found = True
            return False

        user32.EnumWindows(visit_window, 0)
        return found
    except Exception:
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


def _get_windows_desktop_path():
    """读取 Windows 为当前用户配置的桌面路径。"""
    if os.name != "nt":
        return None

    try:
        import ctypes

        buffer = ctypes.create_unicode_buffer(260)
        CSIDL_DESKTOPDIRECTORY = 0x0010
        result = ctypes.windll.shell32.SHGetFolderPathW(
            None, CSIDL_DESKTOPDIRECTORY, None, 0, buffer
        )
        if result == 0 and buffer.value:
            return Path(buffer.value)
    except Exception:
        pass
    return None


def get_desktop_path():
    """优先使用系统桌面目录；无法读取时采用常见默认位置。"""
    return _get_windows_desktop_path() or Path.home() / "Desktop"


def ensure_desktop_shortcut():
    """自动确保当前用户桌面有 Season_Fight 快捷方式。"""
    desktop = get_desktop_path()

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


def launch_app():
    """启动后端；已有窗口时只唤醒它，不重复创建窗口。"""
    if start_backend() and not focus_existing_app_window():
        open_edge()


if __name__ == "__main__":
    # 1. 确保桌面快捷方式
    ensure_desktop_shortcut()

    # 2. 启动后端，并打开或唤醒应用窗口
    launch_app()
