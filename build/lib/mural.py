"""
店内の壁画（クリスプ版）。

assets/characters/ の画像を「カスタムブロック＋リソースパック」で壁に貼る。
1 ブロック = 1 枚の高解像度テクスチャ（既定 64x64）なので、コンクリのドット絵より
はるかに鮮明にキャラが出る。画像が無い／Pillow が無い場合は panels.py の
ドット絵にフォールバックする。

仕組み:
  - Behavior Pack 側に blocks/<id>.json を置き、カスタムブロック jiro:<id> を定義。
  - Resource Pack 側に terrain_texture.json とタイル画像 textures/blocks/<id>.png を置く。
  - world_resource_packs.json で RP を有効化する。

向き（重要）:
  Bedrock の標準キューブ UV と方位から、ミラーにならない貼り付けを導出している。
    西の壁(x=-8, +X 面を内側から見る): 画像の左→右 が z=11→1（z = 11 - col）
    東の壁(x=+8, -X 面を内側から見る): 画像の左→右 が z=1→11（z = col + 1）
  どちらも上下は y=-54(上)→-59(下)。タイルの左右反転は不要。
"""
from __future__ import annotations

import json
import os

from . import consts as C

ASSET_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "characters")
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")

# リソースパック
RP_NAME = "chiikawa_jiro_rp"
RP_HEADER_UUID = "c2e1d8b3-5f40-4b21-8d32-88b1d1ffee20"
RP_MODULE_UUID = "c2e1d8b3-5f40-4b21-8d32-88b1d1ffee21"
RP_VERSION = [1, 0, 0]

# 壁画の寸法（panels.py と同じ領域: 幅11×高さ6, 客席側の左右の壁）
MURAL_W = 11
MURAL_H = 6
TILE_PX = 64                 # 1 ブロックあたりのテクスチャ解像度
Y_TOP = C.FEET_Y + (MURAL_H - 1)   # 最上段の y（-59 + 5 = -54）

# (壁の x, 壁の識別子)
WALLS = [
    (C.SHOP_X_MIN, "w"),   # 西の壁 ← 画像1枚目（ファイル名順の先頭）
    (C.SHOP_X_MAX, "e"),   # 東の壁 ← 画像2枚目
]


def _list_images():
    if not os.path.isdir(ASSET_DIR):
        return []
    files = [
        f for f in os.listdir(ASSET_DIR)
        if os.path.splitext(f)[1].lower() in _IMAGE_EXTS
    ]
    files.sort()
    return [os.path.join(ASSET_DIR, f) for f in files]


def _wall_pos(wall_letter, r, c):
    """タイル (row=r 上から, col=c 左から) → ワールド座標 (x, y, z)。"""
    y = Y_TOP - r
    if wall_letter == "w":           # 西の壁: 左→右 = z 11→1
        return C.SHOP_X_MIN, y, (MURAL_W - c)
    else:                            # 東の壁: 左→右 = z 1→11
        return C.SHOP_X_MAX, y, (c + 1)


def place_image_murals(w):
    """壁画をカスタムブロックで貼り、(block_id, PIL.Image) のリストを返す。
    画像や Pillow が無ければ panels.py のドット絵にフォールバックし [] を返す。"""
    try:
        from PIL import Image
    except Exception:
        from . import panels
        panels.place_character_panels(w)
        print("  [mural] Pillow 無し → ドット絵にフォールバック")
        return []

    images = _list_images()
    if not images:
        from . import panels
        panels.place_character_panels(w)
        print("  [mural] 画像無し → ドット絵にフォールバック")
        return []

    tiles = []
    used = []
    for i, (wall_x, wl) in enumerate(WALLS):
        if i >= len(images):
            break
        try:
            img = Image.open(images[i]).convert("RGB").resize(
                (MURAL_W * TILE_PX, MURAL_H * TILE_PX), Image.LANCZOS
            )
        except Exception as e:  # noqa: BLE001
            print(f"  [mural] {os.path.basename(images[i])}: 取り込み失敗 ({e})")
            continue
        for r in range(MURAL_H):
            for c in range(MURAL_W):
                tile = img.crop(
                    (c * TILE_PX, r * TILE_PX, (c + 1) * TILE_PX, (r + 1) * TILE_PX)
                )
                bid = f"m{wl}_{r}_{c}"
                x, y, z = _wall_pos(wl, r, c)
                w.set_block(x, y, z, f"{C.BP_NAMESPACE}:{bid}")
                tiles.append((bid, tile))
        used.append(os.path.basename(images[i]))
    if used:
        print(f"  [mural] 壁画(カスタムブロック)に使用: {', '.join(used)}")
    return tiles


def _block_def(bid):
    """カスタムブロック jiro:<bid> の Behavior Pack 定義（フルキューブ・不透明）。"""
    return {
        "format_version": "1.20.10",
        "minecraft:block": {
            "description": {"identifier": f"{C.BP_NAMESPACE}:{bid}"},
            "components": {
                "minecraft:material_instances": {
                    "*": {"texture": bid, "render_method": "opaque"}
                },
                "minecraft:light_dampening": 0,
            },
        },
    }


def write_mural_packs(world_path, tiles):
    """BP にカスタムブロック定義を、RP にテクスチャを書き出し、RP を有効化する。
    build_behavior_pack の後（BP ディレクトリ生成後）に呼ぶこと。"""
    if not tiles:
        return

    # --- Behavior Pack: blocks/<id>.json ---
    bp_root = os.path.join(world_path, "behavior_packs", C.BP_NAME)
    blocks_dir = os.path.join(bp_root, "blocks")
    os.makedirs(blocks_dir, exist_ok=True)
    for bid, _img in tiles:
        with open(os.path.join(blocks_dir, f"{bid}.json"), "w", encoding="utf-8") as f:
            json.dump(_block_def(bid), f, ensure_ascii=False, indent=2)

    # --- Resource Pack ---
    rp_root = os.path.join(world_path, "resource_packs", RP_NAME)
    tex_blocks = os.path.join(rp_root, "textures", "blocks")
    os.makedirs(tex_blocks, exist_ok=True)

    # manifest.json（resources モジュール）
    manifest = {
        "format_version": 2,
        "header": {
            "name": "ちいかわ 郎 ラーメン — 壁画テクスチャ",
            "description": "店内の壁画（キャラ画像）のリソースパック",
            "uuid": RP_HEADER_UUID,
            "version": RP_VERSION,
            "min_engine_version": [1, 20, 0],
        },
        "modules": [
            {"type": "resources", "uuid": RP_MODULE_UUID, "version": RP_VERSION}
        ],
    }
    with open(os.path.join(rp_root, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # terrain_texture.json（テクスチャキー → png）
    texture_data = {
        bid: {"textures": f"textures/blocks/{bid}"} for bid, _img in tiles
    }
    terrain = {
        "resource_pack_name": RP_NAME,
        "texture_name": "atlas.terrain",
        "padding": 0,
        "num_mip_levels": 0,
        "texture_data": texture_data,
    }
    with open(os.path.join(rp_root, "textures", "terrain_texture.json"), "w", encoding="utf-8") as f:
        json.dump(terrain, f, ensure_ascii=False, indent=2)

    # タイル画像（png）
    for bid, img in tiles:
        img.save(os.path.join(tex_blocks, f"{bid}.png"))

    # world_resource_packs.json（RP を有効化）— BP の空配列を上書きする
    wrp = [{"pack_id": RP_HEADER_UUID, "version": RP_VERSION}]
    with open(os.path.join(world_path, "world_resource_packs.json"), "w", encoding="utf-8") as f:
        json.dump(wrp, f, ensure_ascii=False, indent=2)

    print(f"  [mural] カスタムブロック {len(tiles)} 個 / RP テクスチャを書き出し")
