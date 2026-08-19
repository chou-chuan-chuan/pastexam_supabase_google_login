#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from fontTools.ttLib import TTFont

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf"
TTF_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf"
WOFF2_PATH = REPO_ROOT / "assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.woff2"

def main() -> int:
    errors: list[str] = []
    def require(cond: bool, msg: str) -> None:
        if not cond:
            errors.append(msg)

    source = TTFont(SOURCE, recalcTimestamp=False)
    ttf = TTFont(TTF_PATH, recalcTimestamp=False)
    woff2 = TTFont(WOFF2_PATH, recalcTimestamp=False)
    try:
        scmap = source.getBestCmap()
        tcmap = ttf.getBestCmap()
        wcmap = woff2.getBestCmap()

        # Stable release policy:
        # 懐 and 夕 must use untouched source ChenYuluoyan glyph mappings.
        for cp, ch in ((0x61D0, "懐"), (0x5915, "夕")):
            require(cp in scmap, f"Source font is missing {ch} U+{cp:04X}")
            require(tcmap.get(cp) == scmap.get(cp),
                    f"{ch} U+{cp:04X} must preserve the source glyph mapping")

        # 々 remains the normal Phase-1 derived Japanese mark, not the recent
        # experimental special redraw.
        repeat_name = tcmap.get(0x3005)
        require(repeat_name is not None, "々 U+3005 is missing")
        if repeat_name is not None:
            require(ttf["hmtx"].metrics[repeat_name][0] == 960,
                    f"々 advance must be 960, got {ttf['hmtx'].metrics[repeat_name][0]}")

        require(tcmap == wcmap, "TTF and WOFF2 cmap differ")
    finally:
        source.close()
        ttf.close()
        woff2.close()

    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        print(f"Stable release verification failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    print("PASS: 懐 preserves the original source glyph")
    print("PASS: 々 uses the baseline Phase-1 mark")
    print("PASS: 夕 preserves the original source glyph")
    print("PASS: TTF/WOFF2 cmap agree")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
