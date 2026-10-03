"""Shared geometry for QuanFangwei handwritten note renderers.

Canvas coordinates have Y downward. The caller owns parsing/drawing and passes
measured (width, ascent, descent) tuples. This does not modify font outlines.
Defaults reproduce the approved quantum-notes renderer's 1.26 math scale.
"""
from math import hypot
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen, replayRecording


RELATION_CHARACTERS = frozenset('=＝<>＜＞~～≠≡≈≃∼≲≳≤≥≪≫∝∈∉→←↔⇒⇔')
RELATION_SIDE_EM = .18
BINARY_SIDE_EM = .14
PARENTHESIS_CHARACTERS = frozenset('()（）')
PARENTHESIS_SIDE_EM = .06
RADICAL_DIAGONAL_SLOPE = .28
RADICAL_BOTTOM_INSET = .16

CONJUGATE_SCALE = 1.0
ORDINARY_SCRIPT_SCALE = 0.65


class NoteMathLayout:
    def __init__(self, font, math_scale=1.26):
        self.font = font
        self.math_scale = math_scale
        self.units = font['head'].unitsPerEm
        self.glyphs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self.ink_extents = {}

    def scale(self, size):
        return size * self.math_scale / self.units

    def bounds(self, character):
        if character not in self.ink_extents:
            pen = BoundsPen(self.glyphs)
            self.glyphs[self.cmap[ord(character)]].draw(pen)
            self.ink_extents[character] = pen.bounds
        return self.ink_extents[character]

    def text_metrics(self, text, size, advance):
        # Preserve established leading, but never underestimate taller ink.
        ascent, descent = .8 * size, .23 * size
        for character in text:
            bounds = self.bounds(character)
            if bounds:
                ascent = max(ascent, bounds[3] * self.scale(size))
                descent = max(descent, -bounds[1] * self.scale(size))
        return advance, ascent, descent

    def relation_spacing(self, text, size):
        """Extra left/right advance per relation or parenthesis, in canvas units.

        Apply only to math text runs, not raw accent glyphs or prose. Existing
        adjacent spaces count toward the minimum clearance (0.18 math-em for
        relations, 0.06 for parentheses), so
        already spaced relations are not padded twice. Font metrics are unchanged.
        """
        result = []
        for index, character in enumerate(text):
            if character in PARENTHESIS_CHARACTERS:
                gap = PARENTHESIS_SIDE_EM * self.units * self.scale(size)
            elif character in RELATION_CHARACTERS:
                gap = RELATION_SIDE_EM * self.units * self.scale(size)
            else:
                result.append((0, 0))
                continue
            sides = []
            for step in (-1, 1):
                available, cursor = 0, index + step
                while 0 <= cursor < len(text) and text[cursor].isspace():
                    available += self.font['hmtx'][self.cmap[ord(text[cursor])]][0] * self.scale(size)
                    cursor += step
                sides.append(max(0, gap - available))
            result.append(tuple(sides))
        return result

    @staticmethod
    def is_binary_sign(character, before, after):
        """Classify +/− at a parsed expression boundary, not inside prose.

        Callers represent a preceding compound operand by a closing parenthesis.
        Expression starts, opening delimiters and other operators take unary signs.
        """
        before, after = before.rstrip(), after.lstrip()
        return (character in '+−' and bool(before) and bool(after)
                and before[-1] not in '([{⟨,+−±∓×÷*/:;|' + ''.join(RELATION_CHARACTERS)
                and after[0] not in ')]}⟩,;=<>')

    def binary_spacing(self, size, before='', after=''):
        """Minimum side spacing for an already classified binary + or −.

        Count existing boundary spaces toward the 0.14 math-em minimum.
        Use the same offsets in both width measurement and drawing.
        """
        gap = BINARY_SIDE_EM * self.units * self.scale(size)
        sides = []
        for boundary in (reversed(before), iter(after)):
            occupied = 0
            for char in boundary:
                if not char.isspace():
                    break
                occupied += self.math_advance(char, size)
            sides.append(max(0, gap - occupied))
        return tuple(sides)

    def subscript_geometry(self, base, base_metrics, lower, lower_metrics, size):
        """Bring a lower script close to the base, keeping 65% script size.

        Simple bases use their actual right ink edge and the lower script's
        first left bearing. Compound bases use their measured advance. Keep
        a positive 36-unit gap, including for descenders such as y/p/φ.
        Superscripts remain on their existing independent placement path.
        """
        width, ascent, descent = base_metrics
        scale = self.scale(size)
        body = self.bounds(base) if isinstance(base, str) and len(base) == 1 else None
        right = body[2] * scale if body else width
        first = self.bounds(lower[0]) if isinstance(lower, str) and lower else None
        left = first[0] * scale * ORDINARY_SCRIPT_SCALE if first else 0
        dx, dy = right + 36 * scale - left, .14 * size
        return dx, dy, (max(width, dx + lower_metrics[0]),
                        max(ascent, lower_metrics[1] - dy),
                        max(descent, lower_metrics[2] + dy))

    def limit_geometry(self, base, lower, upper, size, lower_text=None, upper_text=None):
        """Center lim conditions below/above the complete operator word.

        Plain condition runs use native vertical ink bounds for a compact gap;
        compound conditions fall back to their measured enclosing metrics.
        Return base X, lower X/Y, upper X/Y, and the complete measured box.
        """
        width = max(base[0], lower[0], upper[0])
        scale, gap = self.scale(size), 36 * self.scale(size)
        body_bottom = -min(self.bounds(c)[1] for c in 'lim') * scale
        body_top = max(self.bounds(c)[3] for c in 'lim') * scale
        def ink(text, measured):
            bounds = [self.bounds(c) for c in text] if isinstance(text,str) else []
            bounds = [b for b in bounds if b]
            if bounds:
                return max(b[3] for b in bounds)*scale*.65, -min(b[1] for b in bounds)*scale*.65
            return measured[1], measured[2]
        la, ld = ink(lower_text, lower)
        ua, ud = ink(upper_text, upper)
        ly = body_bottom + gap + la
        uy = -body_top - gap - ud
        return ((width-base[0])/2, (width-lower[0])/2, ly,
                (width-upper[0])/2, uy,
                (width + .12*size, max(base[1],ua-uy if upper_text is not None else 0),
                 max(base[2],ld+ly if lower_text is not None else 0)))

    def summation_geometry(self, base, lower, upper, size, lower_text=None):
        """Lift the centered lower sum limit; preserve the upper limit policy."""
        width = max(base[0], lower[0], upper[0]) + 5
        scale = self.scale(size)
        body_bottom = -self.bounds('∑')[1] * scale * 1.35
        bounds = [self.bounds(c) for c in lower_text] if isinstance(lower_text,str) else []
        bounds = [b for b in bounds if b]
        lower_ascent = max(b[3] for b in bounds)*scale*.55 if bounds else lower[1]
        lower_descent = -min(b[1] for b in bounds)*scale*.55 if bounds else lower[2]
        ly = body_bottom + 36 * scale + lower_ascent
        uy = -base[1] - 3
        return ((width-base[0])/2, (width-lower[0])/2, ly,
                (width-upper[0])/2, uy,
                (width, max(base[1],upper[1]-uy), max(base[2],lower_descent+ly)))

    def conjugate_geometry(self, base_ascent, size):
        # * is already a small raised drawing. Render it at full math size.
        bounds = self.bounds('*')
        bottom, top = bounds[1] * self.scale(size), bounds[3] * self.scale(size)
        return base_ascent + size * .06 - bottom, top

    def hat_geometry(self, base, base_metrics, size):
        """Place native U+0302 ink; return dx, dy and unchanged-advance metrics.

        Use the font's scoped operator-hat lookup when available. Other bases
        use MATH accent centers and the same 48-unit native ink clearance.
        This is a narrow hat adapter, not a general OpenType shaping engine.
        """
        width, ascent, descent = base_metrics
        mark = self.cmap[0x302]
        mb = self.bounds('\u0302')
        name = self.cmap.get(ord(base)) if isinstance(base, str) and len(base) == 1 else None
        offset = None
        if name and 'GPOS' in self.font:
            for lookup in reversed(self.font['GPOS'].table.LookupList.Lookup):
                if lookup.LookupType != 4:
                    continue
                for sub in lookup.SubTable:
                    if sub.MarkCoverage.glyphs != [mark] or name not in sub.BaseCoverage.glyphs:
                        continue
                    record = sub.MarkArray.MarkRecord[0]
                    anchor = sub.BaseArray.BaseRecord[sub.BaseCoverage.glyphs.index(name)].BaseAnchor[record.Class]
                    if anchor is not None:
                        offset = (anchor.XCoordinate - record.MarkAnchor.XCoordinate,
                                  anchor.YCoordinate - record.MarkAnchor.YCoordinate)
                        break
                if offset is not None:
                    break
        if offset is None:
            attachments = self.font['MATH'].table.MathGlyphInfo.MathTopAccentAttachment
            centers = dict(zip(attachments.TopAccentCoverage.glyphs,
                               (value.Value for value in attachments.TopAccentAttachment)))
            center = centers.get(name, width / self.scale(size) / 2)
            mark_center = centers.get(mark, (mb[0] + mb[2]) / 2)
            top = self.bounds(base)[3] if name else ascent / self.scale(size)
            dy = round(min(top + 48 - mb[1], self.font['OS/2'].sTypoAscender - 4 - mb[3]))
            offset = (center - mark_center, dy)
        dx, rise = offset
        scale = self.scale(size)
        return dx * scale, -rise * scale, (width, max(ascent, (mb[3] + rise) * scale), descent)

    def vector_geometry(self, base, base_metrics, size):
        """Native right-arrow accent, with unchanged outline and 48-unit gap.

        This explicit renderer adapter does not add U+20D7 to the font cmap.
        The 85% arrow matches the native thin stroke, without a fixed-pixel head.
        """
        width, ascent, descent = base_metrics
        scale, ratio = self.scale(size), .85
        arrow = self.bounds('→')
        single = isinstance(base, str) and len(base) == 1
        body = self.bounds(base) if single else None
        center = (body[0] + body[2]) * scale / 2 if body else width / 2
        ink_width = (arrow[2] - arrow[0]) * scale * ratio
        left = max(0, min(center - ink_width / 2, width - ink_width))
        dx = left - arrow[0] * scale * ratio
        base_top = body[3] * scale if body else ascent
        dy = -base_top - 48 * scale + arrow[1] * scale * ratio
        top = dy - arrow[3] * scale * ratio
        return dx, dy, ratio, (max(width, left + ink_width), max(ascent, -top), descent)

    def radical_geometry(self, radicand, size):
        """Reference-inspired short hook, rising diagonal and horizontal roof.

        This is a renderer outline, not a replacement font glyph. Stroke width
        follows the handwritten math scale; the radicand stays at full size.
        The short entry is capped independently of content height, while the
        diagonal keeps a consistent slope even around a tall fraction.
        """
        width, ascent, descent = radicand
        radius = 18 * self.scale(size)
        bottom = descent - min(max(descent, 0), RADICAL_BOTTOM_INSET * size)
        top = -ascent - .05 * size - radius
        height = bottom - top
        hook_height = min(.26 * height, .38 * size)
        valley_x = radius + .18 * size
        roof_x = valley_x + RADICAL_DIAGONAL_SLOPE * height
        offset = roof_x + .12 * size + radius
        points = [(radius, bottom-hook_height), (valley_x, bottom),
                  (roof_x, top), (offset+width+.07*size, top)]
        directions, normals = [], []
        for a, b in zip(points, points[1:]):
            dx, dy = b[0]-a[0], b[1]-a[1]
            length = hypot(dx, dy)
            directions.append((dx/length, dy/length))
            normals.append((-dy/length, dx/length))
        def shift(p, vector, amount=radius):
            return (p[0]+vector[0]*amount, p[1]+vector[1]*amount)
        def corner(index, side):
            a, b = normals[index-1], normals[index]
            factor = side*radius/(1+a[0]*b[0]+a[1]*b[1])
            return shift(points[index], (a[0]+b[0], a[1]+b[1]), factor)
        # A rounded outer valley avoids the long spike of an acute miter join.
        turn = tuple(normals[0][i]+normals[1][i] for i in (0,1))
        turn_length = hypot(*turn)
        valley_control = shift(points[1],turn,1.8*radius/turn_length)
        outline = [
            ('moveTo',(shift(points[0],normals[0]),)),
            ('lineTo',(shift(points[1],normals[0]),)),
            ('qCurveTo',(valley_control,shift(points[1],normals[1]))),
            ('lineTo',(corner(2,1),)),
            ('lineTo',(shift(points[3],normals[2]),)),
            ('qCurveTo',(shift(points[3],directions[2],2*radius),shift(points[3],normals[2],-radius))),
            ('lineTo',(corner(2,-1),)),
            ('lineTo',(corner(1,-1),)),
            ('lineTo',(shift(points[0],normals[0],-radius),)),
            ('qCurveTo',(shift(points[0],directions[0],-2*radius),shift(points[0],normals[0]))),
            ('closePath',()),
        ]
        pen = BoundsPen(None)
        replayRecording(outline, pen)
        left, top, right, bottom = pen.bounds
        return outline, offset, (max(offset+width, right),
                                 max(ascent, -top), max(descent, bottom))

    def math_advance(self, character, size):
        advance = self.font['hmtx'][self.cmap[ord(character)]][0]
        if character == '−':
            # Match the 247-unit native =/- ink length and +/= advance family.
            advance -= 436 - 247
        return advance * self.scale(size)

    def rule_outline(self, width, size):
        """Native minus stroke centered at canvas y=0, with fixed end caps.

        Only the middle section changes length. Keep native thickness, subtle
        slope and terminal shapes for both short minuses and fraction rules.
        """
        scale = self.scale(size)
        native = RecordingPen()
        self.glyphs[self.cmap[ord('−')]].draw(native)
        target = width / scale
        if target < 104:
            raise ValueError('Rule too short to preserve native terminals')
        def point(pt):
            x, y = pt
            if x <= 99:
                x -= 45
            elif x >= 431:
                x = target - (481 - x)
            else:
                x = 54 + (x - 99) * (target - 104) / (431 - 99)
            return x * scale, -(y - 328) * scale
        return [(op, tuple(point(p) for p in pts)) for op, pts in native.value]

    def fraction_axis(self, size):
        return self.font['MATH'].table.MathConstants.AxisHeight.Value * (size * self.math_scale) / self.units

    @staticmethod
    def numerator_gap(size):
        # Small optical gap; ordinary glyph metrics already reserve descender air.
        return .06 * size

    def fraction_metrics(self, numerator, denominator, size):
        axis = self.fraction_axis(size)
        return (max(numerator[0], denominator[0]) + size * .20,
                axis + self.numerator_gap(size) + numerator[1] + numerator[2],
                max(0, 3 + denominator[1] + denominator[2] - axis))

    @staticmethod
    def integral_geometry(base, lower, upper, size):
        """Apply only to ∫/∮; callers keep sum limits centered and stacked."""
        width, ascent, descent = base
        x = width + size * .08
        upper_y, lower_y = -size * .72, size * .34
        return (x, upper_y, lower_y,
                (x + max(lower[0], upper[0]) + size * .08,
                 max(ascent, upper[1] - upper_y),
                 max(descent, lower[2] + lower_y)))
