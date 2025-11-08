import os
import zipfile
from pathlib import Path
from db.mongo import backups_col
from datetime import datetime
from config import BACKUP_FOLDER

BACKUP_ROOT = Path(BACKUP_FOLDER or "backups")
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

def create_backup_zip(src_paths, prefix="backup"):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    name = f"{prefix}_{ts}.zip"
    dest = BACKUP_ROOT / name
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in src_paths:
            p = Path(p)
            if p.is_dir():
                for f in p.rglob('*'):
                    if f.is_file():
                        zf.write(f, arcname=f.relative_to(p.parent))
            elif p.is_file():
                zf.write(p, arcname=p.name)
    backups_col.insert_one({'file': str(dest), 'created_at': ts})
    return str(dest)

# simple coroutine starter for scheduled task (call with asyncio.create_task)
async def start_auto_backup():
    # minimal immediate backup once and return; scheduler handles periodic
    try:
        create_backup_zip(['./', 'db/'], prefix='init_backup')
        print("✅ Auto backup created")
    except Exception as e:
        print("backup error:", e)
