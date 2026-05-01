from pathlib import Path
import os

def get_project_root() -> Path:
    """
    Tìm thư mục gốc của dự án.
    """
    try:
        current_file = Path(__file__).resolve()
        current_dir = current_file.parent
    except NameError:
        current_dir = Path.cwd()

    for parent in [current_dir] + list(current_dir.parents):
        if (parent / 'src').exists() or (parent / '.gitignore').exists():
            return parent
    return current_dir

ROOT = get_project_root()

# --- Đường dẫn chuẩn (Path objects) ---
# Dùng toán tử / để nối đường dẫn: DATA_DIR / "file.csv"
DATA_DIR = ROOT / "database"
RAW_DATA_DIR = DATA_DIR
PROCESSED_DIR = ROOT / "output" / "processed"
OUTPUT_DIR = ROOT / "output"
FIG_DIR = OUTPUT_DIR / "figures"
TABLE_DIR = OUTPUT_DIR / "tables"

# Đảm bảo các thư mục tồn tại
for d in [DATA_DIR, PROCESSED_DIR, FIG_DIR, TABLE_DIR]:
    d.mkdir(parents=True, exist_ok=True)