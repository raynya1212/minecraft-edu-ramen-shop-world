"""
Behavior Pack の生成。

ゲーム進行を mcfunction の状態機械で実装する（tick.json から毎tick実行）。
スコアボード jiro_state でプレイヤーごとの進行を管理する:
    0=店外 / 1=食券購入済 / 3=コール中(注文) / 5=提供済(退店可)

食券購入→店員NPCをタップするとダイアログが開き、二郎系の正しいコール
(そのまま/ニンニク/ヤサイ/…/全マシマシ)から1つを選んで確定→ラーメン提供。
正しいコールと NG コール（罠）が混在し、NG は退店。

コール入力は店員NPCのダイアログ。Bedrock では NPC を「プレイヤーが直接タップして」
開いたダイアログのボタンだけがコマンドを発火する（/dialogue open のコマンド自動表示
では発火しない）。そのため自動表示はせず、spawn_npcs で
  dialogue change @e[type=npc,tag=jiro_clerk] jiro_call
によりシーンを割り当て、プレイヤーがタップして開く運用にする。各ボタンは
  /scoreboard players set @initiator jiro_call N
でタップした本人にコール番号を立て、loop が拾って提供する。
"""
from __future__ import annotations

import json
import os

from . import consts as C

# BP の UUID/version は、MEE 側の古いパックキャッシュを避けるため大きな仕様変更ごとに更新する。
BP_HEADER_UUID = "b1d0c7a2-4e3f-4a10-9c21-77a0c0ffeeb0"
BP_MODULE_UUID = "b1d0c7a2-4e3f-4a10-9c21-77a0c0ffeeb1"
PACK_VERSION = [1, 9, 0]

# コール可能ゾーン（座席〜カウンター前。食券持ちでここに来るとコール開始）
SEAT_BOX = f"x={C.COUNTER_X_MIN},y={C.FEET_Y},z={C.SEAT_Z - 1},dx={C.COUNTER_X_MAX - C.COUNTER_X_MIN},dy=2,dz=3"
# 店外（広場）ゾーン
OUTSIDE_BOX = f"x={C.PLAZA_X_MIN},y={C.FLOOR_Y},z={C.PLAZA_Z_MIN},dx={C.PLAZA_X_MAX - C.PLAZA_X_MIN},dy=6,dz={-C.PLAZA_Z_MIN + C.SHOP_Z_FRONT}"


def _functions() -> dict[str, str]:
    ns = C.BP_NAMESPACE
    n = len(C.CALL_PRESETS)
    secs = C.CALL_TIME_SECONDS

    objective_boot = """scoreboard objectives add jiro_state dummy
scoreboard objectives add jiro_sec dummy
scoreboard objectives add jiro_call dummy
scoreboard objectives add jiro_sys dummy
scoreboard objectives add jiro_menu dummy
scoreboard objectives add jiro_g dummy
scoreboard objectives add jiro_y dummy
scoreboard objectives add jiro_a dummy
scoreboard objectives add jiro_k dummy
scoreboard objectives add jiro_mm dummy
"""

    # NPCダイアログのボタンが立てる jiro_call(1..n) を loop で拾う行
    call_dispatch = "\n".join(
        f"execute as @a if score @s jiro_state matches 3 if score @s jiro_call matches {i} run function {ns}/call{i}"
        for i in range(1, n + 1)
    )

    # 店員（コール用）＋雰囲気NPC（店員/客）の召喚＆設定行を生成する。
    # その場の位置でタグ付け（r=2 かつ他NPCタグを除外）して複数NPCの取り違えを防ぐ。
    # Microsoft Learn の公式例どおり type=npc を使い、位置＋タグで各NPCを識別する。
    npc_specs = [("jiro_clerk", C.CLERK_X, C.CLERK_Y, C.CLERK_Z, C.CLERK_YAW, C.CALL_SCENE)]
    for _tag, _name, _text, _x, _y, _z, _yaw in C.FLAVOR_NPCS:
        npc_specs.append((_tag, _x, _y, _z, _yaw, _tag))
    _all_npc_tags = [s[0] for s in npc_specs]
    _notags = ",".join(f"tag=!{t}" for t in _all_npc_tags)
    _spawn_lines = []
    for tag, x, y, z, yaw, scene in npc_specs:
        _spawn_lines.append(f"execute unless entity @e[type=npc,tag={tag}] run summon npc {x} {y} {z}")
        _spawn_lines.append(f"execute unless entity @e[type=npc,tag={tag}] run tag @e[type=npc,x={x},y={y},z={z},r=2,c=1,{_notags}] add {tag}")
        _spawn_lines.append(f"tp @e[type=npc,tag={tag}] {x} {y} {z} {yaw} 0")
        _spawn_lines.append(f"dialogue change @e[type=npc,tag={tag}] {scene}")
    spawn_npcs_body = "\n".join(_spawn_lines) + "\n"

    funcs = {
        # 入口: tick.json から毎tick。オブジェクトは毎tick確保（存在すれば無害）し、
        # 別ブートに頼らないことで「最初の1回が走らない」事故を避ける。
        "main": f"""# 毎tick のエントリ
function {ns}/boot
function {ns}/loop
""",
        "noop": "# tick.json intentionally does nothing; hidden repeating command block runs jiro/main.\n",
        # 物理トリガー（入口・食券機）からも呼ぶ初期化。tick.json が動かない環境でも
        # 食券機/NPCの入口処理だけは必ず進むようにする。
        "boot": f"""{objective_boot}execute as @a unless score @s jiro_state matches 0.. run scoreboard players set @s jiro_state 0
execute as @a unless score @s jiro_call matches 0.. run scoreboard players set @s jiro_call 0
execute as @a unless score @s jiro_menu matches 0.. run scoreboard players set @s jiro_menu 0
function {ns}/spawn_npcs
""",
        # 毎tick のメインループ
        "loop": f"""# 新規プレイヤーの初期化
execute as @a unless score @s jiro_state matches 0.. run scoreboard players set @s jiro_state 0
execute as @a unless score @s jiro_call matches 0.. run scoreboard players set @s jiro_call 0
execute as @a unless score @s jiro_menu matches 0.. run scoreboard players set @s jiro_menu 0

# 店員＋客のNPCを用意する（各NPCは個別に存在確認。タップでセリフ/コール）
function {ns}/spawn_npcs

# 食券購入済みでカウンターに座ったらコール開始(state=3)
execute as @a[{SEAT_BOX}] if score @s jiro_state matches 1 run function {ns}/ask

# コール中(state=3): 店員をタップしてコール。制限時間は廃止。
execute as @a if score @s jiro_state matches 3 run title @s actionbar 店員をタップして「ニンニク入れますか？」に答えよう

# NPCダイアログで選んだコールを反映（jiro_call=1..{n}）
{call_dispatch}

# 退店して提供済みなら再挑戦できるようリセット
execute as @a[{OUTSIDE_BOX}] if score @s jiro_state matches 5 run function {ns}/reset_player
""",
        # 店員＋雰囲気NPCを用意する。各NPCは「いなければ召喚→位置でタグ付け」し、
        # 母tick その場へ tp して向きを固定、dialogue change でシーンを割り当てる。
        # 位置タグ付け（r=2 かつ他NPCタグを除外）で複数NPCの取り違えを防ぐ。
        "spawn_npcs": spawn_npcs_body,
        # 食券販売機（ボタン裏のコマンドブロックが呼ぶ）
        "order": f"""function {ns}/boot
execute as @p[r=6] run function {ns}/order_mini
""",
        "order_player": f"""function {ns}/order_mini
""",
        "order_mini": f"""function {ns}/boot
scoreboard players set @s jiro_state 3
scoreboard players set @s jiro_sec 0
scoreboard players set @s jiro_call 0
scoreboard players set @s jiro_menu 1
scoreboard players set @s jiro_g 0
scoreboard players set @s jiro_y 0
scoreboard players set @s jiro_a 0
scoreboard players set @s jiro_k 0
scoreboard players set @s jiro_mm 0
title @s subtitle ラーメン豚 ミニ ¥1540（ちいかわ）
title @s title 食券を買った！
playsound note.pling @s ~ ~ ~ 1 1.2
give @s paper 1
""",
        "order_small": f"""function {ns}/boot
scoreboard players set @s jiro_state 3
scoreboard players set @s jiro_sec 0
scoreboard players set @s jiro_call 0
scoreboard players set @s jiro_menu 2
scoreboard players set @s jiro_g 0
scoreboard players set @s jiro_y 0
scoreboard players set @s jiro_a 0
scoreboard players set @s jiro_k 0
scoreboard players set @s jiro_mm 0
title @s subtitle ラーメン豚 小 ¥1760（ハチワレ）
title @s title 食券を買った！
playsound note.pling @s ~ ~ ~ 1 1.2
give @s paper 1
""",
        "order_large": f"""function {ns}/boot
scoreboard players set @s jiro_state 3
scoreboard players set @s jiro_sec 0
scoreboard players set @s jiro_call 0
scoreboard players set @s jiro_menu 3
scoreboard players set @s jiro_g 0
scoreboard players set @s jiro_y 0
scoreboard players set @s jiro_a 0
scoreboard players set @s jiro_k 0
scoreboard players set @s jiro_mm 0
title @s subtitle ラーメン豚 大 ¥1980（うさぎ）
title @s title 食券を買った！
playsound note.pling @s ~ ~ ~ 1 1.2
give @s paper 1
""",
        # コール開始（食券持ちがカウンターに座ったら）。具材・タイマーを初期化して案内。
        "ask": f"""scoreboard players set @s jiro_state 3
scoreboard players set @s jiro_sec 0
scoreboard players set @s jiro_call 0
scoreboard players set @s jiro_g 0
scoreboard players set @s jiro_y 0
scoreboard players set @s jiro_a 0
scoreboard players set @s jiro_k 0
scoreboard players set @s jiro_mm 0
title @s subtitle 店員をタップして正しいコールを選べ！
title @s title ニンニク入れますか？
playsound random.orb @s ~ ~ ~ 1 1
""",
        # 提供（正しいコール確定）。ラーメンを渡してすぐ退店可にする。
        "serve": f"""scoreboard players set @s jiro_state 5
title @s subtitle ラーメンを受け取った！入口から退店できます
title @s title コール成立！お待ち！
tellraw @s {{"rawtext":[{{"text":"§6=== あなたのコール ==="}}]}}
execute if score @s jiro_menu matches 1 run tellraw @s {{"rawtext":[{{"text":"§eラーメン豚 ミニ ¥1540（ちいかわ）"}}]}}
execute if score @s jiro_menu matches 2 run tellraw @s {{"rawtext":[{{"text":"§eラーメン豚 小 ¥1760（ハチワレ）"}}]}}
execute if score @s jiro_menu matches 3 run tellraw @s {{"rawtext":[{{"text":"§eラーメン豚 大 ¥1980（うさぎ）"}}]}}
execute if score @s jiro_g matches 1 run tellraw @s {{"rawtext":[{{"text":"§f・ニンニク"}}]}}
execute if score @s jiro_y matches 1 run tellraw @s {{"rawtext":[{{"text":"§f・ヤサイ"}}]}}
execute if score @s jiro_a matches 1 run tellraw @s {{"rawtext":[{{"text":"§f・アブラ"}}]}}
execute if score @s jiro_k matches 1 run tellraw @s {{"rawtext":[{{"text":"§f・カラメ"}}]}}
execute if score @s jiro_mm matches 1 run tellraw @s {{"rawtext":[{{"text":"§c・マシマシ！！"}}]}}
execute if score @s jiro_g matches 0 if score @s jiro_y matches 0 if score @s jiro_a matches 0 if score @s jiro_k matches 0 run tellraw @s {{"rawtext":[{{"text":"§7・そのまま（追加トッピングなし）"}}]}}
playsound random.levelup @s ~ ~ ~ 1 1
clear @s bowl
give @s beetroot_soup 1
""",
        # 退店処理（state0 に戻し、食券・どんぶりを没収してスポーンへ）
        "fail": f"""scoreboard players set @s jiro_state 0
scoreboard players set @s jiro_call 0
clear @s beetroot_soup
clear @s bowl
clear @s paper
tp @s {C.SPAWN_X} {C.SPAWN_Y} {C.SPAWN_Z} 0 0
""",
        # 退店後のリセット
        "reset_player": """scoreboard players set @s jiro_state 0
clear @s paper
title @s actionbar またのご来店を！
""",
        # セルフ水コーナー
        "water": """give @p[r=4] potion 1 0
title @p[r=4] actionbar 水をくんだ！
playsound note.pling @p[r=4] ~ ~ ~ 1 1.4
""",
        "oolong": """give @p[r=4] potion 1 0
title @p[r=4] actionbar 黒烏龍茶を買った！ ¥500
playsound note.pling @p[r=4] ~ ~ ~ 1 0.7
""",
    }

    # CALL_PRESETS から callN を生成。OK=正解→提供 / NG→理由を出して退店。
    for i, preset in enumerate(C.CALL_PRESETS, start=1):
        label, ok, g, y, a, k, mm, reason = preset
        if ok:
            funcs[f"call{i}"] = (
                f"scoreboard players set @s jiro_g {g}\n"
                f"scoreboard players set @s jiro_y {y}\n"
                f"scoreboard players set @s jiro_a {a}\n"
                f"scoreboard players set @s jiro_k {k}\n"
                f"scoreboard players set @s jiro_mm {mm}\n"
                f"scoreboard players set @s jiro_call 0\n"
                f"function {ns}/serve\n"
            )
        else:
            funcs[f"call{i}"] = (
                f"scoreboard players set @s jiro_call 0\n"
                f"title @s subtitle {reason}\n"
                f"title @s title コール失敗…退店！\n"
                f'tellraw @s {{"rawtext":[{{"text":"§c{reason}"}}]}}\n'
                f"playsound mob.wither.spawn @s ~ ~ ~ 0.7 0.8\n"
                f"function {ns}/fail\n"
            )

    return funcs


def _dialogue_open_button(name: str, scene_tag: str) -> dict:
    return {
        "name": name,
        "commands": [f"/dialogue open @e[type=npc,tag=jiro_history,c=1] @initiator {scene_tag}"],
    }


def _history_topic_scenes() -> list[dict]:
    scenes = []
    menu_tag = "jiro_history"
    for key, _label, title, pages in C.HISTORY_LESSONS:
        page_count = len(pages)
        for index, page_text in enumerate(pages):
            page_no = index + 1
            scene_tag = f"jiro_history_{key}_{page_no}"
            text = f"{title} ({page_no}/{page_count})\n\n{page_text}"
            buttons = []
            if index > 0:
                buttons.append(_dialogue_open_button("前へ", f"jiro_history_{key}_{page_no - 1}"))
            if index < page_count - 1:
                buttons.append(_dialogue_open_button("次へ", f"jiro_history_{key}_{page_no + 1}"))
            buttons.append(_dialogue_open_button("目次へ", menu_tag))
            scenes.append(
                {
                    "scene_tag": scene_tag,
                    "npc_name": "歴史案内",
                    "text": text,
                    "buttons": buttons,
                }
            )
    return scenes


def _history_quiz_scenes() -> list[dict]:
    scenes = []
    for index, (key, label, question, choices, correct_text, wrong_text) in enumerate(C.HISTORY_QUIZ):
        question_tag = f"jiro_history_{key}"
        next_tag = f"jiro_history_{C.HISTORY_QUIZ[index + 1][0]}" if index + 1 < len(C.HISTORY_QUIZ) else "jiro_history"
        buttons = []
        for choice_index, (choice_label, is_correct) in enumerate(choices, start=1):
            result_tag = f"{question_tag}_{'ok' if is_correct else 'ng'}_{choice_index}"
            buttons.append(_dialogue_open_button(choice_label, result_tag))
            scenes.append(
                {
                    "scene_tag": result_tag,
                    "npc_name": "歴史案内",
                    "text": correct_text if is_correct else wrong_text,
                    "buttons": [
                        _dialogue_open_button("次へ" if index + 1 < len(C.HISTORY_QUIZ) else "目次へ", next_tag),
                        _dialogue_open_button("問題に戻る", question_tag),
                    ],
                }
            )
        scenes.append(
            {
                "scene_tag": question_tag,
                "npc_name": "歴史案内",
                "text": f"{label}\n\n{question}",
                "buttons": buttons + [_dialogue_open_button("目次へ", "jiro_history")],
            }
        )
    return scenes


def _dialogue_scenes() -> dict:
    """店内NPCのダイアログ全シーンを1ファイルにまとめて返す。

    - コール用シーン(CALL_SCENE): ボタンに正しいコールと NG コール（罠）が混在し、
      タップ本人(@initiator)に jiro_call を立てる。loop 側で正誤を判定する。
    - 雰囲気NPCのシーン: 役割に応じたセリフ。歴史案内だけはページ式の学習ダイアログ。
    """
    call_buttons = []
    for i, preset in enumerate(C.CALL_PRESETS, start=1):
        label = preset[0]
        call_buttons.append(
            {
                "name": label,
                "commands": [
                    f"/execute as @initiator if score @s jiro_state matches 3 run scoreboard players set @s jiro_call {i}",
                    f"/execute as @initiator if score @s jiro_state matches 3 run function {C.BP_NAMESPACE}/call{i}"
                ],
            }
        )
    scenes = [
        {
            "scene_tag": C.CALL_SCENE,
            "npc_name": "郎の店主",
            "text": "ニンニク入れますか？",
            "buttons": call_buttons,
        }
    ]
    # 雰囲気NPC（店員/客）のセリフシーン。歴史案内だけはページ式の学習ボタンを置く。
    for tag, name, text, _x, _y, _z, _yaw in C.FLAVOR_NPCS:
        buttons = []
        if tag == "jiro_history":
            buttons = [_dialogue_open_button(label, f"jiro_history_{key}_1") for key, label, _title, _pages in C.HISTORY_LESSONS]
            buttons.append(_dialogue_open_button("ミニクイズ", f"jiro_history_{C.HISTORY_QUIZ[0][0]}"))
        scenes.append(
            {
                "scene_tag": tag,
                "npc_name": name,
                "text": text,
                "buttons": buttons,
            }
        )
    scenes.extend(_history_topic_scenes())
    scenes.extend(_history_quiz_scenes())
    return {
        "format_version": "1.17.0",
        "minecraft:npc_dialogue": {"scenes": scenes},
    }


def build_behavior_pack(world_path: str):
    """ワールド内に Behavior Pack 一式と world_behavior_packs.json を書き出す。"""
    bp_root = os.path.join(world_path, "behavior_packs", C.BP_NAME)
    func_dir = os.path.join(bp_root, "functions", C.BP_NAMESPACE)
    os.makedirs(func_dir, exist_ok=True)

    # manifest.json
    manifest = {
        "format_version": 2,
        "header": {
            "name": "Chiikawa Jiro Ramen Game",
            "description": "Runs the ticket, NPC, call, and ramen flow for the world.",
            "uuid": BP_HEADER_UUID,
            "version": PACK_VERSION,
            "min_engine_version": [1, 20, 0],
        },
        "modules": [
            {
                "type": "data",
                "uuid": BP_MODULE_UUID,
                "version": PACK_VERSION,
            }
        ],
    }
    with open(os.path.join(bp_root, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # tick.json は空回し。実機差を避けるため、床下のリピートコマンドブロックで jiro/main を回す。
    with open(os.path.join(bp_root, "functions", "tick.json"), "w", encoding="utf-8") as f:
        json.dump({"values": [f"{C.BP_NAMESPACE}/noop"]}, f, ensure_ascii=False, indent=2)

    # 各 mcfunction
    for name, body in _functions().items():
        with open(os.path.join(func_dir, f"{name}.mcfunction"), "w", encoding="utf-8") as f:
            f.write(body)

    # 店内NPCのダイアログ全シーン（コール＋雰囲気NPC）を1ファイルに書き出す。
    dlg_dir = os.path.join(bp_root, "dialogue")
    os.makedirs(dlg_dir, exist_ok=True)
    with open(os.path.join(dlg_dir, f"{C.CALL_SCENE}.json"), "w", encoding="utf-8") as f:
        json.dump(_dialogue_scenes(), f, ensure_ascii=False, indent=2)

    # world_behavior_packs.json（ワールドで BP を有効化）
    wbp = [{"pack_id": BP_HEADER_UUID, "version": PACK_VERSION}]
    with open(os.path.join(world_path, "world_behavior_packs.json"), "w", encoding="utf-8") as f:
        json.dump(wbp, f, ensure_ascii=False, indent=2)
    with open(os.path.join(world_path, "world_behavior_pack_history.json"), "w", encoding="utf-8") as f:
        json.dump(wbp, f, ensure_ascii=False, indent=2)

    # resource pack は使わないが空配列を用意
    with open(os.path.join(world_path, "world_resource_packs.json"), "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    with open(os.path.join(world_path, "world_resource_pack_history.json"), "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
