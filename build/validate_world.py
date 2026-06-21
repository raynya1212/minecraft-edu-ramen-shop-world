"""
生成結果の検証。

build/_work のワールドを開き、主要なブロック・Block Entity・Behavior Pack・
level.dat 設定が意図どおりかを点検してレポートする。

  py -3.12 build/validate_world.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import amulet  # noqa: E402
from amulet.level.formats.leveldb_world.format import BedrockLevelDAT  # noqa: E402

from lib import consts as C  # noqa: E402
from lib.behavior_pack import BP_HEADER_UUID, PACK_VERSION  # noqa: E402

WORK_DIR = C.WORK_DIR

PASS, FAIL = "  OK ", "  NG "
_errors = []


def check(cond, label):
    print((PASS if cond else FAIL) + label)
    if not cond:
        _errors.append(label)
    return cond


def block_at(level, x, y, z):
    b, _be = level.get_version_block(x, y, z, C.DIM, C.VERSION)
    return getattr(b, "base_name", str(b))


def block_ns_at(level, x, y, z):
    """(namespace, base_name) を返す。カスタムブロック判定用。"""
    b, _be = level.get_version_block(x, y, z, C.DIM, C.VERSION)
    return getattr(b, "namespace", ""), getattr(b, "base_name", str(b))


def be_at(level, x, y, z):
    _b, be = level.get_version_block(x, y, z, C.DIM, C.VERSION)
    return be


def sign_text_at(level, x, y, z):
    be = be_at(level, x, y, z)
    if be is None:
        return ""
    front = be.nbt.get("FrontText", {})
    return str(front.get("Text", ""))


def main():
    print("== 検証: ちいかわ 郎 ラーメンワールド ==")
    level = amulet.load_level(WORK_DIR)

    # --- 地形・建物 ---
    print("[地形・建物]")
    check(block_at(level, 0, C.GROUND_Y, 5) == C.BLK_FLOOR, "店内の床が light_gray_concrete")
    check(block_at(level, C.SHOP_X_MIN, C.FLOOR_Y + 2, 14) == C.BLK_WALL, "西壁が white_concrete")
    check(block_at(level, C.SHOP_X_MAX, C.FLOOR_Y + 2, 14) == C.BLK_WALL, "東壁が white_concrete")
    check(block_at(level, 0, C.CEIL_Y, 8) == C.BLK_CEIL, "天井が white_concrete")
    check(block_at(level, 0, C.FEET_Y, C.SPAWN_Z) == "air", "スポーン位置が空気（立てる）")
    check(block_at(level, 0, C.GROUND_Y, C.SPAWN_Z) == C.BLK_PLAZA, "広場が gray_concrete")

    # --- 入口・自動ドア（バニラの鉄ドア＋感圧板。BP 非依存）---
    print("[入口・自動ドア]")
    door_lo = all(
        block_at(level, x, C.FLOOR_Y + 1, C.SHOP_Z_FRONT) == "iron_door"
        for x in (C.ENTRANCE_X_MIN, C.ENTRANCE_X_MAX)
    )
    door_hi = all(
        block_at(level, x, C.FLOOR_Y + 2, C.SHOP_Z_FRONT) == "iron_door"
        for x in (C.ENTRANCE_X_MIN, C.ENTRANCE_X_MAX)
    )
    check(door_lo and door_hi, "左右に鉄の自動ドア（高さ2）がある")
    check(block_at(level, C.ENTRANCE_FRAME_X_MIN, C.FEET_Y, C.SHOP_Z_FRONT) == C.BLK_FRAME, "ドア枠（左）が gray_concrete")
    check(block_at(level, C.ENTRANCE_FRAME_X_MAX, C.FEET_Y, C.SHOP_Z_FRONT) == C.BLK_FRAME, "ドア枠（右）が gray_concrete")
    check(block_at(level, 0, C.FEET_Y, C.SHOP_Z_FRONT) != C.BLK_FRAME, "中央の柱を撤去し2枚扉を連結（x=0 が扉）")
    plates_out = sum(
        block_at(level, x, C.FEET_Y, C.SHOP_Z_FRONT - 1) == C.BLK_PLATE
        for x in (C.ENTRANCE_X_MIN, C.ENTRANCE_X_MAX)
    )
    plates_in = sum(
        block_at(level, x, C.FEET_Y, C.SHOP_Z_FRONT + 1) == C.BLK_PLATE
        for x in (C.ENTRANCE_X_MIN, C.ENTRANCE_X_MAX)
    )
    check(plates_out == 2, f"外側の感圧板 {plates_out}/2（踏むとドアが開く）")
    check(plates_in == 2, f"内側の感圧板 {plates_in}/2")

    # --- 看板（郎）---
    print("[黄色い『郎』看板]")
    sign_found = any(
        block_at(level, x, y, C.SHOP_Z_FRONT - 1) == C.BLK_SIGN_BG
        for x in range(-7, 8)
        for y in range(C.CEIL_Y, C.CEIL_Y + 15)
    )
    check(sign_found, "黄色い看板の下地がある")
    glyph_found = sum(
        block_at(level, x, y, C.SHOP_Z_FRONT - 1) == C.BLK_SIGN_FG
        for x in range(-7, 8)
        for y in range(C.CEIL_Y, C.CEIL_Y + 15)
    )
    check(glyph_found >= 20, f"看板の文字『郎』（黒）がある（{glyph_found} ブロック）")

    # --- カウンター・内装 ---
    print("[内装]")
    check(block_at(level, 5, C.COUNTER_TOP_Y, C.COUNTER_Z) == C.BLK_COUNTER, "赤いカウンター天板")
    # 縦型の食券販売機（本体3列・3メニューボタン）
    check(block_at(level, C.TICKET_X, C.FLOOR_Y + 1, C.TICKET_Z) == C.BLK_TICKET, "食券販売機の本体（鉄）")
    check(block_at(level, C.TICKET_X, C.FLOOR_Y + 6, C.TICKET_Z) == C.BLK_TICKET_SCREEN, "食券販売機のメニュー画面（水色）")
    ticket_cmds = []
    ticket_rows = (
        (C.FLOOR_Y + 6, "order_mini", "ミニ"),
        (C.FLOOR_Y + 4, "order_small", "小"),
        (C.FLOOR_Y + 2, "order_large", "大"),
    )
    for y, expected, label in ticket_rows:
        check(block_at(level, C.TICKET_X - 1, y, C.TICKET_Z) == "command_block", f"食券販売機の{expected}コマンド")
        check(block_at(level, C.TICKET_X - 1, y, C.TICKET_Z - 1) == "stone_button", f"食券販売機の{expected}ボタン")
        check(label in sign_text_at(level, C.TICKET_X, y, C.TICKET_Z - 1), f"食券販売機の{expected}ラベル")
        be = be_at(level, C.TICKET_X - 1, y, C.TICKET_Z)
        ticket_cmds.append(str(be.nbt.get("Command", "")) if be is not None else "")
    isolated_rows = all(
        block_at(level, C.TICKET_X - 1, y, C.TICKET_Z) != "command_block"
        for y in (C.FLOOR_Y + 3, C.FLOOR_Y + 5)
    )
    check(isolated_rows, "券売機の注文コマンド段が隣接していない")
    check(all(fn in cmd for fn, cmd in zip(("order_mini", "order_small", "order_large"), ticket_cmds)), "券売機がミニ/小/大を選べる")
    check(all("execute as @p" in cmd for cmd in ticket_cmds), "券売機ボタンが押したプレイヤーとして注文関数を実行")
    check(block_at(level, 0, C.CEIL_Y - 1, C.COUNTER_Z - 1) == "wall_sign", "コール案内の看板（店員をタップ）")
    check(block_at(level, C.SYSTEM_CLOCK_X, C.SYSTEM_CLOCK_Y, C.SYSTEM_CLOCK_Z) == "repeating_command_block", "床下のリピートコマンド時計")
    clock_be = be_at(level, C.SYSTEM_CLOCK_X, C.SYSTEM_CLOCK_Y, C.SYSTEM_CLOCK_Z)
    clock_cmd = str(clock_be.nbt.get("Command", "")) if clock_be is not None else ""
    check("function jiro/main" in clock_cmd, "リピート時計が function jiro/main を実行")
    # 店外の黒烏龍茶自販機
    check(block_at(level, 9, C.FLOOR_Y + 2, -5) == "command_block", "店外の黒烏龍茶自販機コマンド")
    check(block_at(level, 9, C.FLOOR_Y + 2, -6) == "stone_button", "店外の黒烏龍茶自販機ボタン")
    check(block_at(level, 9, C.FLOOR_Y + 4, -6) == "light_blue_stained_glass", "黒烏龍茶自販機の商品窓")
    check(block_at(level, 10, C.FLOOR_Y + 2, -6) == "iron_trapdoor", "黒烏龍茶自販機の取出口")

    # コールは店員NPCをタップ。物理端末（カウンター前のコマンドブロック＋ボタン）は
    # 廃止したので、跡地にコマンドブロック／石ボタンが残っていないことを確認する。
    console_xs = (-4, -3, -2, -1, 1, 2, 3, 4)
    no_cb = all(
        block_at(level, x, C.COUNTER_TOP_Y, C.COUNTER_Z) != "command_block"
        for x in console_xs
    )
    no_btn = all(
        block_at(level, x, C.COUNTER_TOP_Y, C.COUNTER_Z - 1) != "stone_button"
        for x in console_xs
    )
    check(no_cb and no_btn, "旧コール端末（物理ボタン）が撤去されている")

    # --- 二郎風の内装（黄色い掲示・コール表・行列導線・セルフ水）---
    print("[二郎風の内装]")
    check(block_at(level, C.SHOP_X_MIN + 1, C.FLOOR_Y + 3, 2) == "wall_sign", "西壁に食券/着席ルールの掲示")
    check(block_at(level, C.SHOP_X_MAX - 1, C.FLOOR_Y + 3, 9) == "wall_sign", "東壁にコール表の掲示")
    no_floating_signs = all(
        block_at(level, x, C.FLOOR_Y + 3, z) != "wall_sign"
        for x, zs in ((C.SHOP_X_MIN + 1, (5, 6)), (C.SHOP_X_MAX - 1, (6, 7)))
        for z in zs
    )
    check(no_floating_signs, "Image Map額縁エリア付近に浮いた看板が無い")
    queue_n = sum(block_at(level, 3, C.FLOOR_Y, z) in ("yellow_concrete", "black_concrete") for z in range(2, 8))
    check(queue_n == 6, f"食券機前の行列マーカー（{queue_n}/6）")
    check(block_at(level, 2, C.FLOOR_Y + 1, 1) == "standing_sign", "行列案内看板を券売機前から少し離して配置")
    check(block_at(level, C.SHOP_X_MIN + 2, C.FLOOR_Y + 2, 12) == "cauldron", "セルフ水コーナーの大釜")
    check(block_at(level, C.SHOP_X_MIN + 3, C.FLOOR_Y + 1, 12) == "command_block", "セルフ水コーナーの給水コマンド")
    check(block_at(level, C.SHOP_X_MIN + 3, C.FLOOR_Y + 1, 11) == "stone_button", "セルフ水コーナーの給水ボタン")
    check(block_at(level, 0, C.CEIL_Y - 2, C.KITCHEN_Z_MAX - 1) == "wall_sign", "背面の黄色いメニュー札")
    history_signs_removed = all(
        block_at(level, C.SHOP_X_MIN + 1, C.FLOOR_Y + 4, z) != "wall_sign"
        for z in (3, 4, 8, 12)
    )
    check(history_signs_removed, "壁の歴史年表看板を撤去")
    check(block_at(level, C.SHOP_X_MIN + 2, C.FLOOR_Y + 1, 4) != "lectern", "歴史ブック台を撤去しNPCに集約")
    left_frames = sum(block_at(level, C.SHOP_X_MIN, y, z) == "frame" for y in (C.FEET_Y + 3, C.FEET_Y + 2) for z in (5, 6))
    right_frames = sum(block_at(level, C.SHOP_X_MAX, y, z) == "frame" for y in (C.FEET_Y + 3, C.FEET_Y + 2) for z in (5, 6))
    kitchen_frames = sum(block_at(level, x, y, C.SHOP_Z_BACK) == "frame" for y in (C.FEET_Y + 3, C.FEET_Y + 2) for x in (-1, 0))
    outdoor_frames = sum(block_at(level, x, y, C.SHOP_Z_FRONT - 4) == "frame" for y in (C.FEET_Y + 3, C.FEET_Y + 2) for x in (-7, -6))
    check(left_frames == 4, f"左壁のImage Map額縁（{left_frames}/4）")
    check(right_frames == 4, f"右壁のImage Map額縁（{right_frames}/4）")
    check(kitchen_frames == 4, f"キッチン壁のImage Map額縁（{kitchen_frames}/4）")
    check(outdoor_frames == 4, f"店外パネルのImage Map額縁（{outdoor_frames}/4）")

    level.close()

    # --- Behavior Pack ---
    print("[Behavior Pack]")
    bp_root = os.path.join(WORK_DIR, "behavior_packs", C.BP_NAME)
    check(os.path.isfile(os.path.join(bp_root, "manifest.json")), "manifest.json")
    check(os.path.isfile(os.path.join(bp_root, "functions", "tick.json")), "tick.json")
    tick_data = json.load(open(os.path.join(bp_root, "functions", "tick.json"), encoding="utf-8"))
    check(tick_data.get("values") == [f"{C.BP_NAMESPACE}/noop"], "tick.json は noop（時計はリピートコマンドブロック）")
    # min_engine_version は古いエンジンでも読めるよう [1,20,0]
    mani = json.load(open(os.path.join(bp_root, "manifest.json"), encoding="utf-8"))
    mev = mani.get("header", {}).get("min_engine_version")
    check(mev == [1, 20, 0], f"min_engine_version={mev}（古い版でも読める）")
    fdir = os.path.join(bp_root, "functions", C.BP_NAMESPACE)
    base_fns = ("main", "noop", "boot", "loop", "ask", "serve", "fail", "order", "order_player",
                "order_mini", "order_small", "order_large", "water", "oolong",
                "spawn_npcs", "reset_player")
    for fn in base_fns:
        check(os.path.isfile(os.path.join(fdir, fn + ".mcfunction")), f"function {fn}")
    # コール選択肢ごとの call1..callN
    for i in range(1, len(C.CALL_PRESETS) + 1):
        check(os.path.isfile(os.path.join(fdir, f"call{i}.mcfunction")), f"function call{i}")
    # カスタムブロック／RP は廃止（MEE が拒否してBP全体が無効化される原因だった）
    check(not os.path.isdir(os.path.join(bp_root, "blocks")),
          "カスタムブロック定義が無い（MEE 非対応の実験機能を使わない）")

    # 店内NPCのダイアログ（dialogue/jiro_call.json）。コール＋雰囲気NPCのセリフ。
    dlg_path = os.path.join(bp_root, "dialogue", f"{C.CALL_SCENE}.json")
    if check(os.path.isfile(dlg_path), "dialogue/jiro_call.json がある"):
        dlg = json.load(open(dlg_path, encoding="utf-8"))
        scenes = dlg.get("minecraft:npc_dialogue", {}).get("scenes", [])
        by_tag = {s.get("scene_tag"): s for s in scenes}
        call_scene = by_tag.get(C.CALL_SCENE, {})
        btns = call_scene.get("buttons", [])
        check(len(btns) == len(C.CALL_PRESETS),
              f"ダイアログのコール選択肢（{len(btns)}/{len(C.CALL_PRESETS)}）")
        check(any("jiro_call" in c for b in btns for c in b.get("commands", [])),
              "ボタンが @initiator の jiro_call を立てる")
        check(all(any(f"function jiro/call{i}" in c for c in b.get("commands", []))
              for i, b in enumerate(btns, start=1)),
              "ボタンが直接 call1..call6 を実行する（tick 非依存）")
        check("ニンニク入れますか" in call_scene.get("text", ""), "店員の問いかけが『ニンニク入れますか？』")
        check(any(b.get("name") == "はい" for b in btns), "NG選択肢『はい』がある")
        # 雰囲気NPC（店主・助手・常連客…）のセリフ用シーン。歴史案内だけはページ式学習ボタン付き。
        for tag, name, _text, _x, _y, _z, _yaw in C.FLAVOR_NPCS:
            sc = by_tag.get(tag, {})
            if tag == "jiro_history":
                history_buttons = sc.get("buttons", [])
                expected_buttons = len(C.HISTORY_LESSONS) + 1
                check(len(history_buttons) == expected_buttons,
                    f"歴史案内NPCの学習ボタン（{len(history_buttons)}/{expected_buttons}）")
                check(any("jiro_history_timeline_1" in c for b in history_buttons for c in b.get("commands", [])),
                    "歴史案内NPCから年表ページを開ける")
                check(any(C.HISTORY_QUIZ[0][0] in c for b in history_buttons for c in b.get("commands", [])),
                    "歴史案内NPCからミニクイズを始められる")
            else:
                check(sc.get("buttons") == [] and bool(sc.get("text")),
                      f"NPCセリフ『{name}』のシーン（ボタン無し＝取引なし）")
        for key, _label, _title, pages in C.HISTORY_LESSONS:
            for page_index in range(1, len(pages) + 1):
                scene_tag = f"jiro_history_{key}_{page_index}"
                sc = by_tag.get(scene_tag, {})
                check(bool(sc.get("text")) and any("目次へ" == b.get("name") for b in sc.get("buttons", [])),
                    f"歴史ページ {scene_tag}")
        first_quiz = by_tag.get(f"jiro_history_{C.HISTORY_QUIZ[0][0]}", {})
        check(len(first_quiz.get("buttons", [])) >= 4, "ミニクイズは問題と選択肢を分けて表示")
        check(any(f"jiro_history_{C.HISTORY_QUIZ[0][0]}_ok" in c for b in first_quiz.get("buttons", []) for c in b.get("commands", [])),
              "ミニクイズの正解ボタンが解答ページを開く")

    # serve がラーメンを出し、すぐ退店可にする
    serve_txt = ""
    serve_path = os.path.join(fdir, "serve.mcfunction")
    if os.path.isfile(serve_path):
        serve_txt = open(serve_path, encoding="utf-8").read()
    check("jiro_state 5" in serve_txt and "beetroot_soup" in serve_txt,
          "serve がラーメンを出して提供済み(state=5)にする")
    check("jiro_menu" in serve_txt and "ラーメン豚" in serve_txt, "serve が選択メニューと価格を表示する")
    check("追加トッピングなし" in serve_txt and "具なし" not in serve_txt, "そのままは追加トッピングなしとして表示")
    check("hunger" not in serve_txt, "空腹効果を使わない（満腹/ダメージ問題を回避）")
    check(not os.path.isfile(os.path.join(fdir, "eating_tick.mcfunction")),
          "実食演出(eating_tick)は廃止")
    check(not os.path.isfile(os.path.join(fdir, "done.mcfunction")),
          "完食演出(done)は廃止")
    # ask はコール開始＋制限時間を初期化（ダイアログは自動で開かない）
    ask_txt = ""
    ask_path = os.path.join(fdir, "ask.mcfunction")
    if os.path.isfile(ask_path):
        ask_txt = open(ask_path, encoding="utf-8").read()
    check("jiro_state 3" in ask_txt and "dialogue open" not in ask_txt,
          "ask がコール開始（自動オープンなし・タイマー廃止）")
    # order は boot を呼んで、tick.json が走らない環境でもスコア初期化とNPC召喚を行う
    order_txt = ""
    order_path = os.path.join(fdir, "order.mcfunction")
    if os.path.isfile(order_path):
        order_txt = open(order_path, encoding="utf-8").read()
        check("function jiro/boot" in order_txt and "order_mini" in order_txt,
            "order が boot を呼んでから既定のミニを実行する")
    order_player_txt = ""
    order_player_path = os.path.join(fdir, "order_player.mcfunction")
    if os.path.isfile(order_player_path):
        order_player_txt = open(order_player_path, encoding="utf-8").read()
        check("function jiro/order_mini" in order_player_txt,
            "order_player は互換用に order_mini へ委譲する")
    # spawn_npcs が店員＋雰囲気NPCを用意し、タップでダイアログが開くよう割り当てる
    sc = ""
    sc_path = os.path.join(fdir, "spawn_npcs.mcfunction")
    if os.path.isfile(sc_path):
        sc = open(sc_path, encoding="utf-8").read()
    check("summon npc" in sc and "dialogue change" in sc,
          "spawn_npcs が NPC を用意しダイアログを割り当てる")
    check("jiro_clerk" in sc, "店員(jiro_clerk)を召喚する")
    for tag, name, _text, _x, _y, _z, _yaw in C.FLAVOR_NPCS:
        check(tag in sc, f"NPC『{name}』({tag}) を召喚する")
    check(not os.path.isfile(os.path.join(fdir, "timeout.mcfunction")), "タイマー/時間切れは廃止")

    wbp_path = os.path.join(WORK_DIR, "world_behavior_packs.json")
    check(os.path.isfile(wbp_path), "world_behavior_packs.json")
    if os.path.isfile(wbp_path):
        wbp = json.load(open(wbp_path, encoding="utf-8"))
        check(any(e.get("pack_id") == BP_HEADER_UUID and e.get("version") == PACK_VERSION for e in wbp), "BP が有効化登録されている")
    wbh_path = os.path.join(WORK_DIR, "world_behavior_pack_history.json")
    check(os.path.isfile(wbh_path), "world_behavior_pack_history.json")
    if os.path.isfile(wbh_path):
        wbh = json.load(open(wbh_path, encoding="utf-8"))
        check(any(e.get("pack_id") == BP_HEADER_UUID and e.get("version") == PACK_VERSION for e in wbh), "BP 履歴にも登録されている")

        # --- Resource Pack は不使用（画像はImage Mapの地図＋額縁方式）---
    print("[Resource Pack]")
    check(not os.path.isdir(os.path.join(WORK_DIR, "resource_packs")),
            "リソースパック無し（実験的機能を使わない）")
    wrp_path = os.path.join(WORK_DIR, "world_resource_packs.json")
    if check(os.path.isfile(wrp_path), "world_resource_packs.json"):
        wrp = json.load(open(wrp_path, encoding="utf-8"))
        check(wrp == [], "world_resource_packs.json が空（RP 無効）")
    wrh_path = os.path.join(WORK_DIR, "world_resource_pack_history.json")
    if check(os.path.isfile(wrh_path), "world_resource_pack_history.json"):
        wrh = json.load(open(wrh_path, encoding="utf-8"))
        check(wrh == [], "world_resource_pack_history.json が空（RP 無効）")

    # --- level.dat ---
    print("[level.dat]")
    dat = BedrockLevelDAT.from_file(os.path.join(WORK_DIR, "level.dat"))
    t = dat.compound
    check(t.get("GameType").py_int == 2, "GameType=2（アドベンチャー）")
    check(t.get("commandsEnabled").py_int == 1, "commandsEnabled=1")
    check(t.get("commandblocksenabled").py_int == 1, "commandblocksenabled=1")
    check(t.get("commandBlocksEnabled").py_int == 1, "commandBlocksEnabled=1")
    check(t.get("Generator").py_int == 2, "Generator=2（フラット）")
    check("FlatWorldLayers" in t, "FlatWorldLayers がある")
    check(t.get("educationFeaturesEnabled").py_int == 1, "educationFeaturesEnabled=1")
    check(t.get("SpawnZ").py_int == C.SPAWN_Z, f"SpawnZ={C.SPAWN_Z}")
    # 実験機能フラグは使わない（MEE 非対応でBPが拒否される原因だった）
    check(t.get("experiments") is None, "実験機能フラグ無し（MEE で安定動作）")

    print()
    if _errors:
        print(f"=== {len(_errors)} 件の問題 ===")
        for e in _errors:
            print(" - " + e)
        sys.exit(1)
    else:
        print("=== すべて OK ===")


if __name__ == "__main__":
    main()
