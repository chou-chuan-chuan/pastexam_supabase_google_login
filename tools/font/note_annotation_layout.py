"""Wrap English annotations with indivisible $math$ spans and native metrics.

The renderer supplies text/math measurers returning (width, ascent, descent).
Adjacent punctuation stays attached to its math span. All output uses a common
baseline for each line; tall fractions increase that line's measured height.
"""
import re


def annotation_lines(source, max_width, text_measure, math_measure, space_width):
    if source.count('$') % 2:
        raise ValueError('Unclosed annotation math span')
    groups, group = [], []
    for index, part in enumerate(source.split('$')):
        if index % 2:
            if part:
                group.append(('math', part, math_measure(part)))
        else:
            for token in re.findall(r'\s+|\S+', part):
                if token.isspace():
                    if group:
                        groups.append(group)
                        group = []
                else:
                    group.append(('text', token, text_measure(token)))
    if group:
        groups.append(group)
    lines, line = [], []
    advance = ascent = descent = 0
    for group in groups:
        group_width = sum(item[2][0] for item in group)
        if group_width > max_width:
            raise ValueError(f'Annotation span too wide: {group!r}')
        gap = space_width if line else 0
        if line and advance + gap + group_width > max_width:
            lines.append((line, advance, ascent, descent))
            line = []
            advance = ascent = descent = gap = 0
        advance += gap
        for kind, content, (width, top, bottom) in group:
            line.append((kind, content, advance, width, top, bottom))
            advance += width
            ascent, descent = max(ascent, top), max(descent, bottom)
    if line:
        lines.append((line, advance, ascent, descent))
    return lines
