#!/usr/bin/env python3
"""Measure final kana/mark ink separation using adaptively flattened curves.

Quadratic contours are flattened to 0.02 font-unit flatness. Segment distances
measure the actual diagonal gap; vertical scans report the local upper stroke
where base and mark overlap in X. Filled-path intersection is checked separately.
"""
from __future__ import annotations

from io import BytesIO
import subprocess

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

from measure_kana_kanji_balance import ROOT, FONT_REL
from verify_supplement_font import bounds, mark_to_base_anchors, outlines_intersect

BASE_MAIN = '514297a9c801e981333fded9473d61489669b486'
BASE_TTF_SHA256 = '16eb157eadd5fcb100eba444b96cbaa925853116c8d514b675f3bad4e4671457'
OLD_OFFSET = 17
FLATNESS = 0.02


def baseline_bytes():
    return subprocess.check_output(['git','show',f'{BASE_MAIN}:{FONT_REL}'],cwd=ROOT)


class OutlinePen(BasePen):
    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.segments = []

    def _moveTo(self, point):
        self.first = self.last = np.array(point,dtype=float)

    def _lineTo(self, point):
        point = np.array(point,dtype=float)
        if np.any(point != self.last):
            self.segments.append((self.last,point))
        self.last = point

    def _qCurveToOne(self, control, end):
        def flatten(a,b,c):
            # Midpoint deviation bound for a quadratic Bezier from its chord.
            if np.linalg.norm(a-2*b+c)/4 <= FLATNESS:
                self._lineTo(c)
                return
            ab,bc = (a+b)/2,(b+c)/2
            middle = (ab+bc)/2
            flatten(a,ab,middle); flatten(middle,bc,c)
        flatten(self.last,np.array(control),np.array(end))

    def _closePath(self):
        self._lineTo(self.first)

    def _endPath(self):
        pass


def segments(font, name, delta=(0,0)):
    gs = font.getGlyphSet(); pen = OutlinePen(gs); gs[name].draw(pen)
    return np.array(pen.segments) + np.array(delta)


def point_segment_distances(points, lines):
    start,end = lines[:,0],lines[:,1]
    direction = end-start
    t = np.sum((points[:,None,:]-start)*direction,axis=2)/np.sum(direction*direction,axis=1)
    nearest = start + np.clip(t,0,1)[:,:,None]*direction
    distances = np.linalg.norm(points[:,None,:]-nearest,axis=2)
    i,j = np.unravel_index(np.argmin(distances),distances.shape)
    return float(distances[i,j]),points[i],nearest[i,j]


def contour_distance(a,b):
    forward = point_segment_distances(a.reshape(-1,2),b)
    reverse = point_segment_distances(b.reshape(-1,2),a)
    return forward if forward[0] <= reverse[0] else (reverse[0],reverse[2],reverse[1])


def vertical_intersections(lines,x):
    a,b = lines[:,0],lines[:,1]
    dx = b[:,0]-a[:,0]
    active = (np.minimum(a[:,0],b[:,0]) <= x) & (x <= np.maximum(a[:,0],b[:,0])) & (abs(dx)>1e-12)
    a,b,dx = a[active],b[active],dx[active]
    return a[:,1]+(x-a[:,0])*(b[:,1]-a[:,1])/dx


def measure(font, base='て', extra_y=0):
    name = f'uni{ord(base):04X}'
    bp,mp,_ = mark_to_base_anchors(font,'uni3099',name)
    delta = (bp[0]-mp[0],bp[1]-mp[1]+extra_y)
    bb,mb = bounds(font,name),bounds(font,'uni3099')
    placed = (mb[0]+delta[0],mb[1]+delta[1],mb[2]+delta[0],mb[3]+delta[1])
    a,b = segments(font,name),segments(font,'uni3099',delta)
    distance,base_point,mark_point = contour_distance(a,b)
    intersects = outlines_intersect(font,name,'uni3099',delta)
    lo,hi = max(bb[0],placed[0]),min(bb[2],placed[2])
    vertical = []
    for x in np.linspace(lo,hi,max(2,int((hi-lo)/.05)+1)) if lo < hi else []:
        base_y,mark_y = vertical_intersections(a,x),vertical_intersections(b,x)
        if len(base_y) and len(mark_y):
            vertical.append((float(min(mark_y)-max(base_y)),float(x),float(max(base_y)),float(min(mark_y))))
    return {
        'base':base,'base_bounds':list(bb),'mark_bounds':list(placed),
        'base_anchor':[bp[0],bp[1]+extra_y],'mark_anchor':list(mp),'mark_delta':list(delta),
        'minimum_clearance':0.0 if intersects else distance,'intersects':intersects,
        'closest_base_point':base_point.tolist(),'closest_mark_point':mark_point.tolist(),
        'x_overlap':[lo,hi], 'minimum_vertical_gap':list(min(vertical)) if vertical else None,
    }


def offset_delta(offset):
    """Existing scoped offsets live before the accepted 1.026 anchor scale."""
    from japanese.build_kana import accepted_base_bounds, KANA_VERTICAL_SHIFT_1_026, JAPANESE_BOTTOM_ALIGNMENT_SHIFT
    from kana_sources.han_balance import HIRAGANA_HAN_BALANCE_SCALE
    _,y0,_,y1 = accepted_base_bounds('て'); cy = (y0+y1)/2
    def anchor(value):
        return round(cy+(835+KANA_VERTICAL_SHIFT_1_026+value-cy)*HIRAGANA_HAN_BALANCE_SCALE)+JAPANESE_BOTTOM_ALIGNMENT_SHIFT
    return anchor(offset)-anchor(OLD_OFFSET)


def candidate_font(offset):
    font = TTFont(BytesIO(baseline_bytes()),recalcTimestamp=False)
    delta = offset_delta(offset)
    glyph = font['glyf']['uni3067']
    glyph.components[1].y += delta
    glyph.recalcBounds(font['glyf'])
    matches = 0
    for lookup in font['GPOS'].table.LookupList.Lookup:
        if lookup.LookupType == 4:
            for sub in lookup.SubTable:
                if 'uni3099' in sub.MarkCoverage.glyphs and 'uni3066' in sub.BaseCoverage.glyphs:
                    matches += 1
                    record = sub.BaseArray.BaseRecord[sub.BaseCoverage.glyphs.index('uni3066')]
                    for anchor in record.BaseAnchor:
                        if anchor:
                            anchor.YCoordinate += delta
    assert matches == 1
    return font
