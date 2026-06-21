"""
ちいかわ「郎」ラーメンワールド 生成器（エントリポイント）。

  py -3.12 build/new_world.py

種ワールド生成 → 建物/二郎風内装/保護 → Behavior Pack → level.dat 作り込み
→ .mcworld 梱包 までを通しで行う。
"""
from __future__ import annotations

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import consts as C  # noqa: E402
from lib.worldgen import create_seed_world, write_level_dat  # noqa: E402
from lib.geom import WorldWriter  # noqa: E402
from lib.building import build_exterior  # noqa: E402
from lib.interior import build_interior  # noqa: E402
from lib.image_maps import import_image_maps, place_image_map_frames  # noqa: E402
from lib.protection import build_protection  # noqa: E402
from lib.behavior_pack import build_behavior_pack  # noqa: E402
from lib.packer import pack_mcworld  # noqa: E402

PROJECT = os.path.dirname(HERE)
WORK_DIR = C.WORK_DIR
DIST = os.path.join(PROJECT, "dist", "ChiikawaRamen.mcworld")


def main():
    t0 = time.time()
    print("== ちいかわ 郎 ラーメンワールド 生成 ==")
    print(f"GROUND_Y={C.GROUND_Y}  FEET_Y={C.FEET_Y}  CEIL_Y={C.CEIL_Y}")

    print("[1/6] 種ワールドを生成…")
    create_seed_world(WORK_DIR)

    print("[2/6] 建物・二郎風内装・保護を配置…")
    w = WorldWriter(WORK_DIR)
    build_exterior(w)
    build_interior(w)
    place_image_map_frames(w)
    build_protection(w)
    print("      保存中…")
    w.save()
    w.close()

    print("[3/6] Behavior Pack を生成…")
    build_behavior_pack(WORK_DIR)

    print("[4/6] level.dat を作り込み（Education 設定・スポーン・フラット地形）…")
    write_level_dat(WORK_DIR)

    print("[4.5/6] Image Map で左右の壁の地図画像を生成…")
    import_image_maps(WORK_DIR)

    print("[5/6] .mcworld へ梱包…")
    out = pack_mcworld(WORK_DIR, DIST)

    print("[6/6] 完了")
    size_kb = os.path.getsize(out) / 1024
    print(f"  → {out}  ({size_kb:.0f} KB)")
    print(f"  所要 {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
