"""Manually interpreted strokes in the maintainer photographs' pixel coordinates.

The coordinates are reviewable against the unmodified reference images. They
describe pen trajectories, not traced filled bitmap boundaries. One uniform
scale and translation puts each drawing into its glyph cell; no independently
stretched axes or shape regularization is allowed. The existing stroke engine
still supplies the final contours. Raster images are not read during a build.
"""

from dataclasses import dataclass

from japanese.stroke_engine import Stroke


@dataclass(frozen=True)
class PhotoSource:
    reference: str
    crop: tuple[int, int, int, int]
    # Pixel-space pen paths, with the original image's downward-positive y.
    paths: tuple[tuple[tuple[float, float], ...], ...]
    # Longest axis in font units, retaining each photo's aspect ratio.
    span: float = 640.0
    center_y: float = 505.0
    pressure: float = 38.0

    @property
    def pixel_bounds(self):
        points = [point for path in self.paths for point in path]
        return (min(x for x, _ in points), min(y for _, y in points),
                max(x for x, _ in points), max(y for _, y in points))

    @property
    def scale(self):
        x0, y0, x1, y1 = self.pixel_bounds
        return self.span / max(x1 - x0, y1 - y0)

    def to_source(self, x, y):
        x0, y0, x1, y1 = self.pixel_bounds
        return (480.0 + (x - (x0 + x1) / 2) * self.scale,
                self.center_y - (y - (y0 + y1) / 2) * self.scale)

    def strokes(self):
        return tuple(Stroke(tuple(self.to_source(x, y) for x, y in path),
                            self.pressure, self.pressure, self.pressure * 0.94)
                     for path in self.paths)


SHEET_AI_SA_KI = "U+3042-U+3044-U+3055-U+304D-maintainer-handwritten.png"
SHEET_TO_RI = "U+3068-U+308A-maintainer-handwritten.png"

PHOTO_SOURCES = {
    "あ": PhotoSource(SHEET_AI_SA_KI, (75, 55, 255, 260), (
        ((106, 111), (111, 114), (131, 113), (152, 111), (174, 108), (191, 104)),
        ((148, 74), (146, 86), (144, 103), (143, 123), (142, 145),
         (142, 167), (144, 188), (147, 208), (152, 225)),
        ((180, 132), (182, 144), (182, 156), (177, 167), (167, 180),
         (154, 196), (142, 208), (127, 213), (113, 220), (105, 224),
         (99, 221), (95, 214), (93, 203), (96, 190), (104, 178),
         (114, 168), (127, 162), (145, 156), (162, 152), (179, 152),
         (197, 156), (216, 161), (229, 167), (235, 177), (237, 193),
         (235, 207), (228, 219), (217, 228), (203, 237), (191, 245)),
    ), pressure=36.0),
    "い": PhotoSource(SHEET_AI_SA_KI, (315, 100, 495, 253), (
        ((332, 118), (331.5, 139), (332, 163), (334, 184), (338, 199),
         (343, 209), (347, 220), (353, 231), (358, 237), (362, 238), (368, 215)),
        ((447, 123), (454, 127), (462, 138), (468, 155), (474, 173), (478, 187), (481, 199)),
    ), span=650.0, center_y=505.0, pressure=38.0),
    "う": PhotoSource("U+3046-u-maintainer-handwritten.png", (56, 40, 142, 199), (
        ((84, 54), (94, 57), (103, 61), (114, 69)),
        ((69, 109), (79, 106), (88, 103), (98, 99), (108, 98),
         (117, 100), (124, 106), (128, 114), (129, 125), (128, 135),
         (124, 146), (120, 156), (115, 168), (110, 180), (106, 186)),
    ), span=620.0, pressure=33.0),
    "お": PhotoSource("U+304A-o-maintainer-handwritten.png", (45, 28, 184, 180), (
        ((59, 76), (64, 77), (74, 75), (85, 72), (99, 71), (113, 69)),
        ((87, 43), (86.5, 57), (86, 74), (85.5, 94), (85.5, 116),
         (85.5, 137), (85.5, 153), (85, 162), (82, 162), (75, 156),
         (66, 150), (61, 144), (60, 135), (62, 127), (69, 121),
         (80, 115), (93, 110), (107, 106), (119, 104), (131, 105),
         (143, 109), (152, 115), (158, 123), (159, 131), (156, 141),
         (150, 151), (142, 158), (132, 163), (122, 166)),
        ((145, 73), (151, 77), (160, 82), (171, 90)),
    ), span=640.0, pressure=34.0),
    "さ": PhotoSource(SHEET_AI_SA_KI, (115, 325, 254, 525), (
        ((132, 400), (137, 398), (151, 398), (169, 394), (190, 388),
         (210, 382), (228, 378), (239, 374)),
        ((169, 344), (173, 356), (181, 370), (191, 385), (202, 403),
         (212, 420), (226, 435), (238, 447)),
        ((144, 451), (143, 465), (146, 479), (155, 489), (168, 497),
         (184, 504), (201, 509), (220, 511)),
    ), pressure=36.0),
    "き": PhotoSource(SHEET_AI_SA_KI, (360, 323, 502, 527), (
        ((378, 389), (382, 386), (398, 383), (415, 378), (432, 372),
         (448, 369), (459, 366), (465, 362)),
        ((402, 434), (416, 428), (433, 422), (452, 417), (471, 413), (486, 409)),
        ((413, 342), (417, 355), (422, 367), (430, 383), (439, 400),
         (448, 418), (456, 436), (463, 449), (469, 456)),
        ((377, 470), (379, 478), (382, 489), (389, 498), (401, 502),
         (417, 507), (434, 511), (451, 513), (468, 513), (477, 512)),
    ), pressure=37.0),
    "と": PhotoSource(SHEET_TO_RI, (50, 46, 167, 184), (
        ((65, 62), (75, 74), (86, 88), (98, 104)),
        ((150, 68), (139, 77), (126, 86), (111, 96), (96, 106),
         (83, 117), (75, 128), (71, 141), (72, 153), (78, 159),
         (92, 163), (109, 166), (126, 168), (140, 169), (153, 167)),
    ), span=540.0, center_y=475.0, pressure=40.0),
    "り": PhotoSource(SHEET_TO_RI, (71, 263, 158, 439), (
        ((89, 277), (87, 292), (85, 311), (84, 331), (84, 346),
         (87, 358), (90, 346), (95, 339)),
        ((139, 280), (140, 295), (144, 315), (145, 336), (145, 354),
         (141, 374), (137, 394), (132, 407), (124, 419), (118, 426)),
    ), pressure=38.0),
}
