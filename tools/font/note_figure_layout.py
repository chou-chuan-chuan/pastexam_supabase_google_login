"""Small optical label and annotation offsets for the handwritten quantum-note diagrams.

Coordinates are canvas units, Y downward. Label offsets preserve existing curves.
The Gaussian comparison explicitly lays out a new paired diagram.
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


def spectrum_width_arrow_y(axis_y, figure_id):
    """Lift the Fourier spectrum (W05) width arrow; keep other diagrams fixed."""
    return axis_y - (25 if figure_id == 'W05' else 15)


def spectrum_note_frame(x, y, width):
    """Upper-right definition above the paired Gaussian diagrams."""
    return x + .53 * width, y, .46 * width, 70


def gaussian_comparison_panels(x, y, width):
    """Matched peak heights with the x-space density to the left of k space.

    Horizontal scales are illustrative (alpha=1); the x standard deviation is
    twice the k standard deviation. Arrow endpoints are the exact 1/e points.
    """
    panels=[]
    for offset,sigma in ((0,.16),(.53,.08)):
        left=x+offset*width+18
        span=.46*width-42
        baseline=y+205
        peak_height=95
        center=left+span/2
        half_width=2**.5*sigma*span
        panels.append(dict(left=left,span=span,baseline=baseline,height=peak_height,
                           center=center,sigma=sigma,
                           arrow=(center-half_width,baseline-peak_height/2.718281828459045,
                                  center+half_width)))
    return panels
