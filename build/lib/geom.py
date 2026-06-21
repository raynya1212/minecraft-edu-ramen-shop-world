"""
Amulet レベルの薄いラッパとブロック配置ヘルパ。

座標は Bedrock の絶対座標。set_block は base name（"white_concrete" など）と
任意のブロック状態 props、任意の Block Entity を受け取る。
"""
from __future__ import annotations

import os

import amulet
from amulet.api.block import Block
from amulet.api.block_entity import BlockEntity
from amulet_nbt import ByteTag, FloatTag, IntTag, LongTag, StringTag, CompoundTag

from .consts import VERSION, DIM


def _to_tag(value):
    """python 値を Bedrock のブロック状態タグへ変換する。"""
    if isinstance(value, bool):
        return ByteTag(1 if value else 0)
    if isinstance(value, int):
        return IntTag(value)
    if isinstance(value, str):
        return StringTag(value)
    return value  # すでに amulet_nbt タグ


class WorldWriter:
    """Amulet レベルを開いてブロックを書き込むためのラッパ。"""

    def __init__(self, path: str):
        self.path = path
        self.level = amulet.load_level(path)

    # --- 基本 ---
    def set_block(self, x, y, z, name, props=None, block_entity=None):
        if name == "air":
            block = Block("minecraft", "air")
        else:
            # "jiro:tile_..." のように名前空間付きならそれを尊重する（カスタムブロック）。
            if ":" in name:
                namespace, base = name.split(":", 1)
            else:
                namespace, base = "minecraft", name
            if props:
                block = Block(
                    namespace, base, {k: _to_tag(v) for k, v in props.items()}
                )
            else:
                block = Block(namespace, base)
        self.level.set_version_block(
            int(x), int(y), int(z), DIM, VERSION, block, block_entity
        )

    def fill(self, x1, y1, z1, x2, y2, z2, name, props=None):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    self.set_block(x, y, z, name, props)

    def fill_hollow(self, x1, y1, z1, x2, y2, z2, name, props=None):
        """外殻だけを埋める（中は触らない）。"""
        xmin, xmax = min(x1, x2), max(x1, x2)
        ymin, ymax = min(y1, y2), max(y1, y2)
        zmin, zmax = min(z1, z2), max(z1, z2)
        for x in range(xmin, xmax + 1):
            for y in range(ymin, ymax + 1):
                for z in range(zmin, zmax + 1):
                    if (
                        x in (xmin, xmax)
                        or y in (ymin, ymax)
                        or z in (zmin, zmax)
                    ):
                        self.set_block(x, y, z, name, props)

    # --- Block Entity 系 ---
    def set_sign(self, x, y, z, name, text, props=None, glowing=True):
        """看板を設置する。name は standing_sign / *_wall_sign など。"""
        nbt = CompoundTag(
            {
                "id": StringTag("Sign"),
                "x": IntTag(int(x)),
                "y": IntTag(int(y)),
                "z": IntTag(int(z)),
                "FrontText": CompoundTag(
                    {
                        "Text": StringTag(text),
                        "TextOwner": StringTag(""),
                        "SignTextColor": IntTag(-16777216),
                        "IgnoreLighting": ByteTag(1 if glowing else 0),
                        "GlowingText": ByteTag(1 if glowing else 0),
                        "PersistFormatting": ByteTag(1),
                        "HideGlowOutline": ByteTag(0),
                    }
                ),
                "BackText": CompoundTag(
                    {
                        "Text": StringTag(""),
                        "TextOwner": StringTag(""),
                        "SignTextColor": IntTag(-16777216),
                        "IgnoreLighting": ByteTag(0),
                        "GlowingText": ByteTag(0),
                        "PersistFormatting": ByteTag(1),
                        "HideGlowOutline": ByteTag(0),
                    }
                ),
                "IsWaxed": ByteTag(0),
            }
        )
        be = BlockEntity("minecraft", "Sign", int(x), int(y), int(z), nbt)
        self.set_block(x, y, z, name, props, be)

    def set_command_block(self, x, y, z, command, props=None, name_tag="", auto=False, block_name="command_block"):
        """コマンドブロックを設置する（既定はレッドストーン駆動）。"""
        if props is None:
            props = {"facing_direction": 0, "conditional_bit": False}
        mode = 1 if block_name == "repeating_command_block" else 0
        nbt = CompoundTag(
            {
                "id": StringTag("CommandBlock"),
                "x": IntTag(int(x)),
                "y": IntTag(int(y)),
                "z": IntTag(int(z)),
                "Command": StringTag(command),
                "CustomName": StringTag(name_tag),
                "auto": ByteTag(1 if auto else 0),
                "powered": ByteTag(0),
                "conditionMet": ByteTag(0),
                "TrackOutput": ByteTag(0),
                "Version": IntTag(38),
                "LPRoO": ByteTag(0),  # LastPerformedRedstoneOutputResult 系の保険
                "LPCommandMode": IntTag(mode),
                "LPCondionalMode": ByteTag(0),
                "LPRedstoneMode": ByteTag(1 if auto else 0),
            }
        )
        be = BlockEntity("minecraft", "CommandBlock", int(x), int(y), int(z), nbt)
        self.set_block(x, y, z, block_name, props, be)

    def set_filled_map_frame(self, x, y, z, map_id, facing_direction, rotation=0):
        """Bedrock の額縁(frame)に filled_map を入れて設置する。"""
        item = CompoundTag(
            {
                "Name": StringTag("minecraft:filled_map"),
                "Count": ByteTag(1),
                "tag": CompoundTag({"map_uuid": LongTag(int(map_id))}),
            }
        )
        nbt = CompoundTag(
            {
                "id": StringTag("ItemFrame"),
                "x": IntTag(int(x)),
                "y": IntTag(int(y)),
                "z": IntTag(int(z)),
                "Item": item,
                "ItemDropChance": FloatTag(1.0),
                "ItemRotation": ByteTag(int(rotation)),
            }
        )
        be = BlockEntity("minecraft", "ItemFrame", int(x), int(y), int(z), nbt)
        self.set_block(
            x, y, z, "frame",
            {"facing_direction": int(facing_direction), "item_frame_map_bit": True},
            be,
        )

    # --- 保存 ---
    def save(self):
        self.level.save()

    def close(self):
        self.level.close()
