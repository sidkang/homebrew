# /// script
# requires-python = ">=3.12"
# dependencies = ["fonttools==4.59.0", "py7zr==1.0.0"]
# ///

from __future__ import annotations

import json
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTCollection

from build import (
    FACES,
    FAMILY,
    IOSEVKA_RANGES,
    NERD_RANGES,
    POSTSCRIPT_FAMILY,
    SOURCES,
    SPINNER,
    VERSION,
    codepoints,
    italic,
    mapping,
    select_faces,
    unicode_tables,
)

REQUIRED_TABLES = {"OS/2", "cmap", "glyf", "head", "hhea", "hmtx", "loca", "maxp", "name", "post"}


def draw(font, glyph_name: str):
    glyph_set = font.getGlyphSet()
    pen = DecomposingRecordingPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    return pen.value


def coordinates(ops) -> list[tuple[float, float]]:
    points = []
    for _op, curve in ops:
        points.extend(point for point in curve if point is not None)
    return points


def same_outline(left, right) -> bool:
    left_points = coordinates(left)
    right_points = coordinates(right)
    if not left_points and not right_points:
        return True
    if not left_points or not right_points:
        return False
    left_box = (
        min(point[0] for point in left_points),
        min(point[1] for point in left_points),
        max(point[0] for point in left_points),
        max(point[1] for point in left_points),
    )
    right_box = (
        min(point[0] for point in right_points),
        min(point[1] for point in right_points),
        max(point[0] for point in right_points),
        max(point[1] for point in right_points),
    )
    return all(abs(left_box[index] - right_box[index]) <= 1 for index in range(4))


def advance(font, glyph_name: str) -> int:
    return font["hmtx"][glyph_name][0]


def verify(repo_root: Path) -> None:
    output = repo_root / "dist" / "term-slab-sc-ss17"
    cache = output / "cache"
    collection_path = output / f"{POSTSCRIPT_FAMILY}.ttc"
    info = json.loads((output / "BUILD-INFO.json").read_text())
    if info["family"] != FAMILY or info["version"] != VERSION:
        raise SystemExit("BUILD-INFO does not match this module")
    collection = TTCollection(str(collection_path))
    if len(collection.fonts) != len(FACES):
        raise SystemExit(f"expected {len(FACES)} faces, found {len(collection.fonts)}")
    sarasa = select_faces(cache / "sarasa", SOURCES["sarasa"]["family"])
    iosevka = select_faces(cache / "iosevka", SOURCES["iosevka"]["family"])
    nerd = select_faces(
        cache / "nerd",
        SOURCES["nerd"]["family"],
        SOURCES["nerd"]["family_aliases"],
        marker="NerdFontMono",
    )
    iosevka_points = codepoints(IOSEVKA_RANGES)
    nerd_points = codepoints(NERD_RANGES) - set(SPINNER)
    seen = set()
    for font in collection.fonts:
        if FAMILY not in font["name"].getDebugName(1):
            raise SystemExit(f"unexpected family {font['name'].getDebugName(1)}")
        missing = REQUIRED_TABLES - set(font.keys())
        if missing:
            raise SystemExit(f"missing tables: {sorted(missing)}")
        key = (font["OS/2"].usWeightClass, italic(font))
        if key in seen:
            raise SystemExit(f"duplicate face {key}")
        seen.add(key)
        produced = {}
        for table in unicode_tables(font):
            produced.update(table.cmap)
        for codepoint in SPINNER:
            if codepoint in produced:
                raise SystemExit(f"U+{codepoint:04X} is present in {key}")
        check_donor(font, produced, iosevka[key]["font"], sarasa[key]["font"], iosevka_points, "Iosevka")
        check_donor(font, produced, nerd[key]["font"], sarasa[key]["font"], nerd_points, "Nerd")
        cjk = 0x4E00
        if mapping(font).get(cjk) != mapping(sarasa[key]["font"]).get(cjk):
            raise SystemExit("CJK mapping changed")
        if advance(font, produced[cjk]) != advance(sarasa[key]["font"], mapping(sarasa[key]["font"])[cjk]):
            raise SystemExit("CJK advance changed")
    if seen != {(weight, is_italic) for weight, is_italic, _, _ in FACES}:
        raise SystemExit(f"face set is {seen}")
    print(f"verified {collection_path}")


def check_donor(destination, produced, donor, sarasa, points: set[int], label: str) -> None:
    donor_map = mapping(donor)
    sarasa_map = mapping(sarasa)
    for codepoint in points:
        if codepoint in donor_map:
            glyph_name = produced.get(codepoint)
            if glyph_name is None:
                raise SystemExit(f"{label} U+{codepoint:04X} was not copied")
            if not same_outline(draw(destination, glyph_name), draw(donor, donor_map[codepoint])):
                raise SystemExit(f"{label} U+{codepoint:04X} outline differs")
            if advance(destination, glyph_name) != advance(donor, donor_map[codepoint]):
                raise SystemExit(f"{label} U+{codepoint:04X} advance differs")
            continue
        if produced.get(codepoint) != sarasa_map.get(codepoint):
            raise SystemExit(f"{label} left U+{codepoint:04X} without the Sarasa fallback")


if __name__ == "__main__":
    module = Path(__file__).resolve().parent
    verify(module.parents[1])
