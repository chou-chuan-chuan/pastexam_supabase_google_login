"""Shared geometry for QuanFangwei handwritten note renderers.

Canvas coordinates have Y downward. The caller owns parsing/drawing and passes
measured (width, ascent, descent) tuples. This does not modify font outlines.
Defaults reproduce the approved quantum-notes renderer's 1.26 math scale.
"""
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen, replayRecording


RELATION_CHARACTERS = frozenset('=＝<>＜＞~～≠≡≈≃∼≲≳≤≥≪≫∝∈∉→←↔⇒⇔')
RELATION_SIDE_EM = .18

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
        """Extra left/right advance per relation, in canvas units.

        Apply only to math text runs, not raw accent glyphs or prose. Existing
        adjacent spaces count toward the minimum 0.18 math-em clearance, so
        already spaced relations are not padded twice. Font metrics are unchanged.
        """
        gap = RELATION_SIDE_EM * self.units * self.scale(size)
        result = []
        for index, character in enumerate(text):
            if character not in RELATION_CHARACTERS:
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
        """Extend the native radical's stem and roof, retaining its hook/terminals.

        Return canvas-coordinate outline commands, radicand X offset, and bounds.
        The split coordinates follow the 1.034 native contour: the hook below
        y=278 and roof above y=449 translate rigidly; only the middle stem grows.
        Roof points right of x=242 extend horizontally without scaling thickness.
        No glyph in the font is changed and the radicand remains at full size.
        """
        width, ascent, descent = radicand
        scale = self.scale(size)
        offset, gap, padding = 280 * scale, 48 * scale, 48 * scale
        # The outer hook reaches y=252; start stretching above its full contour.
        # A split at y=208 incorrectly lengthened its left tail on tall roots.
        extra = max(0, (ascent + descent + gap) / scale - (462 - 131))
        roof_right = max(516, (offset + width + padding) / scale)
        def point(pt):
            x, y = pt
            if x > 242:
                x = 242 + (x - 242) * (roof_right - 242) / (516 - 242)
            y += extra * max(0, min(1, (y - 278) / (449 - 278)))
            return x * scale, descent - (y - 131) * scale
        native = RecordingPen()
        self.glyphs[self.cmap[ord('√')]].draw(native)
        outline = [(op, tuple(point(p) if p is not None else None for p in pts))
                   for op, pts in native.value]
        pen = BoundsPen(None)
        replayRecording(outline, pen)
        left, top, right, bottom = pen.bounds
        return outline, offset, (max(offset + width + padding, right),
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
