import os
import zipfile
from pathlib import Path
from utils.time import now_wib_str
from db.mongo import backups_col

BACKUP_ROOT = Path(os.getenv("BACKUP_FOLDER", "backups"))
BACKUP_ROOT.mkdir(exist_ok=True)

def create_backup(src_paths, prefix="backup"):
    timestamp = now_wib_str().replace(" ", "_").replace(":", "-")
    filename = f"{prefix}_{timestamp}.zip"
    output = BACKUP_ROOT / filename

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for src in src_paths:
            src = Path(src)
            if src.is_dir():
                for file in src.rglob("*"):
                    if file.is_file():
                        z.write(file, file.relative_to(src.parent))
            elif src.is_file():
                z.write(src, src.name)

    backups_col.insert_one({
        "file": str(output),
        "created_at": timestamp
    })

    return str(output)
