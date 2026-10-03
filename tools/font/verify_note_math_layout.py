#!/usr/bin/env python3
"""Verify shared note geometry against real font ink and immutable assets."""
from pathlib import Path
import hashlib
from fontTools.ttLib import TTFont
from note_math_layout import NoteMathLayout, CONJUGATE_SCALE, ORDINARY_SCRIPT_SCALE

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
            axis = layout.fraction_axis(size)
            equals = layout.bounds('=')
            assert abs(axis - (equals[1] + equals[3]) / 2 * layout.scale(size)) < .05
            for top, bottom in (('dx', 'dt'), ('d⟨x⟩', 'dt'), ('Ψ', 'ρ')):
                n, d = metrics(top, size * .85), metrics(bottom, size * .85)
                _, ascent, descent = layout.fraction_metrics(n, d, size)
                assert -axis - 3 - n[2] - n[1] >= -ascent - 1e-9
                assert -axis + 3 + d[1] + d[2] <= descent + 1e-9
    print('PASS: full-size conjugates, right-side integral limits, fraction axis and ink bounds; TTF/WOFF2 unchanged')


if __name__ == '__main__':
    verify()
