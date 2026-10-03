"""Small optical label offsets for the handwritten quantum-note diagrams.

Coordinates are canvas units, Y downward. Curves and axes are not moved.
Offsets are scoped to semantic label roles, never all text with the same word.
"""


def label_offset(role, height):
    if role == 'wave_fixed':
        # Put the top of 15px text below the complete sine-wave envelope.
        return 0, .25 * height + 18 - 35
    return {
        'spectrum_width': (0, -14),
        'packet_wavelength': (0, -20),
        'sinc_zero': (0, 10),
        'optics_angle': (0, -13),
        'spreading_width': (0, 10),
        'beats_envelope_axis': (0, -6),
    }.get(role, (0, 0))


def reserved_figure_height(height, label_bottom):
    """Reserve the actual lowest label ink plus a small following-text gap."""
    return max(height, label_bottom + 4)
