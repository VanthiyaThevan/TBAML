# Export script for package creation
import os
import shutil
from pathlib import Path

# Source and destination paths
src_root = Path(".")
dst_root = Path("D:/learning/SG_Hackathon/package_export")

# Files and directories to copy
copy_items = [
    "app/",
    "alembic/",
    "alembic.ini",
    "requirements.txt",
    "env.example",
]

# Create destination directory
dst_root.mkdir(parents=True, exist_ok=True)

# Copy files and directories
for item in copy_items:
    src = src_root / item
    dst = dst_root / item
    # Skip missing items but report them
    if not src.exists():
        print(f"Warning: source item not found, skipping: {src}")
        continue

    if src.is_dir():
        # remove existing destination to ensure clean copy
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

print("Package export complete!")