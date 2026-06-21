"""
.mcworld への梱包。

ワールドフォルダの中身（level.dat / db/ / behavior_packs/ など）を
zip のルート直下に固めて .mcworld を作る。
"""
from __future__ import annotations

import os
import zipfile


def pack_mcworld(world_dir: str, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(world_dir):
            for name in files:
                full = os.path.join(root, name)
                # world_dir 直下を zip のルートにする
                arc = os.path.relpath(full, world_dir).replace(os.sep, "/")
                zf.write(full, arc)
    return out_path
