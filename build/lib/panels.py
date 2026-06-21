"""
ちいかわキャラクターの壁画（店内の左右の壁）。

2 通りで設置できる:
  1) build/assets/characters/ に画像（png/jpg/jpeg/webp）があれば Pillow で取り込み、
     背景を消してピクセルを一番近い色のコンクリブロックに置き換え、壁に貼る。
  2) 画像が無ければ、同梱のオリジナル・ドット絵を使う（原画テクスチャは埋め込まない）。

画像はファイル名順に、左（西）の壁→右（東）の壁の順で割り当てる。
"""
from __future__ import annotations

import os

from . import consts as C

ASSET_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "characters")

# --- ブロックの代表 RGB（Bedrock concrete の近似）---
CONCRETE_RGB = {
    "white_concrete": (207, 213, 214),
    "light_gray_concrete": (125, 125, 115),
    "gray_concrete": (54, 57, 61),
    "black_concrete": (8, 10, 15),
    "red_concrete": (142, 33, 33),
    "orange_concrete": (224, 97, 1),
    "yellow_concrete": (241, 175, 21),
    "lime_concrete": (94, 169, 24),
    "green_concrete": (73, 91, 36),
    "cyan_concrete": (21, 119, 136),
    "light_blue_concrete": (36, 137, 199),
    "blue_concrete": (45, 47, 143),
    "purple_concrete": (100, 32, 156),
    "magenta_concrete": (169, 48, 159),
    "pink_concrete": (214, 101, 143),
    "brown_concrete": (96, 60, 32),
}

# --- オリジナル・ドット絵パネル（top→bottom） ---
LEGEND = {
    "W": "white_concrete",
    "K": "black_concrete",
    "P": "pink_concrete",
    "B": "light_blue_concrete",
    "Y": "yellow_concrete",
    "R": "red_concrete",
    "G": "light_gray_concrete",
    ".": None,  # 透過（空気）
}

CHIIKAWA = [
    "..WWW..",
    ".WWWWW.",
    "WWWWWWW",
    "WKWWWKW",
    "WWWWWWW",
    "WPWWWPW",
    ".WWKWW.",
    ".WWWWW.",
    "WWWWWWW",
    "WW...WW",
]

HACHIWARE = [
    "B.....B",
    "BB...BB",
    ".BWWWB.",
    "WBWWWBW",
    "WKWWWKW",
    "WWWWWWW",
    ".WPKPW.",
    ".WWWWW.",
    "WWWWWWW",
    "WW...WW",
]

USAGI = [
    ".W...W.",
    ".W...W.",
    ".W...W.",
    ".WWWWW.",
    "WWWWWWW",
    "WKWWWKW",
    "WWWYWWW",
    ".WWWWW.",
    "WWWWWWW",
    "WW...WW",
]

# 店員（コック）: 白い帽子＋赤いエプロンのオリジナル立ちパネル
CLERK = [
    ".WWWWW.",
    "WWWWWWW",
    ".WWWWW.",
    "WKWWWKW",
    "WWWWWWW",
    ".WWWWW.",
    ".RRRRR.",
    "WRRRRRW",
    ".RRRRR.",
    "WW...WW",
]


# --- 画像取り込み（Pillow） ---
def _nearest_block(rgb):
    r, g, b = rgb[:3]
    best, bestd = None, 1e18
    for name, (cr, cg, cb) in CONCRETE_RGB.items():
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < bestd:
            best, bestd = name, d
    return best


def _image_to_rows(image_path, max_w, max_h):
    """画像をブロックのドット絵（ポスター）に変換する。16:9 のシーン画像でも
    キャラの色が淡い背景に埋もれないよう、セルごとに「一番鮮やかなピクセル」を採用する。
    淡い（彩度の低い）セルは平均色＝ほぼ白になり、白い壁になじむ＝背景が自然に消える。
    アスペクト比を保って max_w x max_h 以内に縮小する。返り値は top→bottom の行配列。
    各セルは block 名 or None（ほぼ透過のセルのみ None）。"""
    from PIL import Image

    img = Image.open(image_path).convert("RGBA")
    iw, ih = img.size
    scale = min(max_w / float(iw), max_h / float(ih))
    nw = max(1, min(max_w, int(round(iw * scale))))
    nh = max(1, min(max_h, int(round(ih * scale))))

    k = max(6, 132 // max(nw, nh))  # 作業解像度（小さすぎると平均化で色が飛ぶ）
    work = img.resize((nw * k, nh * k), Image.LANCZOS)
    wp = work.load()

    rows = []
    for cy in range(nh):
        line = []
        for cx in range(nw):
            best = None
            best_sat = -1
            ar = ag = ab = aa = n = 0
            for yy in range(cy * k, cy * k + k):
                for xx in range(cx * k, cx * k + k):
                    r, g, b, a = wp[xx, yy]
                    ar += r
                    ag += g
                    ab += b
                    aa += a
                    n += 1
                    if a < 128:
                        continue
                    s = max(r, g, b) - min(r, g, b)
                    if s > best_sat:
                        best_sat, best = s, (r, g, b)
            if aa // n < 128:
                line.append(None)  # ほぼ透過 → 壁(白)を残す
            elif best is None or best_sat < 18:
                line.append(_nearest_block((ar // n, ag // n, ab // n)))
            else:
                line.append(_nearest_block(best))  # 鮮やかな色（キャラ）を優先
        rows.append(line)
    return rows


def _draw_image_panel(w, rows, base_x, base_y, base_z, facing):
    h = len(rows)
    width = len(rows[0]) if rows else 0
    half = width // 2
    for r, line in enumerate(rows):
        y = base_y + (h - 1 - r)
        for cidx, block in enumerate(line):
            if not block:
                continue
            off = cidx - half
            if facing == "east":      # 西壁、+X を向く。横軸 = Z
                w.set_block(base_x, y, base_z + off, block)
            elif facing == "west":    # 東壁、-X を向く。横軸 = Z（左右反転）
                w.set_block(base_x, y, base_z - off, block)
            elif facing == "south":   # 横軸 = X
                w.set_block(base_x + off, y, base_z, block)
            elif facing == "north":   # 横軸 = X（左右反転）
                w.set_block(base_x - off, y, base_z, block)


def _authored_to_rows(art, legend=LEGEND):
    return [[legend.get(ch) for ch in line] for line in art]


def _fit_rows(rows, max_w, max_h):
    """rows を max_w x max_h 以内に間引く（はみ出し防止）。"""
    h = len(rows)
    width = len(rows[0]) if rows else 0
    if h <= max_h and width <= max_w:
        return rows
    nh = min(h, max_h)
    nw = min(width, max_w)
    out = []
    for ry in range(nh):
        line = rows[int(ry * h / nh)]
        out.append([line[int(rx * width / nw)] for rx in range(nw)])
    return out


# キャラの壁画の配置先（店内の左右の壁・客席エリア）
# (base_x, facing, center_z, max_w, max_h, fallback_art)
WALL_SLOTS = [
    (C.SHOP_X_MIN, "east", 6, 11, 6, CHIIKAWA),   # 左（西）の壁
    (C.SHOP_X_MAX, "west", 6, 11, 6, HACHIWARE),  # 右（東）の壁
]

_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def _list_images():
    if not os.path.isdir(ASSET_DIR):
        return []
    files = [
        f for f in os.listdir(ASSET_DIR)
        if os.path.splitext(f)[1].lower() in _IMAGE_EXTS
    ]
    files.sort()
    return [os.path.join(ASSET_DIR, f) for f in files]


def place_character_panels(w):
    """キャラを店内の左右の壁に貼る。assets の画像を使い、無ければオリジナルのドット絵。"""
    base_y = C.FEET_Y
    images = _list_images()
    used = []
    for i, (bx, facing, cz, mw, mh, fallback) in enumerate(WALL_SLOTS):
        rows = None
        if i < len(images):
            try:
                rows = _image_to_rows(images[i], mw, mh)
                used.append(os.path.basename(images[i]))
            except Exception as e:  # noqa: BLE001
                print(f"  [panels] {os.path.basename(images[i])}: 取り込み失敗→オリジナル使用 ({e})")
                rows = None
        if rows is None:
            rows = _fit_rows(_authored_to_rows(fallback), mw, mh)
        _draw_image_panel(w, rows, bx, base_y, cz, facing)
    if used:
        print(f"  [panels] 壁画に画像を使用: {', '.join(used)}")
    else:
        print("  [panels] すべてオリジナルのドット絵を使用")
