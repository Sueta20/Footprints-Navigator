import platform
import time
import os
import threading
from database import FootprintsDB

# --- Windows専用ライブラリの遅延インポート ---
if platform.system() == "Windows":
    import win32com.client
    import pythoncom
    import glob
    from urllib.parse import urlparse, unquote

def file_url_to_path_win(u: str) -> str | None:
    if not u: return None
    pu = urlparse(u)
    if pu.scheme.lower() != "file": return None
    p = f"\\\\{pu.netloc}{pu.path}" if pu.netloc else pu.path
    p = unquote(p).replace("/", "\\")
    if len(p) >= 3 and p[0] == "\\" and p[2] == ":": p = p[1:]
    return p

def list_explorer_windows_win() -> dict[int, str]:
    mapping = {}
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        for w in shell.Windows():
            try:
                if "explorer.exe" not in (w.FullName or "").lower(): continue
                path = None
                try: path = w.Document.Folder.Self.Path
                except: path = file_url_to_path_win(w.LocationURL or "")
                if path and (os.path.isabs(path) or path.startswith("\\\\")):
                    mapping[int(w.HWND)] = path
            except: continue
    except: pass
    return mapping

def resolve_lnk_win(path: str) -> str:
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        return shell.CreateShortcut(path).TargetPath or path
    except: return path

# --- 監視メインループ ---

def monitor_windows(db: FootprintsDB):
    """Windows専用：エクスプローラーとRecentフォルダを監視"""
    pythoncom.CoInitialize()
    RECENT_DIR = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Recent')
    last_map = {}
    
    def get_recent_mtime():
        files = glob.glob(os.path.join(RECENT_DIR, "*.lnk")) + glob.glob(os.path.join(RECENT_DIR, "*.url"))
        if not files: return None, 0
        latest = max(files, key=os.path.getmtime)
        return latest, os.path.getmtime(latest)

    _, recent_last_mtime = get_recent_mtime()
    
    while True:
        try:
            # 1) エクスプローラー監視
            cur_map = list_explorer_windows_win()
            for hwnd, path in cur_map.items():
                if path != last_map.get(hwnd):
                    db.record_anything(path)
            last_map = cur_map

            # 2) Recent監視
            item, mtime = get_recent_mtime()
            if mtime > recent_last_mtime and item:
                if item.lower().endswith(".lnk"):
                    target = resolve_lnk_win(item)
                    if os.path.exists(target): db.record_anything(target)
                recent_last_mtime = mtime
        except Exception as e: print(f"WinMonitor Error: {e}")
        time.sleep(2)

def monitor_mac(db: FootprintsDB):
    """Mac専用：Finderの挙動監視（将来の拡張用）"""
    # 現時点では、Macで起動してもエラーにならないよう待機状態にする
    print("Mac Monitor logic goes here.")
    while True:
        time.sleep(10)

def start_monitoring(db):
    current_os = platform.system()
    target_func = monitor_windows if current_os == "Windows" else monitor_mac
    th = threading.Thread(target=target_func, args=(db,), daemon=True)
    th.start()