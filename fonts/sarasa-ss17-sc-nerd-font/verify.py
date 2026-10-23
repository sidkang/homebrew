# /// script
# requires-python = ">=3.12"
# dependencies = ["fonttools==4.59.0", "py7zr==1.0.0", "uharfbuzz==0.56.4", "opentype-sanitizer==9.2.0"]
# ///

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path

import ots
import uharfbuzz as hb
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTCollection

from build import (
    ARCHIVE_PREFIX,
    FACES,
    FAMILIES,
    IOSEVKA_RANGES,
    LAYOUT_TABLES,
    MODULE,
    NERD_RANGES,
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
IDENTITY_NAME_IDS = (1, 2, 3, 4, 6, 16, 17)
CJK_RANGES = (
    range(0x3000, 0x3040),
    range(0x3400, 0x4DC0),
    range(0x4E00, 0xA000),
    range(0xFF00, 0xFFF0),
)
CJK_SAMPLE_STEP = 17
# Iosevka default calt ligatures. Shaped output must match donor glyphs exactly.
LIGATURE_SAMPLES = ("->", "=>", "!=", "===", "<=", ">=", "<!--", "|>", "<|>", "&&", "||", "::", "/*", "www")
MIXED_SAMPLE = "a->b != c 中文，测试。"


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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shaper(path: str, index: int | None):
    face = hb.Face(hb.Blob.from_file_path(path), index or 0)
    return hb.Font(face)


def shape(font, text: str) -> list[tuple[int, int, int, int]]:
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer)
    return [
        (info.codepoint, position.x_advance, position.x_offset, position.y_offset)
        for info, position in zip(buffer.glyph_infos, buffer.glyph_positions)
    ]


def named(font, shaped) -> list[tuple[str, int, int, int]]:
    order = font.getGlyphOrder()
    return [(order[glyph], x_advance, x_offset, y_offset) for glyph, x_advance, x_offset, y_offset in shaped]


def verify(repo_root: Path) -> None:
    output = repo_root / "dist" / MODULE
    cache = output / "cache"
    version = os.environ.get("FONT_VERSION", VERSION)
    info = json.loads((output / "BUILD-INFO.json").read_text())
    if info["version"] != version:
        raise SystemExit(f"BUILD-INFO version is {info['version']}, expected {version}")
    if [item["family"] for item in info["families"]] != [family["family"] for family in FAMILIES]:
        raise SystemExit("BUILD-INFO families do not match this module")
    nerd = select_faces(cache / "nerd", SOURCES["nerd"])
    postscript_names: set[str] = set()
    for family in FAMILIES:
        verify_family(output, cache, family, nerd, postscript_names)
    verify_archive(repo_root, output, version)


def verify_family(output: Path, cache: Path, family, nerd, postscript_names: set[str]) -> None:
    collection_path = output / f"{family['postscript']}.ttc"
    result = ots.sanitize(str(collection_path), os.devnull, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"OTS rejected {collection_path.name}: {result.stderr.strip() or result.stdout.strip()}")
    collection = TTCollection(str(collection_path))
    if len(collection.fonts) != len(FACES):
        raise SystemExit(f"{collection_path.name}: expected {len(FACES)} faces, found {len(collection.fonts)}")
    sarasa = select_faces(cache / family["sarasa"], SOURCES[family["sarasa"]])
    iosevka = select_faces(cache / family["iosevka"], SOURCES[family["iosevka"]])
    iosevka_points = codepoints(IOSEVKA_RANGES)
    nerd_points = codepoints(NERD_RANGES) - set(SPINNER)
    styles = {style: (weight, is_italic, postscript_style) for weight, is_italic, style, postscript_style in FACES}
    seen = set()
    for index, font in enumerate(collection.fonts):
        style = font["name"].getName(2, 3, 1, 0x409).toUnicode()
        if style not in styles:
            raise SystemExit(f"{collection_path.name}: unexpected style {style}")
        weight, is_italic, postscript_style = styles[style]
        key = (font["OS/2"].usWeightClass, italic(font))
        if key != (weight, is_italic):
            raise SystemExit(f"{family['family']} {style} has weight/italic {key}")
        if key in seen:
            raise SystemExit(f"duplicate face {key}")
        seen.add(key)
        label = f"{family['family']} {style}"
        check_names(font, family, style, postscript_style, label)
        postscript = font["name"].getName(6, 3, 1, 0x409).toUnicode()
        if postscript in postscript_names:
            raise SystemExit(f"Duplicate PostScript name: {postscript}")
        postscript_names.add(postscript)
        missing = REQUIRED_TABLES - set(font.keys())
        if missing:
            raise SystemExit(f"{label}: missing tables {sorted(missing)}")
        for tag in ("vmtx", "vhea", "VORG"):
            if tag in font:
                raise SystemExit(f"{label}: {tag} should have been removed")
        produced = {}
        for table in unicode_tables(font):
            produced.update(table.cmap)
        for codepoint in SPINNER:
            if codepoint in produced:
                raise SystemExit(f"{label}: U+{codepoint:04X} is present")
        sarasa_font = sarasa[key]["font"]
        iosevka_font = iosevka[key]["font"]
        nerd_font = nerd[key]["font"]
        replaced = check_donor(font, produced, iosevka_font, sarasa_font, iosevka_points, f"{label} Iosevka")
        replaced |= check_donor(font, produced, nerd_font, sarasa_font, nerd_points, f"{label} Nerd")
        check_sarasa(font, produced, sarasa_font, replaced, label)
        if family["layout"]:
            check_layout(collection_path, index, font, iosevka[key], label)
        else:
            check_no_layout(collection_path, index, font, label)
        print(f"verified {label}")
    if seen != {(weight, is_italic) for weight, is_italic, _, _ in FACES}:
        raise SystemExit(f"{collection_path.name}: face set is {seen}")
    print(f"verified {collection_path}")


def check_names(font, family, style: str, postscript_style: str, label: str) -> None:
    expected = {
        1: family["family"],
        2: style,
        3: f"{os.environ.get('FONT_VERSION', VERSION)};{family['postscript']};{postscript_style}",
        4: f"{family['family']} {style}",
        6: f"{family['postscript']}-{postscript_style}",
        16: family["family"],
        17: style,
    }
    for name_id, value in expected.items():
        if font["name"].getName(name_id, 3, 1, 0x409) is None:
            raise SystemExit(f"{label}: English name ID {name_id} is missing")
    # All name records, including localized entries, must match the expected family identity.
    for record in font["name"].names:
        if record.nameID in IDENTITY_NAME_IDS and record.toUnicode() != expected[record.nameID]:
            raise SystemExit(
                f"{label}: name ID {record.nameID} ({record.platformID}/{record.langID:#x}) is {record.toUnicode()!r}"
            )


def check_donor(destination, produced, donor, sarasa, points: set[int], label: str) -> set[int]:
    donor_map = mapping(donor)
    sarasa_map = mapping(sarasa)
    replaced = set()
    for codepoint in points:
        if codepoint in donor_map:
            glyph_name = produced.get(codepoint)
            if glyph_name is None:
                raise SystemExit(f"{label} U+{codepoint:04X} was not copied")
            if not same_outline(draw(destination, glyph_name), draw(donor, donor_map[codepoint])):
                raise SystemExit(f"{label} U+{codepoint:04X} outline differs")
            if advance(destination, glyph_name) != advance(donor, donor_map[codepoint]):
                raise SystemExit(f"{label} U+{codepoint:04X} advance differs")
            replaced.add(codepoint)
            continue
        if codepoint in SPINNER:
            continue
        if produced.get(codepoint) != sarasa_map.get(codepoint):
            raise SystemExit(f"{label}: missing Sarasa fallback for U+{codepoint:04X}")
    return replaced


def check_sarasa(font, produced, sarasa, replaced: set[int], label: str) -> None:
    sarasa_map = mapping(sarasa)
    kept = set(sarasa_map) - replaced - set(SPINNER)
    expected = kept | replaced
    if set(produced) != expected:
        extra = sorted(set(produced) - expected)[:5]
        lost = sorted(expected - set(produced))[:5]
        raise SystemExit(f"{label}: cmap differs; extra {extra}, lost {lost}")
    for codepoint in kept:
        if produced[codepoint] != sarasa_map[codepoint]:
            raise SystemExit(f"{label}: U+{codepoint:04X} no longer maps to the Sarasa glyph")
    cjk = sorted(codepoint for codepoint in codepoints(CJK_RANGES) if codepoint in kept)
    if not cjk:
        raise SystemExit(f"{label}: no CJK characters")
    for codepoint in cjk[::CJK_SAMPLE_STEP] + [0x4E00, 0x3001, 0x3002, 0xFF0C]:
        name = sarasa_map[codepoint]
        if advance(font, name) != advance(sarasa, name):
            raise SystemExit(f"{label}: CJK U+{codepoint:04X} advance changed")
        # Outline drawing includes lsb - xMin offset, detecting position shifts.
        if draw(font, name) != draw(sarasa, name):
            raise SystemExit(f"{label}: CJK U+{codepoint:04X} outline changed")


def check_layout(collection_path: Path, index: int, font, donor_face, label: str) -> None:
    for tag in ("GSUB", "GDEF"):
        if tag not in font:
            raise SystemExit(f"{label}: {tag} is missing")
    features = {record.FeatureTag for record in font["GSUB"].table.FeatureList.FeatureRecord}
    if "calt" not in features:
        raise SystemExit(f"{label}: GSUB has no calt")
    donor = donor_face["font"]
    produced_shaper = shaper(str(collection_path), index)
    donor_shaper = shaper(str(donor_face["path"]), donor_face["index"])
    donor_map = mapping(donor)
    ligated = 0
    for text in LIGATURE_SAMPLES:
        # Sarasa omits glyph names; compare glyphs by outline geometry and advance position.
        expected = named(donor, shape(donor_shaper, text))
        actual = named(font, shape(produced_shaper, text))
        same = len(actual) == len(expected) and all(
            produced[1:] == wanted[1:] and draw(font, produced[0]) == draw(donor, wanted[0])
            for produced, wanted in zip(actual, expected)
        )
        if not same:
            raise SystemExit(f"{label}: shaping {text!r} gives {actual}, donor gives {expected}")
        if [name for name, *_ in expected] != [donor_map[ord(char)] for char in text]:
            ligated += 1
    if ligated < len(LIGATURE_SAMPLES) // 2:
        raise SystemExit(f"{label}: only {ligated} of {len(LIGATURE_SAMPLES)} ligature samples substituted")
    mixed = named(font, shape(produced_shaper, MIXED_SAMPLE))
    cmap = mapping(font)
    for char, (name, *_rest) in zip(reversed(MIXED_SAMPLE), reversed(mixed)):
        if ord(char) < 0x3000:
            break
        if name != cmap[ord(char)]:
            raise SystemExit(f"{label}: unexpected shaping substitution for CJK character {char!r} ({name})")


def check_no_layout(collection_path: Path, index: int, font, label: str) -> None:
    present = [tag for tag in LAYOUT_TABLES if tag in font]
    if present:
        raise SystemExit(f"{label}: unexpected layout tables {present}")
    cmap = mapping(font)
    actual = [name for name, *_ in named(font, shape(shaper(str(collection_path), index), "->"))]
    if actual != [cmap[ord("-")], cmap[ord(">")]]:
        raise SystemExit(f"{label}: '->' shaped to {actual}")


def verify_archive(repo_root: Path, output: Path, version: str) -> None:
    archive = repo_root / "dist" / "releases" / f"{ARCHIVE_PREFIX}-{version.replace(',', '-')}.zip"
    with zipfile.ZipFile(archive) as archive_file:
        names = set(archive_file.namelist())
        required = {"README.md", "BUILD-INFO.json", *(f"{family['postscript']}.ttc" for family in FAMILIES)}
        if not required <= names or not any(name.startswith("licenses/") for name in names):
            raise SystemExit(f"{archive.name} contents are {sorted(names)}")
        for family in FAMILIES:
            name = f"{family['postscript']}.ttc"
            packed = hashlib.sha256(archive_file.read(name)).hexdigest()
            if packed != sha256(output / name):
                raise SystemExit(f"{archive.name}: {name} differs from the verified build")
    print(f"verified {archive}")


if __name__ == "__main__":
    module = Path(__file__).resolve().parent
    verify(module.parents[1])
