"""Shared geometry for QuanFangwei handwritten note renderers.

Canvas coordinates have Y downward. The caller owns parsing/drawing and passes
measured (width, ascent, descent) tuples. This does not modify font outlines.
Defaults reproduce the approved quantum-notes renderer's 1.26 math scale.
"""
from fontTools.pens.boundsPen import BoundsPen


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

    def fraction_axis(self, size):
        return self.font['MATH'].table.MathConstants.AxisHeight.Value * (size * self.math_scale) / self.units

    def fraction_metrics(self, numerator, denominator, size):
        axis = self.fraction_axis(size)
        return (max(numerator[0], denominator[0]) + 8,
                axis + 3 + numerator[1] + numerator[2],
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
