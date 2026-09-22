"""Stable source fingerprint available even when a container has no .git directory."""
import hashlib
from pathlib import Path


def build_id():
    root=Path(__file__).resolve().parents[1]
    digest=hashlib.sha256()
    for path in sorted([root/'app.py',*list((root/'regime').glob('*.py'))]):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes().replace(b'\r\n',b'\n'))
    return digest.hexdigest()[:12]
