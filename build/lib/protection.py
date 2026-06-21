"""保護・境界。アドベンチャー地図として、見えない壁で来場者をシーン内に留める。"""
from __future__ import annotations

from . import consts as C


def build_protection(w):
    """広場の外周に透明なバリアの壁を立てる（void への転落・場外への逸脱を防ぐ）。"""
    x1, x2 = C.PLAZA_X_MIN, C.PLAZA_X_MAX
    z1, z2 = C.PLAZA_Z_MIN, C.PLAZA_Z_MAX
    y0, y1 = C.FEET_Y, C.FEET_Y + 4
    for y in range(y0, y1 + 1):
        for x in range(x1, x2 + 1):
            w.set_block(x, y, z1, "barrier")
            w.set_block(x, y, z2, "barrier")
        for z in range(z1, z2 + 1):
            w.set_block(x1, y, z, "barrier")
            w.set_block(x2, y, z, "barrier")

    # 広場の床下に薄い「deny」層を敷き、地表ブロックの破壊を抑止（運用で Member 化した時用）。
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            w.set_block(x, C.GROUND_Y - 1, z, "deny")
