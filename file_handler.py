from pathlib import Path
import shutil


def save_uploaded_file(uploaded_file, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / uploaded_file.name
    with open(dest, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return dest
