# /// script
# requires-python = ">=3.12"
# dependencies = ["fonttools==4.59.0", "py7zr==1.0.0"]
# ///

from __future__ import annotations

import hashlib
import json
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

import py7zr
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTCollection, TTFont
from fontTools.ttLib.tables.ttProgram import Program

FAMILY = "Sarasa Term Slab SS17 SC Nerd Font"
VERSION = "1.0.41,34.7.0,3.5.1"
POSTSCRIPT_FAMILY = "SarasaTermSlabSS17SCNF"
SPINNER = range(0xF800, 0xF840)
IOSEVKA_RANGES = (
    range(0x0020, 0x0250),
    range(0x1E00, 0x1F00),
    range(0x2000, 0x2400),
    range(0x2500, 0x27C0),
    range(0x2B00, 0x2C00),
)
NERD_RANGES = (
    range(0xE000, 0xF800),
    range(0xF840, 0xF900),
    range(0xF0000, 0xFFFFE),
)
FACES = (
    (400, False, "Regular", "Regular"),
    (600, False, "Semibold", "Semibold"),
    (700, False, "Bold", "Bold"),
    (400, True, "Italic", "Italic"),
    (600, True, "Semibold Italic", "SemiboldItalic"),
    (700, True, "Bold Italic", "BoldItalic"),
)
SOURCES = {
    "sarasa": {
        "url": "https://github.com/be5invis/Sarasa-Gothic/releases/download/v1.0.41/SarasaTermSlabSC-TTF-1.0.41.7z",
        "sha256": "d240c69b2424dc7165f9af57a6e9ecac653afae5ff4d4c034d8d203efc13c92c",
        "family": "Sarasa Term Slab SC",
    },
    "iosevka": {
        "url": "https://github.com/sidkang/homebrew/releases/download/iosevka-term-slab-ss17-v34.7.0/IosevkaTermSlabSS17-34.7.0.zip",
        "sha256": "93f34c025ba9ca1a6efb00f7556a6530f04a77d117ca9b04583ce74c854337c4",
        "family": "Iosevka Term Slab SS17",
    },
    "nerd": {
        "url": "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.5.1/IosevkaTerm.zip",
        "sha256": "b0dfd98968b7c7743080431257bfd082c5ef7dd4d1c674d3ce16bc5520c10cdc",
        "family": "IosevkaTerm Nerd Font Mono",
        "family_aliases": ("IosevkaTerm Nerd Font Mono", "IosevkaTerm NFM"),
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def apply_source_overrides() -> None:
    overrides = {
        "sarasa": ("SARASA_URL", "SARASA_SHA256"),
        "iosevka": ("IOSEVKA_URL", "IOSEVKA_SHA256"),
        "nerd": ("NERD_URL", "NERD_SHA256"),
    }
    for key, (url_name, sha_name) in overrides.items():
        url = os.environ.get(url_name)
        digest = os.environ.get(sha_name)
        if url:
            SOURCES[key]["url"] = url
        if digest:
            SOURCES[key]["sha256"] = digest
    version = os.environ.get("FONT_VERSION")
    if version:
        global VERSION
        VERSION = version


def download(url: str, path: Path, expected: str) -> None:
    if path.exists() and sha256(path) == expected:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    urllib.request.urlretrieve(url, temporary)
    actual = sha256(temporary)
    if actual != expected:
        temporary.unlink(missing_ok=True)
        raise SystemExit(f"{url} sha256 is {actual}, expected {expected}")
    temporary.replace(path)


def extract(archive: Path, destination: Path, expected: str) -> None:
    stamp = destination / ".sha256"
    if stamp.exists() and stamp.read_text().strip() == expected:
        return
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    if archive.suffix == ".7z":
        with py7zr.SevenZipFile(archive, mode="r") as archive_file:
            archive_file.extractall(path=destination)
    else:
        with zipfile.ZipFile(archive) as archive_file:
            archive_file.extractall(destination)
    stamp.write_text(expected + "\n")


def font_names(font: TTFont, name_id: int) -> set[str]:
    found = set()
    for record in font["name"].names:
        if record.nameID != name_id:
            continue
        try:
            found.add(record.toUnicode())
        except UnicodeError:
            continue
    return found


def italic(font: TTFont) -> bool:
    return bool(font["OS/2"].fsSelection & 1)


def oblique_only(font: TTFont) -> bool:
    selection = font["OS/2"].fsSelection
    return bool(selection & (1 << 9)) and not bool(selection & 1)


def family_matches(font: TTFont, expected: str, aliases: tuple[str, ...] = ()) -> bool:
    accepted = (expected, *aliases)
    for name_id in (1, 16):
        for value in font_names(font, name_id):
            if any(value == item or value.startswith(f"{item} ") for item in accepted):
                return True
    return False


def load_collection(path: Path) -> list[tuple[Path, int | None, TTFont]]:
    if path.suffix.lower() == ".ttc":
        collection = TTCollection(str(path))
        return [(path, index, font) for index, font in enumerate(collection.fonts)]
    return [(path, None, TTFont(str(path), lazy=True))]


def iter_fonts(directory: Path, marker: str | None = None) -> list[tuple[Path, int | None, TTFont]]:
    fonts = []
    for path in sorted(directory.rglob("*")):
        if path.suffix.lower() not in {".ttf", ".otf", ".ttc"}:
            continue
        if marker and marker not in path.name:
            continue
        fonts.extend(load_collection(path))
    return fonts


def select_faces(
    directory: Path,
    family: str,
    aliases: tuple[str, ...] = (),
    marker: str | None = None,
) -> dict[tuple[int, bool], dict[str, object]]:
    chosen: dict[tuple[int, bool], dict[str, object]] = {}
    for path, index, font in iter_fonts(directory, marker):
        if not family_matches(font, family, aliases) or oblique_only(font):
            continue
        key = (font["OS/2"].usWeightClass, italic(font))
        if key not in {(weight, is_italic) for weight, is_italic, _, _ in FACES}:
            continue
        described = {
            "path": str(path),
            "index": index,
            "weight": key[0],
            "italic": key[1],
            "family": sorted(font_names(font, 1)),
            "style": sorted(font_names(font, 2)),
            "upm": font["head"].unitsPerEm,
            "font": font,
        }
        if key in chosen:
            raise SystemExit(f"multiple {family} faces match weight {key[0]} italic {key[1]}")
        chosen[key] = described
    missing = [
        style
        for weight, is_italic, style, _ in FACES
        if (weight, is_italic) not in chosen
    ]
    if missing:
        raise SystemExit(f"{family} is missing exact faces: {', '.join(missing)}")
    return chosen


def unicode_tables(font: TTFont):
    return [table for table in font["cmap"].tables if table.format in {4, 12, 13}]


def mapping(font: TTFont) -> dict[int, str]:
    best = font.getBestCmap() or {}
    return dict(best)


def set_mapping(font: TTFont, codepoint: int, glyph_name: str) -> None:
    for table in unicode_tables(font):
        if table.format == 4 and codepoint > 0xFFFF:
            continue
        table.cmap[codepoint] = glyph_name


def delete_mapping(font: TTFont, codepoint: int) -> None:
    for table in unicode_tables(font):
        table.cmap.pop(codepoint, None)


def flatten_glyph(source: TTFont, glyph_name: str, scale: float):
    glyph_set = source.getGlyphSet()
    recorded = DecomposingRecordingPen(glyph_set)
    glyph_set[glyph_name].draw(recorded)
    pen = TTGlyphPen(None)
    recorded.replay(pen)
    glyph = pen.glyph()
    glyph.program = Program()
    if scale != 1 and getattr(glyph, "coordinates", None):
        glyph.coordinates.scale((scale, scale))
    return glyph


def retain_codepoints(base: TTFont, donors: list[tuple[TTFont, set[int]]]) -> set[int]:
    keep = set(mapping(base))
    keep.difference_update(SPINNER)
    for donor, points in donors:
        donor_map = mapping(donor)
        keep.difference_update(codepoint for codepoint in points if codepoint in donor_map)
    return keep


def glyph_closure(font: TTFont, names: set[str]) -> set[str]:
    found: set[str] = set()
    pending = list(names)
    while pending:
        name = pending.pop()
        if name in found or name not in font["glyf"]:
            continue
        found.add(name)
        glyph = font["glyf"][name]
        if glyph.isComposite():
            pending.extend(component.glyphName for component in glyph.components)
    return found


def retain_glyphs(font: TTFont, unicodes: set[int]) -> None:
    current = mapping(font)
    for table in unicode_tables(font):
        for codepoint in list(table.cmap):
            if codepoint not in unicodes:
                del table.cmap[codepoint]
    keep = glyph_closure(font, {current[codepoint] for codepoint in unicodes if codepoint in current})
    keep.add(".notdef")
    order = [name for name in font.getGlyphOrder() if name in keep]
    metrics = font["hmtx"].metrics
    glyf = font["glyf"]
    for name in list(glyf.keys()):
        if name not in keep:
            del glyf[name]
    for name in list(metrics):
        if name not in keep:
            del metrics[name]
    for name in order:
        metrics.setdefault(name, (0, 0))
    font.setGlyphOrder(order)
    font["maxp"].numGlyphs = len(order)
    font["hhea"].numberOfHMetrics = len(order)
    for tag in ("GSUB", "GPOS", "GDEF"):
        if tag in font:
            del font[tag]


def copy_glyphs(source: TTFont, destination: TTFont, codepoints: set[int], prefix: str) -> dict[int, str]:
    source_map = mapping(source)
    wanted = {codepoint: source_map[codepoint] for codepoint in codepoints if codepoint in source_map}
    scale = destination["head"].unitsPerEm / source["head"].unitsPerEm
    renamed = {}
    for glyph_name in sorted(set(wanted.values())):
        new_name = f"{prefix}.{glyph_name}"
        while new_name in destination["glyf"] or new_name in renamed.values():
            new_name = f"{new_name}_"
        renamed[glyph_name] = new_name
    order = list(destination.getGlyphOrder())
    for glyph_name, new_name in renamed.items():
        destination["glyf"][new_name] = flatten_glyph(source, glyph_name, scale)
        advance, bearing = source["hmtx"][glyph_name]
        destination["hmtx"][new_name] = (round(advance * scale), round(bearing * scale))
        order.append(new_name)
    destination.setGlyphOrder(order)
    destination["maxp"].numGlyphs = len(order)
    destination["hhea"].numberOfHMetrics = len(order)
    copied = {}
    for codepoint, glyph_name in wanted.items():
        set_mapping(destination, codepoint, renamed[glyph_name])
        copied[codepoint] = renamed[glyph_name]
    return copied


def codepoints(ranges: tuple[range, ...]) -> set[int]:
    found: set[int] = set()
    for item in ranges:
        found.update(item)
    return found


def set_family(font: TTFont, style: str, postscript_style: str) -> None:
    full_name = f"{FAMILY} {style}"
    postscript = f"{POSTSCRIPT_FAMILY}-{postscript_style}"
    values = {
        0: "Copyright 2026 Sid Kang. Latin and symbols from Iosevka; CJK from Sarasa Gothic; icons from Nerd Fonts.",
        1: FAMILY,
        2: style,
        3: f"{VERSION};{POSTSCRIPT_FAMILY};{postscript_style}",
        4: full_name,
        6: postscript,
        16: FAMILY,
        17: style,
    }
    for name_id, value in values.items():
        font["name"].setName(value, name_id, 3, 1, 0x409)
        font["name"].setName(value, name_id, 1, 0, 0)


def public_face(described: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in described.items() if key != "font"}


def realize(described: dict[str, object]) -> TTFont:
    path = Path(str(described["path"]))
    index = described["index"]
    if index is None:
        font = TTFont(str(path))
    else:
        font = TTCollection(str(path)).fonts[int(index)]
    described["font"] = font
    return font


def build(module_dir: Path, repo_root: Path) -> None:
    apply_source_overrides()
    cache = repo_root / "dist" / "sarasa-term-slab-ss17-sc-nerd-font" / "cache"
    output = repo_root / "dist" / "sarasa-term-slab-ss17-sc-nerd-font"
    release = repo_root / "dist" / "releases"
    output.mkdir(parents=True, exist_ok=True)
    release.mkdir(parents=True, exist_ok=True)
    extracted = {}
    for key, source in SOURCES.items():
        filename = source["url"].rsplit("/", 1)[-1]
        archive = cache / filename
        download(source["url"], archive, source["sha256"])
        destination = cache / key
        extract(archive, destination, source["sha256"])
        extracted[key] = destination

    sarasa = select_faces(extracted["sarasa"], SOURCES["sarasa"]["family"])
    iosevka = select_faces(extracted["iosevka"], SOURCES["iosevka"]["family"])
    nerd = select_faces(
        extracted["nerd"],
        SOURCES["nerd"]["family"],
        SOURCES["nerd"]["family_aliases"],
        marker="NerdFontMono",
    )
    iosevka_points = codepoints(IOSEVKA_RANGES)
    nerd_points = codepoints(NERD_RANGES) - set(SPINNER)
    built = []
    face_info = []
    for weight, is_italic, style, postscript_style in FACES:
        key = (weight, is_italic)
        destination = realize(sarasa[key])
        iosevka_font = realize(iosevka[key])
        nerd_font = realize(nerd[key])
        retain_glyphs(
            destination,
            retain_codepoints(
                destination,
                [(iosevka_font, iosevka_points), (nerd_font, nerd_points)],
            ),
        )
        iosevka_copied = copy_glyphs(iosevka_font, destination, iosevka_points, "ss17")
        nerd_copied = copy_glyphs(nerd_font, destination, nerd_points, "nerd")
        if destination["maxp"].numGlyphs > 65535:
            raise SystemExit(f"{style} has {destination['maxp'].numGlyphs} glyphs; TrueType holds at most 65535")
        for tag in ("vmtx", "vhea", "VORG"):
            if tag in destination:
                del destination[tag]
        for codepoint in SPINNER:
            delete_mapping(destination, codepoint)
        set_family(destination, style, postscript_style)
        built.append(destination)
        face_info.append(
            {
                "style": style,
                "weight": weight,
                "italic": is_italic,
                "sarasa": public_face(sarasa[key]),
                "iosevka": public_face(iosevka[key]),
                "nerd": public_face(nerd[key]),
                "iosevkaCodepoints": len(iosevka_copied),
                "nerdCodepoints": len(nerd_copied),
            }
        )

    collection_path = output / f"{POSTSCRIPT_FAMILY}.ttc"
    collection = TTCollection()
    collection.fonts = built
    collection.save(collection_path)
    info = {
        "family": FAMILY,
        "version": VERSION,
        "file": collection_path.name,
        "sources": {key: {"url": value["url"], "sha256": value["sha256"]} for key, value in SOURCES.items()},
        "faces": face_info,
    }
    (output / "BUILD-INFO.json").write_text(json.dumps(info, indent=2) + "\n")
    stage = output / "stage"
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir()
    shutil.copy(collection_path, stage / collection_path.name)
    shutil.copy(module_dir / "README.md", stage / "README.md")
    shutil.copytree(module_dir / "licenses", stage / "licenses")
    shutil.copy(output / "BUILD-INFO.json", stage / "BUILD-INFO.json")
    archive = release / f"{POSTSCRIPT_FAMILY}-{VERSION.replace(',', '-')}.zip"
    if archive.exists():
        archive.unlink()
    shutil.make_archive(archive.with_suffix(""), "zip", stage)
    print(f"built {archive}")


if __name__ == "__main__":
    module = Path(__file__).resolve().parent
    build(module, module.parents[1])
