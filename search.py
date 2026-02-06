import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
import sqlite3
import os
import platform
import subprocess
import sys
import pyperclip
from pathlib import Path

class FootprintsSearchUI:
    def __init__(self, db_path=None):
        # データベースパスの設定
        if db_path is None:
            base = Path(__file__).resolve().parent
            self.db_path = str(base / "data" / "footprints.db")
        else:
            self.db_path = db_path

        self.root = tk.Tk()
        self.root.title("Footprints Navigator")
        
        # ウィンドウの多重起動防止（タイトルで見つける）
        self._raise_if_already_open()

        self.root.geometry("1000x600")
        self.root.minsize(900, 500)

        # 状態管理
        self.order_key = "last_visit_desc"
        self.user_widths = {}
        self.current_os = platform.system()

        self._setup_style()
        self._setup_ui()
        self.search()

        # イベント
        self.root.bind("<Configure>", self._on_resize)
        self.entry.focus_set() # 起動時に検索窓にカーソル

    def _raise_if_already_open(self):
        """
        Windows環境で、既に同じタイトルのウィンドウがあればそれを前面に出して終了する。
        (Macの場合はOS標準の挙動に任せるか、別実装が必要)
        """
        if self.current_os == "Windows":
            try:
                import ctypes
                hwnd = ctypes.windll.user32.FindWindowW(None, "Footprints Navigator")
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 9) # SW_RESTORE
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                    sys.exit(0)
            except:
                pass

    def _setup_style(self):
        style = ttk.Style()
        # OSごとの標準フォント
        self.base_font = "Helvetica" if self.current_os == "Darwin" else "Segoe UI"
        theme = "aqua" if self.current_os == "Darwin" else "clam"

        try:
            style.theme_use(theme)
        except:
            pass

        style.configure("Treeview", font=(self.base_font, 11), rowheight=30)
        style.configure("Treeview.Heading", font=(self.base_font, 11, "bold"))
        style.map("Treeview", background=[("selected", "#0078D7" if self.current_os == "Windows" else "#0058D2")])

    def _setup_ui(self):
        # 検索エリア
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=15, pady=15)

        ttk.Label(top, text="🔍 Search:", font=(self.base_font, 11)).pack(side="left")
        self.entry = ttk.Entry(top, font=(self.base_font, 12))
        self.entry.pack(side="left", fill="x", expand=True, padx=(10, 10))
        self.entry.bind("<KeyRelease>", lambda e: self.search()) # リアルタイム検索

        # 表示エリア
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        cols = ("Name", "Type", "Count", "LastVisit", "Path")
        self.tree = ttk.Treeview(container, columns=cols, show="headings", selectmode="browse")
        
        # ヘッダー (クリックでソート)
        headers = {"Name": "名前", "Type": "種別", "Count": "回数", "LastVisit": "最終訪問", "Path": "パス"}
        for c, text in headers.items():
            self.tree.heading(c, text=text, command=lambda _c=c: self.sort_column(_c))
        
        # 列幅設定
        self.tree.column("Name", width=200, stretch=False)
        self.tree.column("Type", width=100, stretch=False, anchor="center")
        self.tree.column("Count", width=60, stretch=False, anchor="center")
        self.tree.column("LastVisit", width=160, stretch=False, anchor="center")
        self.tree.column("Path", width=400, stretch=True)

        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.root, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        hsb.pack(side="bottom", fill="x")

        # バインド
        self.tree.bind("<Double-1>", self._open_item)
        self.tree.bind("<Return>", self._open_item)
        
        # 右クリック対応 (Win/Mac)
        rc_event = "<Button-2>" if self.current_os == "Darwin" else "<Button-3>"
        self.tree.bind(rc_event, self._show_context_menu)
        if self.current_os == "Darwin": # Macは右クリックの別の書き方もカバー
            self.tree.bind("<Control-1>", self._show_context_menu)

        self.status = tk.StringVar()
        ttk.Label(self.root, textvariable=self.status, font=(self.base_font, 9)).pack(side="left", padx=15, pady=5)

    def search(self):
        query = self.entry.get()
        # SQLインジェクション対策は?を使えば万全
        word = f"%{query}%"

        order_map = {
            "name": "name COLLATE NOCASE ASC",
            "type": "type ASC",
            "visit_count": "visit_count DESC",
            "last_visit": "last_visit DESC",
            "path": "path ASC"
        }
        sql_order = order_map.get(self.order_key.replace("_desc", ""), "last_visit DESC")

        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(f"""
                    SELECT name, type, visit_count, last_visit, path 
                    FROM footprints 
                    WHERE name LIKE ? OR path LIKE ? 
                    ORDER BY {sql_order} LIMIT 300
                """, (word, word))
                rows = cur.fetchall()

            self.tree.delete(*self.tree.get_children())
            for r in rows:
                self.tree.insert("", "end", values=r)
            self.status.set(f"Displaying {len(rows)} items")
        except Exception as e:
            self.status.set(f"Error: {e}")

    def _open_item(self, _event=None):
        sel = self.tree.selection()
        if not sel: return
        path = self.tree.item(sel[0])["values"][4]
        
        if not Path(path).exists():
            messagebox.showwarning("Not Found", f"パスが存在しません:\n{path}")
            return

        if self.current_os == "Windows":
            os.startfile(path)
        else:
            subprocess.run(["open", path])

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="開く (Open)", command=self._open_item)
            menu.add_command(label="親フォルダを開く (Open Parent)", command=self._open_parent)
            menu.add_separator()
            menu.add_command(label="パスをコピー (Copy Path)", command=self._copy_path)
            menu.post(event.x_root, event.y_root)

    def _open_parent(self):
        sel = self.tree.selection()
        if not sel: return
        path = Path(self.tree.item(sel[0])["values"][4])
        parent = path.parent
        if self.current_os == "Windows":
            os.startfile(str(parent))
        else:
            subprocess.run(["open", str(parent)])

    def _copy_path(self):
        sel = self.tree.selection()
        if not sel: return
        path = self.tree.item(sel[0])["values"][4]
        pyperclip.copy(path)

    def sort_column(self, col):
        # 簡易ソート切り替え
        self.order_key = col.lower()
        self.search()

    def _on_resize(self, event):
        # パス列の自動伸縮
        if event.widget == self.root:
            self.root.update_idletasks()
            tw = self.tree.winfo_width()
            fixed = sum(self.tree.column(c, "width") for c in ("Name", "Type", "Count", "LastVisit"))
            if tw > fixed:
                self.tree.column("Path", width=tw - fixed - 20)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = FootprintsSearchUI()
    app.run()