#!/usr/bin/env python3
"""Verify shared note geometry against real font ink and immutable assets."""
from pathlib import Path
import hashlib
from fontTools.ttLib import TTFont
from note_math_layout import NoteMathLayout, CONJUGATE_SCALE, ORDINARY_SCRIPT_SCALE, RELATION_CHARACTERS, RELATION_SIDE_EM, BINARY_SIDE_EM, RADICAL_SCALE, RADICAL_BOTTOM_INSET, PARENTHESIS_CHARACTERS, PARENTHESIS_SIDE_EM

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / 'assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf'
HASHES = {
    'ttf': 'e902a5e108c8da8e0ea75939148c5f55df01d5399487d760fd94bd8d0647656c',
    'woff2': '15a21205d545b1d4e97162eae0a48f6b9430914ba8305be4ab497f01fd9b84c9',
}


def verify():
    for extension, digest in HASHES.items():
        assert hashlib.sha256(FONT.with_suffix('.' + extension).read_bytes()).hexdigest() == digest
    with TTFont(FONT) as font:
        layout = NoteMathLayout(font)

        def metrics(text, size):
            advance = sum(font['hmtx'][layout.cmap[ord(c)]][0] * layout.scale(size) for c in text)
            return layout.text_metrics(text, size, advance)

        assert CONJUGATE_SCALE == 1 and ORDINARY_SCRIPT_SCALE == .65
        for size in (16, 20, 32, 64):
            gap = RELATION_SIDE_EM * layout.units * layout.scale(size)
            for relation in RELATION_CHARACTERS:
                assert layout.relation_spacing('a'+relation+'b',size) == [(0,0),(gap,gap),(0,0)]
                for source in ('a '+relation+' b', 'a  '+relation+'  b'):
                    pads=layout.relation_spacing(source,size)
                    space_width=font['hmtx'][layout.cmap[ord(' ')]][0]*layout.scale(size)
                    count=1 if source.startswith('a '+relation) else 2
                    actual=pads[source.index(relation)]
                    assert all(abs(p+count*space_width-max(gap,count*space_width))<1e-9 for p in actual)
            assert all(pair == (0,0) for pair in layout.relation_spacing('x−y+x^2',size))
            assert all(abs(p-gap*.65)<1e-9 for p in layout.relation_spacing('=',size*.65)[0])
            paren_gap=PARENTHESIS_SIDE_EM*layout.units*layout.scale(size)
            for paren in PARENTHESIS_CHARACTERS:
                assert layout.relation_spacing(paren,size)==[(paren_gap,paren_gap)]
                assert layout.relation_spacing('  '+paren+'  ',size)[2]==(0,0)
            assert layout.relation_spacing('(x)',size)==[(paren_gap,paren_gap),(0,0),(paren_gap,paren_gap)]
            binary_gap=BINARY_SIDE_EM*layout.units*layout.scale(size)
            assert layout.binary_spacing(size)==(binary_gap,binary_gap)
            assert layout.binary_spacing(size,'x  ','  y')==(0,0)
            for sign in ('+','−'):
                for before,after in (('x','y'),(')','ω'),('2','\\frac{a}{b}')):
                    assert layout.is_binary_sign(sign,before,after)
                for before,after in (('','∞'),('(','x'),('=','α'),('→','∞'),('−','y'),('x','}')):
                    assert not layout.is_binary_sign(sign,before,after)
            for base in ('x', 'p', 'H', 'A', 'B', 'ψ', 'φ', 'ℒ'):
                original = metrics(base, size)
                dx, dy, measured = layout.hat_geometry(base, original, size)
                mark, body = layout.bounds('\u0302'), layout.bounds(base)
                scale = layout.scale(size)
                left, right = dx + mark[0] * scale, dx + mark[2] * scale
                top, bottom = dy - mark[3] * scale, dy - mark[1] * scale
                assert measured[0] == original[0] and left >= 0 and right <= original[0]
                assert abs((left + right) / 2 - (body[0] + body[2]) / 2 * scale) < 2 * scale
                assert 30 * scale <= -body[3] * scale - bottom <= 49 * scale
                assert top >= -measured[1] - 1e-9
                # Native hat is not stretched to the base's full advance.
                assert abs((right - left) / scale - 154) < 1e-9
            for base in ('E', 'k', 'r', 'p', 'j', 'S'):
                original = metrics(base, size)
                dx, dy, ratio, (w, a, d) = layout.vector_geometry(base, original, size)
                arrow, body = layout.bounds('→'), layout.bounds(base)
                scale = layout.scale(size)
                left, right = dx + arrow[0]*scale*ratio, dx + arrow[2]*scale*ratio
                top, bottom = dy - arrow[3]*scale*ratio, dy - arrow[1]*scale*ratio
                assert left >= -1e-9 and right <= w + 1e-9 and top >= -a - 1e-9
                assert abs(-body[3]*scale - bottom - 48*scale) < 1e-9
                assert ratio == .85 and d == original[2]
            for content in (metrics('x', size), metrics('π', size),
                            (size*2, size*1.7, size*.8), (size*8, size*3, size*2)):
                commands, offset, (w, a, d) = layout.radical_geometry(content, size)
                from fontTools.pens.recordingPen import replayRecording
                from fontTools.pens.boundsPen import BoundsPen
                pen = BoundsPen(None); replayRecording(commands, pen)
                left, top, right, bottom = pen.bounds
                assert left >= 0 and right <= w + 1e-9 and top >= -a - 1e-9 and bottom <= d + 1e-9
                assert w > offset + content[0] and a > content[1]
                # The compact lower hook is never stretched, even for tall fractions.
                assert all(abs(actual-expected)<1e-9 for actual,expected in zip(commands[0][1][0], (167*layout.scale(size)*RADICAL_SCALE, content[2]-min(max(content[2],0),RADICAL_BOTTOM_INSET*size))))
                assert sum(op == 'qCurveTo' for op, _ in commands) > 20
            # Tall radicands must not lengthen any part of the native lower hook.
            from fontTools.pens.recordingPen import RecordingPen
            native = RecordingPen(); layout.glyphs[layout.cmap[ord('√')]].draw(native)
            for height in (.8, 2, 5):
                commands, _, _ = layout.radical_geometry((size*2,size*height,size*.23),size)
                for (op, points), (draw_op, drawn) in zip(native.value[:12], commands[:12]):
                    assert op == draw_op
                    for (nx,ny),(dx,dy) in zip(points,drawn):
                        assert abs(dx-nx*layout.scale(size)*RADICAL_SCALE)<1e-9
                        assert abs(dy-(size*(.23-RADICAL_BOTTOM_INSET)-(ny-131)*layout.scale(size)*RADICAL_SCALE))<1e-9
            for base,lower in (('v','p'),('v','g'),('k','0'),('ω','0'),('Ψ','0'),('y','j'),('φ','n'),('R','n')):
                body,script=metrics(base,size),metrics(lower,size*.65)
                dx,dy,(w,a,d)=layout.subscript_geometry(base,body,lower,script,size)
                bb,sb=layout.bounds(base),layout.bounds(lower);scale=layout.scale(size)
                assert abs(dx+sb[0]*scale*.65-bb[2]*scale-36*scale)<1e-9
                assert dy==.14*size
                if lower != 'g': assert dx<body[0]+1
                assert dx+sb[2]*scale*.65<=w+1e-9
                assert dy-sb[1]*scale*.65<=d+1e-9
                assert dy-sb[3]*scale*.65>=-a-1e-9
            for base in ('Ψ', 'ψ', 'φ', 'x'):
                _, ascent, _ = metrics(base, size)
                rise, top = layout.conjugate_geometry(ascent, size)
                star = layout.bounds('*')
                gap = rise + star[1] * layout.scale(size) - ascent
                assert abs(gap - .06 * size) < 1e-9
                assert top > star[1] * layout.scale(size)
                assert 1.53 < CONJUGATE_SCALE / ORDINARY_SCRIPT_SCALE < 1.54
            for operator in ('∫', '∮'):
                for lower, upper in (('−∞', '∞'), ('0', 'L'), ('a', 'b')):
                    op = metrics(operator, size * 1.35)
                    lo, hi = metrics(lower, size * .55), metrics(upper, size * .55)
                    x, uy, ly, (width, ascent, descent) = layout.integral_geometry(op, lo, hi, size)
                    right = layout.bounds(operator)[2] * layout.scale(size * 1.35)
                    assert x > right and uy < 0 < ly
                    assert width >= x + max(lo[0], hi[0])
                    assert -ascent <= uy - hi[1] and descent >= ly + lo[2]
            from fontTools.pens.recordingPen import replayRecording
            from fontTools.pens.boundsPen import BoundsPen
            for rule_width in (247*layout.scale(size),size,4*size):
                pen=BoundsPen(None); replayRecording(layout.rule_outline(rule_width,size),pen)
                left,top,right,bottom=pen.bounds
                assert abs(left)<1e-9 and abs(right-rule_width)<1e-9
                assert abs(top+bottom)<1e-9 and abs(bottom-top-48*layout.scale(size))<1e-9
                assert layout.numerator_gap(size)>bottom
            minus=layout.math_advance('−',size)
            equals=layout.math_advance('=',size)
            assert abs(minus-equals)<2*layout.scale(size)
            for condition in ('a→0','a→∞','L→∞'):
                op,lo=metrics('lim',size),metrics(condition,size*.65)
                bx,lx,ly,ux,uy,(w,a,d)=layout.limit_geometry(op,lo,(0,0,0),size,condition,None)
                assert abs(bx+op[0]/2-lx-lo[0]/2)<1e-9
                bottom=-min(layout.bounds(c)[1] for c in 'lim')*layout.scale(size)
                top=ly-max(layout.bounds(c)[3] for c in condition)*layout.scale(size*.65)
                assert abs(top-bottom-36*layout.scale(size))<1e-9
                assert w>=lx+lo[0] and a>=op[1]
            for condition in ('n','n=−∞'):
                op,lo,hi=metrics('∑',size*1.35),metrics(condition,size*.55),metrics('∞',size*.55)
                bx,lx,ly,ux,uy,(w,a,d)=layout.summation_geometry(op,lo,hi,size,condition)
                assert abs(bx+op[0]/2-lx-lo[0]/2)<1e-9
                assert uy == -op[1]-3
                top=ly-max(layout.bounds(c)[3] for c in condition)*layout.scale(size*.55)
                bottom=-layout.bounds('∑')[1]*layout.scale(size*1.35)
                assert abs(top-bottom-36*layout.scale(size))<1e-9
                assert ly<op[2]+lo[1]+3 and w>=lx+lo[0]
            axis = layout.fraction_axis(size)
            equals = layout.bounds('=')
            assert abs(axis - (equals[1] + equals[3]) / 2 * layout.scale(size)) < .05
            for top, bottom in (('dx', 'dt'), ('d⟨x⟩', 'dt'), ('Ψ', 'ρ')):
                n, d = metrics(top, size * .85), metrics(bottom, size * .85)
                _, ascent, descent = layout.fraction_metrics(n, d, size)
                assert -axis - layout.numerator_gap(size) - n[2] - n[1] >= -ascent - 1e-9
                assert -axis + 3 + d[1] + d[2] <= descent + 1e-9
    print('PASS: full-size conjugates, right-side integral limits, fraction axis and ink bounds; TTF/WOFF2 unchanged')


if __name__ == '__main__':
    verify()
