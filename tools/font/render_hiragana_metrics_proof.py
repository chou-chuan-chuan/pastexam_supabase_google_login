#!/usr/bin/env python3
"""Same-em scalar reference boxes, actual-font proof and comparison tables."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import median

from fontTools.ttLib import TTFont
from PIL import Image,ImageDraw,ImageFont
from kana_sources.hiragana_master_v2 import TARGETS
from measure_hiragana_reference_metrics import measure
from render_hiragana_master_v2_proofs import heading,FONT,PROOFS

ROOT=Path(__file__).resolve().parents[2]
REPORTS=ROOT/'tools/font/reports'
KEYS=('width_em','height_em','center_x_em','center_y_em')
REVIEWED_FLAGS={
    'う':'Tall narrow main gesture from the handwriting; width remains within the reference envelope.',
    'く':'Narrow angled handwritten gesture; width remains within the reference envelope.',
    'り':'Narrow two-stroke handwriting; width remains within the reference envelope.',
    'つ':'Shallow handwritten bowl; its per-character standard/production height target takes precedence over a family median.',
    'へ':'Shallow handwritten arch; its per-character standard/production height target takes precedence over a family median.',
}


def main():
    data=json.loads((ROOT/'tools/font/references/hiragana-metric-references.json').read_text())
    fits=json.loads((ROOT/'tools/font/references/hiragana-metric-targets.json').read_text())
    refs=data['references']
    with TTFont(FONT) as f:current={c:measure(f,c) for c in TARGETS}
    stats={k:{'median':median(m[k] for m in current.values()),
              'min':min(m[k] for m in current.values()),'max':max(m[k] for m in current.values())} for k in KEYS}
    summary={'version':'1.025','family_em':stats,'glyphs':{}}
    for c,m in current.items():
        target=fits['glyphs'][c]['target']
        flags=[]
        if m['height_em']<.75*stats['height_em']['median']:flags.append('short relative to family median')
        if m['width_em']<.7*stats['width_em']['median']:flags.append('narrow relative to family median')
        if m['width_em']>1.4*stats['width_em']['median']:flags.append('wide relative to family median')
        assert not flags or c in REVIEWED_FLAGS,(c,'unreviewed family outlier',flags)
        summary['glyphs'][c]={'metrics':m,'deviation_em':{k:m[k]-v for k,v in target.items()},
            'flags':flags,'review':REVIEWED_FLAGS.get(c,'Within the per-character envelope and family size gates.')}
    (REPORTS/'hiragana-standard-metrics.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    # One common 1-em square: y=-.12 through +.88. The separate dotted
    # right boundary is QuanFangwei's unchanged 960/1024-em full-width cell.
    sheet=Image.new('RGB',(1500,2350),'white');d=ImageDraw.Draw(sheet)
    heading(d,'Complete Master v2 / same-em reference metric boxes',
        'Green: Noto / Source Han box + center. Blue: new QuanFangwei ink + box + center. Gray: 1 em; dotted: 960-unit advance.')
    em=144;face=ImageFont.truetype(str(FONT),em);label=ImageFont.load_default(size=15)
    for i,c in enumerate(TARGETS):
        x=35+(i%5)*300;y=112+(i//5)*220;baseline=y+.88*em
        d.rectangle((x,y,x+em,y+em),outline='#d0d4da')
        d.line((x,baseline,x+em,baseline),fill='#d0d4da')
        for yy in range(round(y),round(y+em),8):d.line((x+em*960/1024,yy,x+em*960/1024,yy+4),fill='#b6bbc3')
        d.text((x,baseline),c,font=face,anchor='ls',fill='#2a4265')
        for m,color in ((refs['noto']['glyphs'][c],'#188450'),(current[c],'#527fbd')):
            x0,y0,x1,y1=m['bounds_em']
            d.rectangle((x+x0*em,baseline-y1*em,x+x1*em,baseline-y0*em),outline=color,width=1)
            cx=x+m['center_x_em']*em;cy=baseline-m['center_y_em']*em
            d.line((cx-4,cy,cx+4,cy),fill=color,width=2);d.line((cx,cy-4,cx,cy+4),fill=color,width=2)
        t=fits['glyphs'][c]['transform']
        d.text((x,y+152),f"s {t['scale']:.4f}  dx {t['dx']:+.1f}  dy {t['dy']:+.1f}",font=label,fill='#444d5b')
        d.text((x,y+174),f"w {current[c]['width_em']:.3f}  h {current[c]['height_em']:.3f} em",font=label,fill='#444d5b')
    sheet.save(PROOFS/'quanfangwei-hiragana-standard-metrics.png')
    rows=[]
    for c in TARGETS:
        t=fits['glyphs'][c]['transform']
        for key in ('noto','source_han'):
            r=refs[key];m=r['glyphs'][c];old=refs['production_1_024']['glyphs'][c]
            rows.append([c,r['family']+' '+r['style'],r['upm'],*(m[k] for k in KEYS),
                         *(old[k] for k in KEYS),*(current[c][k] for k in KEYS),t['scale'],t['dx'],t['dy']])
    headers=['glyph','reference_font','reference_upm',*('reference_'+k for k in KEYS),
             *('old_'+k for k in KEYS),*('new_'+k for k in KEYS),'uniform_scale','dx','dy']
    with (REPORTS/'hiragana-standard-metrics.csv').open('w',newline='') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(headers);writer.writerows(rows)
    lines=['# Version 1.025 — standard Japanese size normalization','',
        'Shape remains entirely from the complete maintainer Master v2. Absolute optical size is normalized against standard Japanese metrics; production 1.024 supplies continuity. The family renderer alone supplies stroke weight. No external font outline, curve, point, component or stroke is retained or installed. External font binaries were read from temporary files outside the repository.','',
        '“Optical” measurements here mean actual ink bounding-box extent and its midpoint, not an ink-mass centroid. Coordinates are divided by each font’s UPM before comparison. Baseline bottom/top, normalized bounds and full-width cell occupancy are retained in the [scalar reference snapshot](../references/hiragana-metric-references.json).','',
        '## References','']
    for key in ('noto','source_han'):
        r=refs[key];lines.append(f"- [{r['family']} {r['style']}]({r['provenance']}), {r['version']}, UPM {r['upm']}; SHA256 `{r['sha256']}`.")
    r=refs['production_1_024'];lines+=['',f"Continuity reference: {r['family']} {r['version']}, UPM {r['upm']}, immutable base `{r['provenance']}`; SHA256 `{r['sha256']}`.",'',
        'Noto and Source Han have identical measured width, height and box centers for all 46 glyphs (maximum difference 0 em). They count as one external reference group, paired with the independent production font.','',
        '## Target and fit policy','',
        'For each character, target height and x/y box centers are the median of the external group and production 1.024. Width is a sanity range: 90% of the smaller reference width through 110% of the larger, capped at `(960−40)/1024` em. Height has a ±5% envelope and centers a ±0.02 em envelope; actual fit tolerances are tighter: height ≤1.5 font units, centers ≤1 unit from target.','',
        'One uniform center-line scale is fitted against actual rendered height, followed by dx/dy to the target center. Pressure is not scaled, so the renderer retains the established handwriting weight. Photo coordinates retain only relative gesture/aspect information; photo pixels never set absolute glyph size. All 46 fits are uniform: **no non-uniform exceptions**. Every advance stays **960 units at 1024 UPM**.','',
        'The large bases are normalized before all 12 small forms are derived. The three Hiragana yōon translations are recalibrated afterward to the existing `(180,24)` ink anchor; Katakana offsets and topology remain unchanged.','',
        '## Family size gate','',
        '| Metric (em) | Median | Minimum | Maximum |','|---|---:|---:|---:|']
    for k,s in stats.items():lines.append(f"| {k} | {s['median']:.6f} | {s['min']:.6f} | {s['max']:.6f} |")
    lines+=['','Flags are triggered by height below 75% of the family median, width below 70%, or width above 140%. The following flags were explicitly reviewed against the handwriting and individual reference envelope:','']
    for c,r in summary['glyphs'].items():
        if r['flags']:lines.append(f"- **{c}**: {', '.join(r['flags'])}. {r['review']}")
    lines+=['','## Per-character comparison','',
        'Ratios are `(width, height, center-x, center-y)` in em. dx/dy are QuanFangwei font units; scale applies uniformly to the manually authored source. Both external fonts are listed separately in the [complete CSV](hiragana-standard-metrics.csv); their identical values are grouped here.','',
        '| Glyph | Reference font | UPM | Ref width | Ref height | Ref cx | Ref cy | Old QFW ratios | New QFW ratios | Scale | dx | dy | Δheight / Δcx / Δcy em |',
        '|---|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---|']
    fmt=lambda m:' / '.join(f'{m[k]:.4f}' for k in KEYS)
    for c in TARGETS:
        r=refs['noto']['glyphs'][c];old=refs['production_1_024']['glyphs'][c];t=fits['glyphs'][c]['transform'];dev=summary['glyphs'][c]['deviation_em']
        lines.append(f"| {c} | Noto / Source Han JP Regular | 1000 | {r['width_em']:.4f} | {r['height_em']:.4f} | {r['center_x_em']:.4f} | {r['center_y_em']:.4f} | {fmt(old)} | {fmt(current[c])} | {t['scale']:.6f} | {t['dx']:+.4f} | {t['dy']:+.4f} | "+' / '.join(f'{dev[k]:+.6f}' for k in ('height_em','center_x_em','center_y_em'))+' |')
    lines+=['','[Same-em metric-box proof](../proofs/quanfangwei-hiragana-standard-metrics.png): green reference box/center, blue new glyph/box/center, common gray em cell. No reference glyph outline is displayed.','',
        'Reproduce measurements with `measure_hiragana_reference_metrics.py --noto /outside/repo/NotoSansCJKjp-Regular.otf --source-han /outside/repo/SourceHanSansJP-Regular.otf`; run `normalize_hiragana_metrics.py`, rebuild canonically, render proofs, and verify with `verify_hiragana_metrics.py`. Measurement snapshots are reviewed data; the verifier does not regenerate them.']
    (REPORTS/'hiragana-standard-metrics.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(stats,indent=2));print('Rendered same-em proof, comparison CSV/Markdown and family/deviation JSON')


if __name__=='__main__':main()
