import platform
import subprocess
import sys
import pystray
from PIL import Image, ImageDraw
from database import FootprintsDB
from main import start_monitoring

def create_image():
    """タスクトレイアイコンの生成 (Win: 青, Mac: 黒)"""
    width, height = 64, 64
    image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    dc = ImageDraw.Draw(image)
    # OSによって色を変える
    main_color = (70, 130, 180) if platform.system() == "Windows" else (30, 30, 30)
    dc.ellipse([5, 5, 59, 59], fill=main_color)
    dc.ellipse([20, 20, 28, 28], fill=(255, 255, 255))
    dc.ellipse([36, 36, 44, 44], fill=(255, 255, 255))
    return image

def on_search(icon, item):
    # 実行環境のpythonを使ってsearch.pyを起動
    subprocess.Popen([sys.executable, "search.py"])

def on_exit(icon, item):
    icon.stop()

if __name__ == "__main__":
    db = FootprintsDB()
    
    # 監視スレッド開始 (OS自動判別)
    start_monitoring(db)

    # タスクトレイUI
    icon = pystray.Icon("Footprints", create_image(), "Footprints Navigator")
    icon.menu = pystray.Menu(
        pystray.MenuItem("検索を開く (Search)", on_search),
        pystray.MenuItem("終了 (Exit)", on_exit)
    )

    print(f"Footprints started on {platform.system()}")
    icon.run()