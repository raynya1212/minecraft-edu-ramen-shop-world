"""店舗の外観: 白いコンクリの建物・ガラスのストアフロント・黄色い「郎」看板・自動ドア枠・外の広場。"""
from __future__ import annotations

import os

from . import consts as C


def _render_kanji_rows(ch: str, cols: int, rows: int):
    """Windows の日本語フォントで漢字を cols×rows のドット絵（'#'/'.'）に起こす。
    フォントが見つからない／PIL が無い場合は None を返す。"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None
    fonts = [
        r"C:\Windows\Fonts\BIZ-UDGothicR.ttc",
        r"C:\Windows\Fonts\msgothic.ttc",
        r"C:\Windows\Fonts\meiryo.ttc",
        r"C:\Windows\Fonts\YuGothM.ttc",
    ]
    font = None
    for fp in fonts:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 220)
                break
            except Exception:
                continue
    if font is None:
        return None
    big = 300
    img = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(img)
    bbox = d.textbbox((0, 0), ch, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((big - tw) / 2 - bbox[0], (big - th) / 2 - bbox[1]), ch, fill=255, font=font)
    cb = img.getbbox()
    if cb:
        img = img.crop(cb)
    side = max(img.size)
    pad = max(1, int(side * 0.08))
    canvas = Image.new("L", (side + 2 * pad, side + 2 * pad), 0)
    canvas.paste(img, (pad + (side - img.size[0]) // 2, pad + (side - img.size[1]) // 2))
    small = canvas.resize((cols, rows), Image.LANCZOS)
    px = small.load()
    out = []
    for r in range(rows):
        out.append("".join("#" if px[c, r] >= 120 else "." for c in range(cols)))
    return out


# 黄色い看板に描く「郎」のドット絵（# = 黒, . = 透過＝黄色のまま）。
# Windows の日本語フォントから生成。無ければ簡易フォールバック。
_ROU_FALLBACK = [
    "..###....##",
    "..#.#..####",
    "..###..#..#",
    "..#.#..#..#",
    "#######.##.",
    "..#.#.#.#..",
    ".##.#.#.#.#",
    "..#.#.#.#.#",
    "..#.#.#.#.#",
    "..#.#...#.#",
    "..#.#...###",
]
ROU_GLYPH = _render_kanji_rows("郎", 13, 13) or _ROU_FALLBACK


def _lay_ground(w):
    """広場と店舗の地面を整える。周囲のフラット地表(草:GROUND_Y)と段差が出ないように、
    触れるチャンクの地中も埋めて境界のすき間（void）を防ぐ。"""
    x1, x2 = C.PLAZA_X_MIN, C.PLAZA_X_MAX
    z1, z2 = C.PLAZA_Z_MIN, C.PLAZA_Z_MAX
    # 地中の充填（bedrock / stone）。地下は見えないので stone で統一。
    w.fill(x1, C.WORLD_FLOOR, z1, x2, C.WORLD_FLOOR, z2, "bedrock")
    w.fill(x1, C.WORLD_FLOOR + 1, z1, x2, C.GROUND_Y - 1, z2, "stone")
    # 地表（広場は灰コンクリ）
    w.fill(x1, C.GROUND_Y, z1, x2, C.GROUND_Y, z2, C.BLK_PLAZA)


def _exterior_walls(w):
    """外周の壁・床・天井。"""
    xmin, xmax = C.SHOP_X_MIN, C.SHOP_X_MAX
    zmin, zmax = C.SHOP_Z_FRONT, C.SHOP_Z_BACK
    y0, y1 = C.FLOOR_Y, C.CEIL_Y

    # 店内の床
    w.fill(xmin + 1, C.FLOOR_Y, zmin + 1, xmax - 1, C.FLOOR_Y, zmax - 1, C.BLK_FLOOR)
    # 天井
    w.fill(xmin, y1, zmin, xmax, y1, zmax, C.BLK_CEIL)

    # 側壁（東西）と背面（北）は白いコンクリで囲う
    for y in range(y0 + 1, y1):
        # 西壁・東壁
        for z in range(zmin, zmax + 1):
            w.set_block(xmin, y, z, C.BLK_WALL)
            w.set_block(xmax, y, z, C.BLK_WALL)
        # 背面壁
        for x in range(xmin, xmax + 1):
            w.set_block(x, y, zmax, C.BLK_WALL)


def _storefront(w):
    """南面（手前）のガラス張りストアフロントと、感圧板で開く鉄の自動ドア。

    自動ドアは Behavior Pack に依存しないバニラ挙動（感圧板→隣接する鉄のドアが開く）。
    既定は閉。中央の柱はなくし、2枚の鉄ドアを隣り合わせ(x=-1,0)にくっつけた両開きドア。
    踏むと左右の扉が中央から外側へ開く。
    """
    z = C.SHOP_Z_FRONT
    y0 = C.FLOOR_Y
    fx0, fx1 = C.ENTRANCE_FRAME_X_MIN, C.ENTRANCE_FRAME_X_MAX

    # 角の柱（白）
    for y in range(y0 + 1, C.CEIL_Y + 1):
        for x in (C.SHOP_X_MIN, C.SHOP_X_MIN + 1, C.SHOP_X_MAX - 1, C.SHOP_X_MAX):
            w.set_block(x, y, z, C.BLK_WALL)

    # ガラスのストアフロント（中央のドア＋枠 x=fx0..fx1 は除く）
    for x in range(C.SHOP_X_MIN + 2, C.SHOP_X_MAX - 1):
        if fx0 <= x <= fx1:
            continue
        for y in range(y0 + 1, C.ENTRANCE_TOP_Y + 1):
            w.set_block(x, y, z, "light_blue_stained_glass")
        for y in range(C.ENTRANCE_TOP_Y + 1, C.CEIL_Y + 1):
            w.set_block(x, y, z, C.BLK_WALL)

    # 自動ドアの枠（左右の柱＋まぐさ）をコントラスト色で。ガラスや白壁と区別できる。
    for y in range(y0 + 1, C.ENTRANCE_TOP_Y + 2):
        w.set_block(fx0, y, z, C.BLK_FRAME)
        w.set_block(fx1, y, z, C.BLK_FRAME)
    for x in range(fx0, fx1 + 1):
        w.set_block(x, C.ENTRANCE_TOP_Y + 1, z, C.BLK_FRAME)  # まぐさ

    # 枠の上〜天井は白壁
    for x in range(fx0, fx1 + 1):
        for y in range(C.ENTRANCE_TOP_Y + 2, C.CEIL_Y + 1):
            w.set_block(x, y, z, C.BLK_WALL)

    # 左右に鉄の自動ドア（高さ2）。隣り合わせ(x=-1,0)に置き、中央でくっつく両開きドア。
    _iron_door(w, C.ENTRANCE_X_MIN, y0 + 1, z, hinge=0)   # 左（西）のドア
    _iron_door(w, C.ENTRANCE_X_MAX, y0 + 1, z, hinge=1)   # 右（東）のドア

    # ドアの上（欄間）にすりガラス
    for x in (C.ENTRANCE_X_MIN, C.ENTRANCE_X_MAX):
        w.set_block(x, C.ENTRANCE_TOP_Y, z, "light_blue_stained_glass")

    # 感圧板（外側 z-1・内側 z+1）。踏むと隣の鉄のドアが開く＝バニラの自動ドア。
    for x in (C.ENTRANCE_X_MIN, C.ENTRANCE_X_MAX):
        w.set_block(x, C.FEET_Y, z - 1, C.BLK_PLATE)
        w.set_block(x, C.FEET_Y, z + 1, C.BLK_PLATE)


def _iron_door(w, x, y_bottom, z, hinge):
    """鉄のドアを1枚（下半分＋上半分）設置する。client/南向き・既定は閉。"""
    # direction=1 で客側（-Z＝南）を向く。hinge で左右の開く向きを変える。
    w.set_block(
        x, y_bottom, z, "iron_door",
        {"direction": 1, "door_hinge_bit": hinge,
         "open_bit": False, "upper_block_bit": False},
    )
    w.set_block(
        x, y_bottom + 1, z, "iron_door",
        {"direction": 1, "door_hinge_bit": hinge,
         "open_bit": False, "upper_block_bit": True},
    )


def _rou_sign(w):
    """入口の上に黄色い「郎」看板（サインボード）を立てる。"""
    z = C.SHOP_Z_FRONT - 1  # ファサードより1ブロック手前に張り出す
    rows = ROU_GLYPH
    h = len(rows)
    width = len(rows[0])
    x_left = -(width // 2)
    y_top = C.CEIL_Y + h  # 屋根の上に持ち上げる

    # 黄色い下地（少し余白をとる）
    w.fill(
        x_left - 1,
        y_top - h - 0,
        z,
        x_left + width,
        y_top + 1,
        z,
        C.BLK_SIGN_BG,
    )
    # 文字（黒）
    # 看板は南面(z=-1)。プレイヤーはスポーン(z=-5)から南(+Z)を向いて見るため、
    # 見る人の左＝+X(東)・右＝-X(西)。文字の左端(cidx=0)を最大xに置くよう列を反転する
    # （そのまま x_left+cidx にすると左右反転して見える）。
    for r, line in enumerate(rows):
        y = y_top - r
        for cidx, ch in enumerate(line):
            if ch == "#":
                w.set_block(x_left + (width - 1 - cidx), y, z, C.BLK_SIGN_FG)
    # 看板を支える袖（左右の白い柱）
    for y in range(C.CEIL_Y + 1, y_top + 2):
        w.set_block(x_left - 2, y, z, C.BLK_WALL)
        w.set_block(x_left + width + 1, y, z, C.BLK_WALL)

    # 入口前の広場に立て看板（読みやすさ用）。店名は「郎」。
    w.set_block(3, C.FEET_Y, C.SHOP_Z_FRONT - 3, "oak_fence")
    w.set_sign(
        3,
        C.FEET_Y + 1,
        C.SHOP_Z_FRONT - 3,
        "standing_sign",
        "郎",
        props={"ground_sign_direction": 8},
    )


def _roof_trim(w):
    """屋根のフチをひと回り。白い建物の輪郭を締める。"""
    xmin, xmax = C.SHOP_X_MIN, C.SHOP_X_MAX
    zmin, zmax = C.SHOP_Z_FRONT, C.SHOP_Z_BACK
    y = C.CEIL_Y + 1
    for x in range(xmin, xmax + 1):
        w.set_block(x, y, zmin, C.BLK_WALL)
        w.set_block(x, y, zmax, C.BLK_WALL)
    for z in range(zmin, zmax + 1):
        w.set_block(xmin, y, z, C.BLK_WALL)
        w.set_block(xmax, y, z, C.BLK_WALL)


def _door_plates(w):
    """入口の足元に感圧板（自動ドアのセンサー）を敷く。外側と内側に並べる。"""
    z_out = C.SHOP_Z_FRONT - 1   # 外側（手前）
    z_in = C.SHOP_Z_FRONT + 1    # 内側
    for x in range(C.ENTRANCE_X_MIN, C.ENTRANCE_X_MAX + 1):
        w.set_block(x, C.FEET_Y, z_out, C.BLK_PLATE)
        w.set_block(x, C.FEET_Y, z_in, C.BLK_PLATE)


def build_exterior(w):
    _lay_ground(w)
    _exterior_walls(w)
    _storefront(w)
    _door_plates(w)
    _roof_trim(w)
    _rou_sign(w)
