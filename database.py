import sqlite3
import os
import platform
from pathlib import Path
from datetime import datetime

class FootprintsDB:
    """
    Footprints Navigator: データベース管理クラス
    - SQLite WALモードによる並列アクセスの最適化
    - 高速検索のためのインデックス設計
    - Windows/macOS 両対応のパス正規化
    """
    def __init__(self, db_path=None):
        if db_path is None:
            # 実行ファイルの階層に data フォルダを作成
            base = Path(__file__).resolve().parent
            self.db_path = base / "data" / "footprints.db"
        else:
            self.db_path = Path(db_path)
        
        # フォルダの自動生成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()

    def _get_connection(self):
        """タイムアウトを長めに設定し、書き込み待ちによるクラッシュを防止"""
        return sqlite3.connect(str(self.db_path), timeout=30)

    def _init_db(self):
        """初期設定（テーブル作成 & インデックス追加）"""
        with self._get_connection() as conn:
            # WALモード設定
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            
            # テーブル作成
            conn.execute('''
                CREATE TABLE IF NOT EXISTS footprints (
                    path TEXT PRIMARY KEY,
                    name TEXT,
                    type TEXT,
                    visit_count INTEGER DEFAULT 1,
                    last_visit DATETIME
                )
            ''')
            
            # 【重要】検索パフォーマンス向上のためのインデックス
            # 最終訪問日時でのソートを爆速にする
            conn.execute('CREATE INDEX IF NOT EXISTS idx_last_visit ON footprints(last_visit DESC);')
            # 名前でのあいまい検索を高速化
            conn.execute('CREATE INDEX IF NOT EXISTS idx_name ON footprints(name COLLATE NOCASE);')

    def record_anything(self, path_str: str):
        """
        パスをデータベースに記録または更新する。
        - 存在しないパスでも resolve(strict=False) で安全に処理。
        - Windows/Mac のパス形式を自動変換。
        """
        if not path_str:
            return

        try:
            # パスの正規化: expanduser (チルダ展開) と resolve (絶対パス化)
            # strict=False により、ファイルが削除された直後でもエラーにならない
            p = Path(path_str).expanduser().resolve(strict=False)
            full_path = str(p)
            
            # 基本情報の抽出
            name = p.name if p.name else full_path
            
            # 種別の判定ロジック
            if p.is_dir():
                ptype = "Folder"
            elif p.suffix.lower() == ".lnk":
                ptype = "Shortcut (Win)"
            elif p.suffix.lower() == ".url":
                ptype = "WebShortcut"
            else:
                ptype = "File"

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with self._get_connection() as conn:
                conn.execute('''
                    INSERT INTO footprints (path, name, type, visit_count, last_visit)
                    VALUES (?, ?, ?, 1, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        visit_count = visit_count + 1,
                        last_visit = excluded.last_visit,
                        name = excluded.name  -- ファイル名変更への追従
                ''', (full_path, name, ptype, now))
            
            # print(f"[DB] Recorded: {name}") # デバッグ時に有効化

        except Exception as e:
            # 監視スレッドを止めないようエラーをキャッチ
            print(f"[DB ERROR] Failed to record {path_str}: {e}")

    def get_stats(self):
        """（将来用）記録されている総件数などを取得"""
        with self._get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM footprints").fetchone()[0]

if __name__ == "__main__":
    # 動作確認用
    db = FootprintsDB()
    db.record_anything("./")
    print(f"Current records: {db.get_stats()}")