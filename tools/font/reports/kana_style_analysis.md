# Kana style analysis

This report measures only the official ChenYuluoyan source. The kana contours are original work and do not use external Japanese font outlines.

## Aggregate observations

- Units per em: 1024
- hhea ascent/descent: 967 / -362
- Median reference advance: 740.0 units
- Median ink width/height: 535.5 / 582.5 units
- Median short-run stroke proxy: 51.2 font units (21.0px at 420px proof size)
- Median optical center: x=354.2, y=320.0
- Requested references absent from the official source cmap: 乀
- Endpoint style: pressure-like rounded or tapered ends; short dots often lean down-right and are not geometric capsules.
- Curve character: loose quadratic sweeps with visibly changing curvature, restrained hooks, and open counters.
- Handwriting slant: mostly upright with local rightward motion on falling strokes; no global mechanical italic transform.
- Center of gravity: slightly above the geometric center, with generous lower and side breathing room.
- Character-box use: variable rather than monospaced-looking ink, while CJK advances cluster around the em width.
- Baseline/optical center: glyph ink stays comfortably inside the source ascent/descent; kana target y=70..850 with optical center near y=455.
- Natural irregularity: stroke widths, joins, and terminal angles vary slightly; repeated primitives receive per-glyph optical adjustment.

## Reference glyph metrics

| Character | Glyph | Advance | LSB | Bounds | Ink box (% em) |
|---|---|---:|---:|---|---:|
| 一 | uni4E00 | 713 | 91 | (91, 293, 577, 407) | 5.3% |
| 丨 | uni4E28 | 285 | 104 | (104, -49, 155, 689) | 3.6% |
| 丿 | uni4E3F | 569 | 98 | (98, -63, 481, 763) | 30.2% |
| 丶 | uni4E36 | 489 | 87 | (87, 155, 358, 485) | 8.5% |
| 乙 | uni4E59 | 734 | 85 | (86, 99, 604, 540) | 21.8% |
| 了 | uni4E86 | 685 | 121 | (121, 19, 497, 662) | 23.1% |
| 口 | uni53E3 | 606 | 94 | (94, 119, 476, 521) | 14.6% |
| 日 | uni65E5 | 535 | 97 | (97, 122, 402, 577) | 13.2% |
| 心 | uni5FC3 | 1092 | 91 | (91, 163, 972, 538) | 31.5% |
| 女 | uni5973 | 774 | 86 | (86, 52, 648, 588) | 28.7% |
| 子 | uni5B50 | 701 | 86 | (86, -5, 575, 645) | 30.3% |
| 之 | uni4E4B | 801 | 88 | (88, 5, 724, 635) | 38.2% |
| 也 | uni4E5F | 939 | 86 | (86, 55, 810, 585) | 36.6% |
| 乃 | uni4E43 | 807 | 87 | (87, -136, 681, 644) | 44.2% |
| 川 | uni5DDD | 715 | 89 | (89, -153, 576, 593) | 34.6% |
| 久 | uni4E45 | 856 | 88 | (88, 36, 731, 684) | 39.7% |
| 九 | uni4E5D | 820 | 86 | (86, 6, 691, 635) | 36.3% |
| 千 | uni5343 | 764 | 87 | (87, -59, 640, 699) | 40.0% |
| 小 | uni5C0F | 865 | 89 | (90, 149, 742, 531) | 23.8% |
| 大 | uni5927 | 746 | 89 | (89, 53, 674, 587) | 29.8% |
