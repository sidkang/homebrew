# /// script
# requires-python = ">=3.12"
# dependencies = ["fonttools==4.59.0", "py7zr==1.0.0"]
# ///

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

import py7zr
from fontTools import subset
from fontTools.otlLib.maxContextCalc import maxCtxFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTCollection, TTFont

MODULE = "sarasa-ss17-sc-nerd-font"
VERSION = "1.0.41,34.7.0-r2,3.5.1"
ARCHIVE_PREFIX = "SarasaSS17SCNF"
# All sources use 1000 UPM. Glyphs copy without scaling.
UPM = 1000
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
LAYOUT_TABLES = ("GSUB", "GPOS", "GDEF")
OVERLAP_SIMPLE = 0x40
IOSEVKA_PREFIX = "ss17"
NERD_PREFIX = "nerd"
FACES = (
    (200, False, "ExtraLight", "ExtraLight"),
    (300, False, "Light", "Light"),
    (400, False, "Regular", "Regular"),
    (600, False, "Semibold", "Semibold"),
    (700, False, "Bold", "Bold"),
    (200, True, "ExtraLight Italic", "ExtraLightItalic"),
    (300, True, "Light Italic", "LightItalic"),
    (400, True, "Italic", "Italic"),
    (600, True, "Semibold Italic", "SemiboldItalic"),
    (700, True, "Bold Italic", "BoldItalic"),
)
# Override sources using <KEY>_URL and <KEY>_SHA256. file:// URLs are supported.
SOURCES = {
    "sarasa-term-slab": {
        "url": "https://github.com/be5invis/Sarasa-Gothic/releases/download/v1.0.41/SarasaTermSlabSC-TTF-1.0.41.7z",
        "sha256": "d240c69b2424dc7165f9af57a6e9ecac653afae5ff4d4c034d8d203efc13c92c",
        "family": "Sarasa Term Slab SC",
    },
    "sarasa-mono": {
        "url": "https://github.com/be5invis/Sarasa-Gothic/releases/download/v1.0.41/SarasaMonoSC-TTF-1.0.41.7z",
        "sha256": "cd078f6103af293c8943f9a333beee2ecf1fe5b6901950a4f610eb37e1b3c0f2",
        "family": "Sarasa Mono SC",
    },
    # Requires the 10-face donor from fonts/iosevka-term-slab-ss17. Pass URL and SHA-256 explicitly.
    "iosevka-term-slab": {
        "url": None,
        "sha256": None,
        "family": "Iosevka Term Slab SS17",
    },
    "iosevka-mono": {
        "url": "https://github.com/be5invis/Iosevka/releases/download/v34.7.0/PkgTTC-IosevkaSS17-34.7.0.zip",
        "sha256": "90dd4a68e9504a2aff27625494ac3309ba7eb659b8735b1fd2902206ef54d07c",
        "family": "Iosevka SS17",
    },
    "nerd": {
        "url": "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.5.1/IosevkaTerm.zip",
        "sha256": "b0dfd98968b7c7743080431257bfd082c5ef7dd4d1c674d3ce16bc5520c10cdc",
        "family": "IosevkaTerm Nerd Font Mono",
        "marker": "NerdFontMono",
    },
}
# Both families share Nerd Font Mono icons. Only Mono retains Iosevka OpenType layout tables.
FAMILIES = (
    {
        "family": "Sarasa Term Slab SS17 SC Nerd Font",
        "postscript": "SarasaTermSlabSS17SCNF",
        "sarasa": "sarasa-term-slab",
        "iosevka": "iosevka-term-slab",
        "layout": False,
    },
    {
        "family": "Sarasa Mono SS17 SC Nerd Font",
        "postscript": "SarasaMonoSS17SCNF",
        "sarasa": "sarasa-mono",
        "iosevka": "iosevka-mono",
        "layout": True,
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def env_prefix(key: str) -> str:
    return key.upper().replace("-", "_")


def apply_source_overrides() -> None:
    for key, source in SOURCES.items():
        url = os.environ.get(f"{env_prefix(key)}_URL")
        digest = os.environ.get(f"{env_prefix(key)}_SHA256")
        if url:
            source["url"] = url
        if digest:
            source["sha256"] = digest
    missing = [env_prefix(key) for key, source in SOURCES.items() if not source["url"] or not source["sha256"]]
    if missing:
        names = ", ".join(f"{name}_URL and {name}_SHA256" for name in missing)
        raise SystemExit(f"Missing required sources: {names}. Provide the 10-face Iosevka Term Slab SS17 archive.")
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
        raise SystemExit(f"SHA-256 mismatch for {url}: got {actual}, expected {expected}")
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
    return {record.toUnicode() for record in font["name"].names if record.nameID == name_id}


def italic(font: TTFont) -> bool:
    return bool(font["OS/2"].fsSelection & 1)


def oblique(font: TTFont) -> bool:
    # Iosevka Oblique faces set both ITALIC and OBLIQUE bits.
    return bool(font["OS/2"].fsSelection & (1 << 9))


def family_matches(font: TTFont, expected: str) -> bool:
    for name_id in (1, 16):
        for value in font_names(font, name_id):
            if value == expected or value.startswith(f"{expected} "):
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


def select_faces(directory: Path, source: dict[str, object]) -> dict[tuple[int, bool], dict[str, object]]:
    family = str(source["family"])
    chosen: dict[tuple[int, bool], dict[str, object]] = {}
    for path, index, font in iter_fonts(directory, source.get("marker")):
        if not family_matches(font, family) or oblique(font):
            continue
        # Skip Iosevka Extended faces sharing the typographic family.
        if font["OS/2"].usWidthClass != 5:
            continue
        key = (font["OS/2"].usWeightClass, italic(font))
        if key not in {(weight, is_italic) for weight, is_italic, _, _ in FACES}:
            continue
        if font["head"].unitsPerEm != UPM:
            raise SystemExit(f"{family} ({path.name}) has unitsPerEm {font['head'].unitsPerEm}, expected {UPM}")
        described = {
            "path": str(path),
            "index": index,
            "weight": key[0],
            "italic": key[1],
            "family": sorted(font_names(font, 1)),
            "style": sorted(font_names(font, 2)),
            "font": font,
        }
        if key in chosen:
            raise SystemExit(f"Duplicate {family} face matching weight {key[0]} and italic {key[1]}")
        chosen[key] = described
    missing = [
        style
        for weight, is_italic, style, _ in FACES
        if (weight, is_italic) not in chosen
    ]
    if missing:
        raise SystemExit(f"{family} is missing required faces: {', '.join(missing)}")
    return chosen


def unicode_tables(font: TTFont):
    return [table for table in font["cmap"].tables if table.format in {4, 12, 13}]


def mapping(font: TTFont) -> dict[int, str]:
    return dict(font.getBestCmap())


def set_mapping(font: TTFont, codepoint: int, glyph_name: str) -> None:
    for table in unicode_tables(font):
        if table.format == 4 and codepoint > 0xFFFF:
            continue
        table.cmap[codepoint] = glyph_name


def delete_mapping(font: TTFont, codepoint: int) -> None:
    for table in unicode_tables(font):
        table.cmap.pop(codepoint, None)


def flatten_glyph(source: TTFont, glyph_name: str):
    glyph_set = source.getGlyphSet()
    recorded = DecomposingRecordingPen(glyph_set)
    glyph_set[glyph_name].draw(recorded)
    pen = TTGlyphPen(None)
    recorded.replay(pen)
    return pen.glyph()


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
        if name in found:
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
    # Rebuild tables directly to avoid repeated linear scans of the glyph order.
    glyf = font["glyf"]
    glyf.glyphs = {name: glyf.glyphs[name] for name in order}
    glyf.glyphOrder = order
    font["hmtx"].metrics = {name: font["hmtx"].metrics[name] for name in order}
    keep_outline_offsets(font, order)
    font.setGlyphOrder(order)
    font["maxp"].numGlyphs = len(order)
    font["hhea"].numberOfHMetrics = len(order)
    for tag in LAYOUT_TABLES:
        if tag in font:
            del font[tag]


def keep_outline_offsets(font: TTFont, names: list[str]) -> None:
    """Preserve outline positions when recalculating xMin.

    Renderers place outlines at lsb - xMin. Upstream Sarasa italic fonts store an xMin
    off by one unit; saving recalculates xMin, so lsb must shift by the same delta.
    """
    glyf = font["glyf"]
    metrics = font["hmtx"].metrics
    for name in names:
        glyph = glyf[name]
        if glyph.numberOfContours == 0:
            continue
        stored = glyph.xMin
        glyph.recalcBounds(glyf)
        if glyph.xMin != stored:
            advance, bearing = metrics[name]
            metrics[name] = (advance, bearing + glyph.xMin - stored)


def add_glyphs(source: TTFont, destination: TTFont, renamed: dict[str, str]) -> None:
    glyf = destination["glyf"]
    order = list(destination.getGlyphOrder())
    for glyph_name, new_name in renamed.items():
        if new_name in glyf:
            raise SystemExit(f"donor glyph {new_name} clashes with the base")
        glyph = flatten_glyph(source, glyph_name)
        # Assign via .glyphs dictionary to avoid linear scans of the glyph order.
        glyf.glyphs[new_name] = glyph
        advance, bearing = source["hmtx"][glyph_name]
        # Flattened outline coordinates are already at rendered positions.
        if glyph.numberOfContours:
            glyph.recalcBounds(glyf)
            bearing = glyph.xMin
        destination["hmtx"][new_name] = (advance, bearing)
        order.append(new_name)
    glyf.glyphOrder = order
    destination.setGlyphOrder(order)
    destination["maxp"].numGlyphs = len(order)
    destination["hhea"].numberOfHMetrics = len(order)


def copy_glyphs(source: TTFont, destination: TTFont, codepoints: set[int], prefix: str) -> dict[int, str]:
    source_map = mapping(source)
    wanted = {codepoint: source_map[codepoint] for codepoint in codepoints if codepoint in source_map}
    renamed = {glyph_name: f"{prefix}.{glyph_name}" for glyph_name in sorted(set(wanted.values()))}
    add_glyphs(source, destination, renamed)
    copied = {codepoint: renamed[glyph_name] for codepoint, glyph_name in wanted.items()}
    for codepoint, glyph_name in copied.items():
        set_mapping(destination, codepoint, glyph_name)
    return copied


def layout_donor(font: TTFont, codepoints: set[int], prefix: str) -> TTFont:
    """Subset donor to codepoints and layout closure with prefixed glyph names.

    Renaming the glyph order before decompiling layout tables binds GSUB, GPOS,
    and GDEF to prefixed names without manual table traversal.
    """
    options = subset.Options()
    options.layout_features = ["*"]
    options.layout_scripts = ["*"]
    options.glyph_names = True
    options.hinting = False
    options.notdef_outline = True
    options.name_IDs = ["*"]
    options.name_languages = ["*"]
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=codepoints & set(mapping(font)))
    subsetter.subset(font)
    buffer = io.BytesIO()
    font.save(buffer)
    buffer.seek(0)
    renamed = TTFont(buffer)
    renamed.setGlyphOrder([f"{prefix}.{name}" for name in renamed.getGlyphOrder()])
    return renamed


def transplant(source: TTFont, destination: TTFont, codepoints: set[int]) -> dict[int, str]:
    add_glyphs(source, destination, {name: name for name in source.getGlyphOrder()})
    copied = {}
    for codepoint, glyph_name in mapping(source).items():
        if codepoint in codepoints:
            set_mapping(destination, codepoint, glyph_name)
            copied[codepoint] = glyph_name
    for tag in LAYOUT_TABLES:
        if tag in source:
            source[tag].ensureDecompiled()
            destination[tag] = source[tag]
    destination["OS/2"].usMaxContext = maxCtxFont(destination)
    return copied


def fold_overlap_flags(font: TTFont) -> None:
    """Retain OVERLAP_SIMPLE only on the first flag byte, as required by OTS.

    fontTools expands repeated flag bytes onto later points, causing OTS failures.
    Clear the bit on points after index 0.
    """
    glyf = font["glyf"]
    for name in font.getGlyphOrder():
        glyph = glyf[name]
        if glyph.numberOfContours <= 0:
            continue
        flags = glyph.flags
        for index in range(1, len(flags)):
            flags[index] &= ~OVERLAP_SIMPLE


def codepoints(ranges: tuple[range, ...]) -> set[int]:
    found: set[int] = set()
    for item in ranges:
        found.update(item)
    return found


def set_family(font: TTFont, family: str, postscript_family: str, style: str, postscript_style: str) -> None:
    full_name = f"{family} {style}"
    postscript = f"{postscript_family}-{postscript_style}"
    values = {
        0: "Copyright 2026 Sid Kang. Latin and symbols from Iosevka; CJK from Sarasa Gothic; icons from Nerd Fonts.",
        1: family,
        2: style,
        3: f"{VERSION};{postscript_family};{postscript_style}",
        4: full_name,
        6: postscript,
        16: family,
        17: style,
    }
    # Overwrite localized name records so none keep the upstream identity.
    for record in font["name"].names:
        if record.nameID in values:
            record.string = values[record.nameID]
    for name_id, value in values.items():
        font["name"].setName(value, name_id, 3, 1, 0x409)
        font["name"].setName(value, name_id, 1, 0, 0)


def public_face(described: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in described.items() if key != "font"}


def realize(described: dict[str, object]) -> TTFont:
    path = Path(str(described["path"]))
    index = described["index"]
    if index is None:
        return TTFont(str(path))
    return TTCollection(str(path)).fonts[int(index)]


def build_face(
    family: dict[str, object],
    sarasa: dict[str, object],
    iosevka: dict[str, object],
    nerd: dict[str, object],
    style: str,
    postscript_style: str,
) -> tuple[TTFont, int, int]:
    destination = realize(sarasa)
    iosevka_font = realize(iosevka)
    nerd_font = realize(nerd)
    iosevka_points = codepoints(IOSEVKA_RANGES)
    nerd_points = codepoints(NERD_RANGES) - set(SPINNER)
    retain_glyphs(
        destination,
        retain_codepoints(
            destination,
            [(iosevka_font, iosevka_points), (nerd_font, nerd_points)],
        ),
    )
    if family["layout"]:
        iosevka_copied = transplant(layout_donor(iosevka_font, iosevka_points, IOSEVKA_PREFIX), destination, iosevka_points)
    else:
        iosevka_copied = copy_glyphs(iosevka_font, destination, iosevka_points, IOSEVKA_PREFIX)
    nerd_copied = copy_glyphs(nerd_font, destination, nerd_points, NERD_PREFIX)
    if destination["maxp"].numGlyphs > 65535:
        raise SystemExit(f"{style} exceeds TrueType limit of 65535 glyphs ({destination['maxp'].numGlyphs})")
    for tag in ("vmtx", "vhea", "VORG"):
        if tag in destination:
            del destination[tag]
    for codepoint in SPINNER:
        delete_mapping(destination, codepoint)
    fold_overlap_flags(destination)
    set_family(destination, str(family["family"]), str(family["postscript"]), style, postscript_style)
    return destination, len(iosevka_copied), len(nerd_copied)


def build_family(
    family: dict[str, object],
    extracted: dict[str, Path],
    nerd: dict[tuple[int, bool], dict[str, object]],
    output: Path,
) -> dict[str, object]:
    sarasa = select_faces(extracted[str(family["sarasa"])], SOURCES[str(family["sarasa"])])
    iosevka = select_faces(extracted[str(family["iosevka"])], SOURCES[str(family["iosevka"])])
    faces_dir = output / "faces" / str(family["postscript"])
    shutil.rmtree(faces_dir, ignore_errors=True)
    faces_dir.mkdir(parents=True)
    face_paths = []
    face_info = []
    for weight, is_italic, style, postscript_style in FACES:
        key = (weight, is_italic)
        font, iosevka_count, nerd_count = build_face(family, sarasa[key], iosevka[key], nerd[key], style, postscript_style)
        # Save faces individually to minimize memory usage from open CJK fonts.
        path = faces_dir / f"{family['postscript']}-{postscript_style}.ttf"
        font.save(path)
        glyphs = font["maxp"].numGlyphs
        del font
        face_paths.append(path)
        face_info.append(
            {
                "style": style,
                "weight": weight,
                "italic": is_italic,
                "glyphs": glyphs,
                "sarasa": public_face(sarasa[key]),
                "iosevka": public_face(iosevka[key]),
                "nerd": public_face(nerd[key]),
                "iosevkaCodepoints": iosevka_count,
                "nerdCodepoints": nerd_count,
            }
        )
        print(f"built {family['family']} {style}: {glyphs} glyphs")
    collection_path = output / f"{family['postscript']}.ttc"
    collection = TTCollection()
    collection.fonts = [TTFont(str(path), lazy=True) for path in face_paths]
    collection.save(collection_path)
    shutil.rmtree(faces_dir)
    return {
        "family": family["family"],
        "postscript": family["postscript"],
        "file": collection_path.name,
        "layout": family["layout"],
        "sarasa": family["sarasa"],
        "iosevka": family["iosevka"],
        "faces": face_info,
    }


def build(module_dir: Path, repo_root: Path) -> None:
    apply_source_overrides()
    output = repo_root / "dist" / MODULE
    cache = output / "cache"
    release = repo_root / "dist" / "releases"
    output.mkdir(parents=True, exist_ok=True)
    release.mkdir(parents=True, exist_ok=True)
    extracted = {}
    for key, source in SOURCES.items():
        filename = str(source["url"]).rsplit("/", 1)[-1]
        archive = cache / filename
        download(str(source["url"]), archive, str(source["sha256"]))
        destination = cache / key
        extract(archive, destination, str(source["sha256"]))
        extracted[key] = destination

    nerd = select_faces(extracted["nerd"], SOURCES["nerd"])
    families = [build_family(family, extracted, nerd, output) for family in FAMILIES]
    info = {
        "version": VERSION,
        "sources": {key: {"url": value["url"], "sha256": value["sha256"]} for key, value in SOURCES.items()},
        "families": families,
    }
    (output / "BUILD-INFO.json").write_text(json.dumps(info, indent=2) + "\n")
    archive = release / f"{ARCHIVE_PREFIX}-{VERSION.replace(',', '-')}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for family in families:
            bundle.write(output / str(family["file"]), str(family["file"]))
        bundle.write(module_dir / "README.md", "README.md")
        bundle.write(output / "BUILD-INFO.json", "BUILD-INFO.json")
        for license_file in sorted((module_dir / "licenses").iterdir()):
            bundle.write(license_file, f"licenses/{license_file.name}")
    print(f"built {archive}")


if __name__ == "__main__":
    module = Path(__file__).resolve().parent
    build(module, module.parents[1])
