"""店内: 赤いカウンター・背もたれのないスツール・厨房・食券販売機・照明・コール案内。"""
from __future__ import annotations

from . import consts as C


def _lighting(w):
    """天井にシーランタンを埋め込み、店内を明るく保つ。"""
    y = C.CEIL_Y
    for x in range(C.SHOP_X_MIN + 2, C.SHOP_X_MAX - 1, 4):
        for z in range(C.SHOP_Z_FRONT + 3, C.SHOP_Z_BACK, 4):
            w.set_block(x, y, z, C.BLK_LIGHT)


def _counter(w):
    """赤いカウンター（2段積み）。手前(南)が客席側、奥(北)が厨房側。"""
    for x in range(C.COUNTER_X_MIN, C.COUNTER_X_MAX + 1):
        w.set_block(x, C.FLOOR_Y + 1, C.COUNTER_Z, C.BLK_COUNTER)
        w.set_block(x, C.COUNTER_TOP_Y, C.COUNTER_Z, C.BLK_COUNTER)
    # 天板のフチ（白）でカウンターを引き締める
    for x in range(C.COUNTER_X_MIN, C.COUNTER_X_MAX + 1):
        w.set_block(x, C.COUNTER_TOP_Y, C.COUNTER_Z - 1, "quartz_slab")

    # 卓上の雰囲気: 箸立て・こしょう・水ピッチャーを小さなブロックで表現
    for x in (-5, 0, 5):
        w.set_block(x, C.COUNTER_TOP_Y + 1, C.COUNTER_Z - 1, "flower_pot")
    for x in (-3, 3):
        w.set_block(x, C.COUNTER_TOP_Y + 1, C.COUNTER_Z - 1, "light_blue_stained_glass")


def _stools(w):
    """背もたれのないスツール（脚＋赤い座面）。装飾。"""
    for x in C.SEAT_XS:
        # 脚（細いフェンス）
        w.set_block(x, C.FLOOR_Y + 1, C.SEAT_Z, "dark_oak_fence")
        # 座面（赤いカーペット）
        w.set_block(x, C.FLOOR_Y + 2, C.SEAT_Z, "red_carpet")


def _kitchen(w):
    """厨房エリア（カウンターの奥）。二郎系の寸胴・コンロを雰囲気で再現。"""
    z0, z1 = C.KITCHEN_Z_MIN, C.KITCHEN_Z_MAX
    # 厨房の床はステンレス風（鉄ブロック帯）
    for x in range(C.SHOP_X_MIN + 1, C.SHOP_X_MAX):
        w.set_block(x, C.FLOOR_Y, z1, "iron_block")

    # コンロ列（かまど/溶鉱炉/燻製器）を背面壁ぎわに
    cook_y = C.FLOOR_Y + 1
    cook_z = z1 - 1
    appliances = ["furnace", "blast_furnace", "smoker", "furnace", "blast_furnace"]
    xs = [-6, -3, 0, 3, 6]
    for x, ap in zip(xs, appliances):
        w.set_block(x, cook_y, cook_z, ap, {"minecraft:cardinal_direction": "south"})

    # 寸胴（スープ寸胴＝大釜）を手前ぎみに3つ
    for x in (-4, 0, 4):
        w.set_block(x, cook_y, z0 + 1, "cauldron",
                    {"cauldron_liquid": "water", "fill_level": 6})

    # 麺・丼の収納（樽）
    for x in (-7, 7):
        w.set_block(x, cook_y, z0, "barrel", {"facing_direction": 1})
        w.set_block(x, cook_y + 1, z0, "barrel", {"facing_direction": 1})

    # のれん風の赤い帯（厨房と客席の境界、カウンター上）
    for x in range(C.COUNTER_X_MIN, C.COUNTER_X_MAX + 1):
        w.set_block(x, C.CEIL_Y - 1, C.COUNTER_Z, "red_wool")

    # 背面の黄色いメニュー札。二郎系の店内によくある、黄色地＋黒文字の雰囲気。
    for x in range(-6, 7):
        w.set_block(x, C.CEIL_Y - 2, z1, "yellow_concrete")
    w.set_sign(0, C.CEIL_Y - 2, z1 - 1, "wall_sign",
               "ラーメン\n小 / 大\n食券を先に", props={"facing_direction": 3})
    w.set_sign(-4, C.CEIL_Y - 2, z1 - 1, "wall_sign",
               "無料トッピング\nニンニク\nヤサイ", props={"facing_direction": 3})
    w.set_sign(4, C.CEIL_Y - 2, z1 - 1, "wall_sign",
               "アブラ\nカラメ\nマシマシ", props={"facing_direction": 3})


def _jiro_wall_decor(w):
    """二郎系ラーメン店らしい注意書き・コール表・行列導線。"""
    # 左右壁の黄色い掲示帯。中央(z=5..7)は Image Map の額縁エリアなので看板を置かない。
    for z in range(2, 14):
        w.set_block(C.SHOP_X_MIN, C.FLOOR_Y + 3, z, "yellow_concrete")
        w.set_block(C.SHOP_X_MAX, C.FLOOR_Y + 3, z, "yellow_concrete")
    # 西壁（左）: 食券と着席ルール
    w.set_sign(C.SHOP_X_MIN + 1, C.FLOOR_Y + 3, 2, "wall_sign",
               "食券は\nカウンターへ\n先にどうぞ", props={"facing_direction": 5})
    w.set_sign(C.SHOP_X_MIN + 1, C.FLOOR_Y + 3, 9, "wall_sign",
               "残さず\n食べ切れる\n量でコール", props={"facing_direction": 5})
    w.set_sign(C.SHOP_X_MIN + 1, C.FLOOR_Y + 3, 13, "wall_sign",
               "水セルフ\nレンゲあり\n席をつめて", props={"facing_direction": 5})
    # 東壁（右）: コール表
    w.set_sign(C.SHOP_X_MAX - 1, C.FLOOR_Y + 3, 2, "wall_sign",
               "コール例\nそのまま\n全マシマシ", props={"facing_direction": 4})
    w.set_sign(C.SHOP_X_MAX - 1, C.FLOOR_Y + 3, 9, "wall_sign",
               "ニンニク\nヤサイ\nアブラ", props={"facing_direction": 4})
    w.set_sign(C.SHOP_X_MAX - 1, C.FLOOR_Y + 3, 13, "wall_sign",
               "カラメ\nマシ\nマシマシ", props={"facing_direction": 4})

    # 歴史学習は歴史案内NPCのダイアログに集約。壁の年表看板や本置きは置かない。

    # 食券機前から客席へ向かう行列マーカー（黄色/黒）。
    for i, z in enumerate(range(2, 8)):
        block = "yellow_concrete" if i % 2 == 0 else "black_concrete"
        w.set_block(3, C.FLOOR_Y, z, block)
    w.set_sign(2, C.FLOOR_Y + 1, 1, "standing_sign",
               "ここから\nならんで\nください", props={"ground_sign_direction": 8})

    # セルフ水コーナー（左奥手前）
    w.set_block(C.SHOP_X_MIN + 2, C.FLOOR_Y + 1, 12, "barrel", {"facing_direction": 1})
    w.set_block(C.SHOP_X_MIN + 2, C.FLOOR_Y + 2, 12, "cauldron", {"cauldron_liquid": "water", "fill_level": 6})
    w.set_command_block(
        C.SHOP_X_MIN + 3, C.FLOOR_Y + 1, 12,
        f"/function {C.BP_NAMESPACE}/water",
        props={"facing_direction": 1, "conditional_bit": False},
    )
    w.set_block(C.SHOP_X_MIN + 3, C.FLOOR_Y + 1, 11, "stone_button",
                {"facing_direction": 2, "button_pressed_bit": False})
    w.set_sign(C.SHOP_X_MIN + 2, C.FLOOR_Y + 3, 12, "standing_sign",
               "水\nセルフ\nボタンで", props={"ground_sign_direction": 8})


def _ticket_machine(w):
    """食券販売機（入口を入ってすぐ右手）。縦型の本体に、
    上からミニ/小/大の順でボタンを積む。各ボタンは1段ずつ間隔を空け、
    コマンドブロックを奥に隠して隣の注文が同時に走らないようにする。"""
    cx, z = C.TICKET_X, C.TICKET_Z          # 本体中央列 x=6、奥行き z=3
    front = z - 1                            # 客が立つ側（南）の面 z=2
    xs = (cx - 1, cx, cx + 1)               # 3列ぶんの幅（x=5,6,7）
    y_base = C.FLOOR_Y + 1                   # -59 足元
    y_large = C.FLOOR_Y + 2                  # -58 下段: 大
    y_small = C.FLOOR_Y + 4                  # -56 中段: 小（1段あける）
    y_mini = C.FLOOR_Y + 6                   # -54 上段: ミニ（1段あける）
    y_top = y_mini

    # 本体（鉄）の箱を組む。各ボタン段は1段ずつ空け、上下の信号干渉を避ける。
    for x in xs:
        for y in range(y_base, y_top + 1):
            block = C.BLK_TICKET_SCREEN if y in (y_large, y_small, y_mini) and x != cx - 1 else C.BLK_TICKET
            w.set_block(x, y, z, block)

    # メニュー別ボタン。上=ミニ、中=小、下=大。各段の間を空けて信号の干渉を避ける。
    menu_buttons = [
        (y_mini, "order_mini", "ミニ ¥1540\nちいかわ\n上のボタン"),
        (y_small, "order_small", "小 ¥1760\nハチワレ\n中のボタン"),
        (y_large, "order_large", "大 ¥1980\nうさぎ\n下のボタン"),
    ]
    for y, fn, label in menu_buttons:
        w.set_command_block(
            cx - 1, y, z,
            f"/execute as @p[r=6] run function {C.BP_NAMESPACE}/{fn}",
            props={"facing_direction": 1, "conditional_bit": False},
        )
        w.set_block(
            cx - 1, y, front, "stone_button",
            {"facing_direction": 2, "button_pressed_bit": False},
        )
        w.set_sign(cx, y, front, "wall_sign", label, props={"facing_direction": 2})
    # 取り出し口（中央下・客側）＝食券が出てくるスロット
    w.set_block(cx + 1, y_base, front, "iron_trapdoor",
                {"facing_direction": 2, "open_bit": False, "upside_down_bit": True})
    # 機体上部の看板（券売機の表示灯）
    w.set_sign(cx + 1, y_base, front, "wall_sign", "券売機\n上ミニ\n中小 下大", props={"facing_direction": 2})


def _oolong_vending_machine(w):
    """店外の黒烏龍茶自販機。"""
    x, z = 9, -5
    y_base = C.FLOOR_Y + 1
    front = z - 1
    for dx in (0, 1):
        w.set_block(x + dx, y_base, z, "black_concrete")
        w.set_block(x + dx, y_base + 1, z, "black_concrete")
        w.set_block(x + dx, y_base + 2, z, "cyan_concrete")
        w.set_block(x + dx, y_base + 3, z, "black_concrete")
        w.set_block(x + dx, y_base + 4, z, "gray_concrete")
    # 前面の光る商品窓・取り出し口・価格表示。黒い筐体に青い飲料列を見せる。
    w.set_block(x, y_base + 3, front, "light_blue_stained_glass")
    w.set_block(x + 1, y_base + 3, front, "light_blue_stained_glass")
    w.set_block(x, y_base + 2, front, "cyan_stained_glass")
    w.set_block(x + 1, y_base + 2, front, "cyan_stained_glass")
    w.set_block(x + 1, y_base + 1, front, "iron_trapdoor",
                {"facing_direction": 2, "open_bit": False, "upside_down_bit": True})
    w.set_block(x, y_base, front, "stone_slab")
    w.set_command_block(
        x, y_base + 1, z,
        f"/function {C.BP_NAMESPACE}/oolong",
        props={"facing_direction": 1, "conditional_bit": False},
    )
    w.set_block(x, y_base + 1, front, "stone_button", {"facing_direction": 2, "button_pressed_bit": False})
    w.set_sign(x, y_base + 4, front, "wall_sign", "黒烏龍茶\n¥500\nCOLD", props={"facing_direction": 2})
    w.set_sign(x + 1, y_base, front, "wall_sign", "取出口", props={"facing_direction": 2})


def _system_clock(w):
    """床下の常時実行コマンドブロック。tick.json が不安定な環境でのタイマー保険。"""
    w.set_command_block(
        C.SYSTEM_CLOCK_X, C.SYSTEM_CLOCK_Y, C.SYSTEM_CLOCK_Z,
        f"/function {C.BP_NAMESPACE}/main",
        props={"facing_direction": 1, "conditional_bit": False},
        name_tag="jiro_clock",
        auto=True,
        block_name="repeating_command_block",
    )


def _call_sign(w):
    """コールは店員NPCをタップして、という案内サイン（のれんに掛ける）。"""
    w.set_sign(
        0, C.CEIL_Y - 1, C.COUNTER_Z - 1, "wall_sign",
        "店員をタップ\nニンニク入れますか？\n正しくコール",
        props={"facing_direction": 2},
    )


def build_interior(w):
    _lighting(w)
    _counter(w)
    _stools(w)
    _kitchen(w)
    _jiro_wall_decor(w)
    _ticket_machine(w)
    _oolong_vending_machine(w)
    _system_clock(w)
    _call_sign(w)
