# Sarasa SS17 SC Nerd Font

This package provides two distinct font families for terminals and editors. Each family contains Latin characters, CJK ideographs, and Nerd Font icons in a single font file.

| Family | File | Base | Latin and symbols | Ligatures |
| --- | --- | --- | --- | --- |
| Sarasa Term Slab SS17 SC Nerd Font | `SarasaTermSlabSS17SCNF.ttc` | Sarasa Term Slab SC | Iosevka Term Slab SS17 (this tap) | No |
| Sarasa Mono SS17 SC Nerd Font | `SarasaMonoSS17SCNF.ttc` | Sarasa Mono SC | Iosevka SS17 (official upstream) | Yes |

These Sarasa variants combine Iosevka and Source Han Sans. SS17 is the Recursive Mono character variant. Nerd Font adds developer icons. Family names follow this sequence: Sarasa style (`Term Slab` or `Mono`), SS17 variant, SC orthography (Simplified Chinese), and the Nerd Font suffix.

- **Term Slab**: Terminal-width symbols take one cell (narrow arrows, em dashes). Slab-serif Latin. No programming ligatures. Family and PostScript names remain identical to earlier single-family releases.
- **Mono**: Standard typographic symbols take two cells (full-width em dashes, ellipses). Sans-serif Latin. Includes Iosevka SS17 OpenType layout features (`calt`, `dlig`), enabling programming ligatures such as `->`, `!=`, and `<=`.

Both families are SC only and have ten faces each:

| Weight | Upright | Italic |
| --- | --- | --- |
| 200 | ExtraLight | ExtraLight Italic |
| 300 | Light | Light Italic |
| 400 | Regular | Italic |
| 600 | Semibold | Semibold Italic |
| 700 | Bold | Bold Italic |

All sources use 1000 units per em (UPM). Outlines copy directly without scaling.

## Ranges

| Code points | Source |
| --- | --- |
| U+0020–U+024F, U+1E00–U+1EFF, U+2000–U+23FF, U+2500–U+27BF, U+2B00–U+2BFF | Iosevka Term Slab SS17 (Term Slab) or Iosevka SS17 (Mono) |
| U+E000–U+F7FF, U+F840–U+F8FF, U+F0000–U+FFFFD | IosevkaTerm Nerd Font Mono |
| All other code points (including CJK) | Sarasa Term Slab SC or Sarasa Mono SC |
| U+F800–U+F83F | Omitted (reserved for Braille Spinner Kitty Term) |

Nerd Font Mono icons are single-cell glyphs. Both families share the same icon donor.

## Layout tables

Term Slab contains no OpenType layout tables (`GSUB`, `GPOS`, `GDEF`), preventing substitutions. Mono retains Iosevka SS17 layout tables. The build subsets Iosevka to the target character ranges and their layout closure, then copies the resulting glyphs and tables into the Sarasa base.

Both families omit Sarasa's CJK layout features, including vertical forms (`vert`) and localized forms (`locl`), plus vertical metrics tables (`vhea`, `vmtx`, `VORG`). These fonts target horizontal SC text; they do not preserve all upstream layout features.

## Outline and metric corrections

- **Overlap flags**: fontTools can copy `OVERLAP_SIMPLE` from a repeated first flag onto later points. The build clears the bit from later points and keeps the first point's flag. This passes OpenType Sanitizer without changing outlines.
- **Italic bearing offsets**: Renderers place outlines at `lsb - xMin`. Some Sarasa italic glyphs store an `xMin` one unit away from their computed bounds. The build moves `lsb` by the same amount as `xMin` to keep those outlines in place.

## Build

The build requires the 10-face `IosevkaTermSlabSS17` donor archive from `fonts/iosevka-term-slab-ss17`. Because release `34.7.0-r2` is not yet published to GitHub Releases, provide this archive locally:

```bash
IOSEVKA_TERM_SLAB_URL=file:///path/to/IosevkaTermSlabSS17-34.7.0-r2.zip \
IOSEVKA_TERM_SLAB_SHA256=<sha256> \
fonts/sarasa-ss17-sc-nerd-font/build.sh
```

Override any source using `<KEY>_URL` and `<KEY>_SHA256`:

| Key | Default source |
| --- | --- |
| `SARASA_TERM_SLAB` | `SarasaTermSlabSC-TTF-1.0.41.7z` |
| `SARASA_MONO` | `SarasaMonoSC-TTF-1.0.41.7z` |
| `IOSEVKA_TERM_SLAB` | Required; local file or release URL |
| `IOSEVKA_MONO` | `PkgTTC-IosevkaSS17-34.7.0.zip` |
| `NERD` | `IosevkaTerm.zip` (v3.5.1) |

`FONT_VERSION` sets the version string in font metadata and the release archive name. The build creates `dist/releases/SarasaSS17SCNF-<version>.zip` directly, containing both TTC files, this README, `licenses/`, and `BUILD-INFO.json`.

The verifier checks that:

- Both TTC files pass OpenType Sanitizer.
- All 20 faces have the expected names, weights, and slopes, including localized name records.
- Sarasa CJK character mappings, advances, and sampled outlines are preserved.
- Latin and icon outlines and advances match their sources.
- Spinner code points U+F800–U+F83F are absent.
- HarfBuzz shapes Mono ligatures like upstream Iosevka SS17, while Term Slab does not substitute glyphs.

## Updates

GitHub Actions checks upstream weekly. New releases of Sarasa Gothic, Nerd Fonts, or the local `font-iosevka-term-slab-ss17` cask trigger a rebuild. Iosevka SS17 for Mono follows the base Iosevka version of the Term Slab donor. The cask version joins all three source versions (for example, `1.0.41-34.7.0-r2-3.5.1`).

## Install

### Homebrew (pending publication)

Once the release workflow publishes the bundle, install the cask:

```bash
brew tap sidkang/homebrew https://github.com/sidkang/homebrew
brew install --cask font-sarasa-ss17-sc-nerd-font
```

The existing single-family cask `font-sarasa-term-slab-ss17-sc-nerd-font` remains live until the automated release workflow publishes the new asset and migrates the cask.

### Manual install

Install built TTC files directly into `~/Library/Fonts`:

```bash
fonts/sarasa-ss17-sc-nerd-font/install.sh SarasaTermSlabSS17SCNF.ttc SarasaMonoSS17SCNF.ttc
```

## Kitty configuration

For Term Slab (no ligatures):

```conf
font_family Sarasa Term Slab SS17 SC Nerd Font
symbol_map U+F800-U+F83F Braille Spinner Kitty Term
narrow_symbols U+F800-U+F83F 1
```

For Mono (with ligatures):

```conf
font_family Sarasa Mono SS17 SC Nerd Font
symbol_map U+F800-U+F83F Braille Spinner Kitty Term
narrow_symbols U+F800-U+F83F 1
```

Remove separate `symbol_map` lines for Sarasa, Iosevka, or Nerd Fonts. Restart Kitty after installation.

## License

`Sarasa` is not a reserved font name. `Source` is reserved by Adobe and is not used in these font names. Third-party licenses and notices are in `licenses/`.
