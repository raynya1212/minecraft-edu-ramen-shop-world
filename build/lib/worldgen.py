"""
種ワールドの生成と level.dat の作り込み。

Amulet で空の LevelDB ワールドを作り、Minecraft Education / Bedrock が
クリエイティブ＋コマンドONで開けるように level.dat を整える。
"""
from __future__ import annotations

import json
import os
import shutil

from amulet.level.formats.leveldb_world.format import LevelDBFormat, BedrockLevelDAT
from amulet_nbt import (
    CompoundTag,
    ListTag,
    ByteTag,
    IntTag,
    LongTag,
    FloatTag,
    StringTag,
)

from .consts import (
    VERSION_TUPLE,
    WORLD_NAME,
    FLAT_LAYERS,
    SPAWN_X,
    SPAWN_Y,
    SPAWN_Z,
)


def create_seed_world(path: str):
    """空の Bedrock ワールドを生成する（levelname.txt まで用意）。"""
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)

    fmt = LevelDBFormat(path)
    fmt.create_and_open("bedrock", VERSION_TUPLE, overwrite=True)
    fmt.close()

    # create_and_open は levelname.txt を書かない。ローダ判定に必須なので用意。
    with open(os.path.join(path, "levelname.txt"), "w", encoding="utf-8") as f:
        f.write(WORLD_NAME)


def _flat_world_layers_json() -> str:
    return json.dumps(
        {
            "biome_id": 1,
            "block_layers": [
                {"block_name": name, "count": count} for name, count in FLAT_LAYERS
            ],
            "encoding_version": 6,
            "structure_options": None,
            "world_version": "version.post_1_18",
        },
        ensure_ascii=False,
    )


def write_level_dat(path: str):
    """level.dat を Education/Bedrock 向けに作り込んで保存する。"""
    v = list(VERSION_TUPLE) + [0] * (5 - len(VERSION_TUPLE))

    root = CompoundTag()

    # バージョン・ストレージ
    root["StorageVersion"] = IntTag(8)
    root["NetworkVersion"] = IntTag(630)
    root["lastOpenedWithVersion"] = ListTag([IntTag(i) for i in v])
    root["MinimumCompatibleClientVersion"] = ListTag([IntTag(i) for i in v])
    root["InventoryVersion"] = StringTag(
        ".".join(str(i) for i in VERSION_TUPLE)
    )
    root["Platform"] = IntTag(2)
    root["isWorldTemplateOptionLocked"] = ByteTag(0)

    # 基本情報
    root["LevelName"] = StringTag(WORLD_NAME)
    root["RandomSeed"] = LongTag(0)
    root["LastPlayed"] = LongTag(0)

    # 生成器（2 = フラット）
    root["Generator"] = IntTag(2)
    root["FlatWorldLayers"] = StringTag(_flat_world_layers_json())
    root["world_policies"] = CompoundTag({})

    # ゲームモード・難易度
    # 既定はアドベンチャー(2)。ただし Minecraft Education では能力を強く絞ると
    # ボタン操作までできなくなる環境があるため、ForceGameType と能力固定は緩める。
    root["GameType"] = IntTag(2)        # アドベンチャー
    root["Difficulty"] = IntTag(1)
    root["ForceGameType"] = ByteTag(0)
    root["spawnMobs"] = ByteTag(1)

    # スポーン
    root["SpawnX"] = IntTag(int(SPAWN_X))
    root["SpawnY"] = IntTag(int(SPAWN_Y))
    root["SpawnZ"] = IntTag(int(SPAWN_Z))
    root["LimitedWorldOriginX"] = IntTag(int(SPAWN_X))
    root["LimitedWorldOriginY"] = IntTag(int(SPAWN_Y))
    root["LimitedWorldOriginZ"] = IntTag(int(SPAWN_Z))

    # コマンド・チート
    root["commandsEnabled"] = ByteTag(1)
    root["commandblockoutput"] = ByteTag(0)
    root["commandblocksenabled"] = ByteTag(1)
    root["commandBlocksEnabled"] = ByteTag(1)
    root["sendcommandfeedback"] = ByteTag(0)
    root["functioncommandlimit"] = IntTag(10000)
    root["maxcommandchainlength"] = IntTag(65535)

    # 権限（参加者は Member、運営は Operator に上げられる）
    root["permissionsLevel"] = IntTag(0)
    root["playerPermissionsLevel"] = IntTag(1)
    root["abilities"] = CompoundTag(
        {
            "attackmobs": ByteTag(1),
            "attackplayers": ByteTag(1),
            "build": ByteTag(1),
            "doorsandswitches": ByteTag(1),
            "flISpeed": FloatTag(0.05),
            "flying": ByteTag(0),
            "instabuild": ByteTag(1),
            "invulnerable": ByteTag(0),
            "lightning": ByteTag(0),
            "mayfly": ByteTag(1),
            "mine": ByteTag(1),
            "op": ByteTag(0),
            "opencontainers": ByteTag(1),
            "permissionsLevel": IntTag(0),
            "playerPermissionsLevel": IntTag(1),
            "teleport": ByteTag(1),
            "walkSpeed": FloatTag(0.1),
        }
    )

    # Education 機能を有効化
    root["eduOffer"] = IntTag(1)
    root["educationFeaturesEnabled"] = ByteTag(1)
    root["hasLockedBehaviorPack"] = ByteTag(0)
    root["hasLockedResourcePack"] = ByteTag(0)
    root["isFromLockedTemplate"] = ByteTag(0)
    root["isFromWorldTemplate"] = ByteTag(0)
    root["texturePacksRequired"] = ByteTag(0)

    # 表示・補助
    root["showcoordinates"] = ByteTag(1)
    root["showbordereffect"] = ByteTag(1)
    root["showtags"] = ByteTag(1)
    root["showdeathmessages"] = ByteTag(1)
    root["recipesunlock"] = ByteTag(0)
    root["dolimitedcrafting"] = ByteTag(0)

    # 時間・天候を固定（昼・晴れ）
    root["Time"] = LongTag(6000)
    root["currentTick"] = LongTag(0)
    root["doDayLightCycle"] = ByteTag(0)
    root["dodaylightcycle"] = ByteTag(0)
    root["doweathercycle"] = ByteTag(0)
    root["rainLevel"] = FloatTag(0.0)
    root["rainTime"] = IntTag(2147483647)
    root["lightningLevel"] = FloatTag(0.0)
    root["lightningTime"] = IntTag(2147483647)
    root["SpawnRadius"] = IntTag(0)

    # 各種ゲームルール（保護寄り・安定寄り）
    root["domobspawning"] = ByteTag(0)
    root["domobloot"] = ByteTag(1)
    root["dotiledrops"] = ByteTag(1)
    root["doentitydrops"] = ByteTag(1)
    root["dofiretick"] = ByteTag(0)
    root["doinsomnia"] = ByteTag(0)
    root["domobgriefing"] = ByteTag(0)
    root["doimmediaterespawn"] = ByteTag(0)
    root["drowningdamage"] = ByteTag(1)
    root["falldamage"] = ByteTag(0)
    root["firedamage"] = ByteTag(1)
    root["freezedamage"] = ByteTag(1)
    root["keepinventory"] = ByteTag(1)
    root["mobgriefing"] = ByteTag(0)
    root["naturalregeneration"] = ByteTag(1)
    root["pvp"] = ByteTag(0)
    root["respawnblocksexplode"] = ByteTag(0)
    root["showcoordinates"] = ByteTag(1)
    root["tntexplodes"] = ByteTag(0)
    root["tntexplosiondropdecay"] = ByteTag(0)
    root["respawndimension"] = IntTag(0)
    root["randomtickspeed"] = IntTag(0)  # 作物などのランダム更新を止める

    # 保護（MD のレシピに合わせて immutable も用意。BP 側でも維持する）
    root["immutableWorld"] = ByteTag(0)  # 建築検証中は 0。運用で 1 にできる
    root["worldStartCount"] = LongTag(4294967295)
    root["serverChunkTickRange"] = IntTag(6)
    root["startWithMapEnabled"] = ByteTag(0)
    root["bonusChestEnabled"] = ByteTag(0)
    root["bonusChestSpawned"] = ByteTag(0)
    root["MapFeatures"] = ByteTag(0)
    root["confirmedPlatformLockedContent"] = ByteTag(0)
    root["LANBroadcast"] = ByteTag(1)
    root["LANBroadcastIntent"] = ByteTag(1)
    root["MultiplayerGame"] = ByteTag(1)
    root["MultiplayerGameIntent"] = ByteTag(1)
    root["XBLBroadcastIntent"] = IntTag(3)
    root["PlatformBroadcastIntent"] = IntTag(3)
    root["cheatsEnabled"] = ByteTag(1)
    root["hasBeenLoadedInCreative"] = ByteTag(1)
    root["spawnGameMode"] = IntTag(2)

    # Bedrock の level.dat は先頭に [version(4B) + length(4B)] のヘッダが必要。
    # BedrockLevelDAT.save_to が正しいヘッダと文字エンコーダで書き出す。
    dat = BedrockLevelDAT(
        root, "", path=os.path.join(path, "level.dat"), level_dat_version=9
    )
    dat.save()
    dat_old = BedrockLevelDAT(
        root, "", path=os.path.join(path, "level.dat_old"), level_dat_version=9
    )
    dat_old.save()
