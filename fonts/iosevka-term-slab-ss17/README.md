# Iosevka Term Slab SS17

A custom [Iosevka](https://github.com/be5invis/Iosevka) terminal font combining three upstream options:

```text
Term  → terminal-width arrows and geometric symbols
Slab  → slab-serif Latin glyphs
SS17  → Recursive Mono-style character variants
```

## Naming and scope

The family follows Iosevka naming conventions:

```text
Iosevka Term Slab
Iosevka Term SS17
Iosevka Term Slab SS17  ← this combination
```

Upstream packages provide the first two combinations, but not both together.

This build generates ten faces covering five weights and two slopes:

```text
Extralight        Extralight Italic
Light             Light Italic
Regular           Italic
Semibold          Semibold Italic
Bold              Bold Italic
```

All ten faces are packaged into a single TrueType Collection (`IosevkaTermSlabSS17.ttc`).
The build plan inherits official `Iosevka Term SS17` settings with slab-serif geometry added.

## Source and toolchain

Source is pinned to upstream commit `6828cb0bd569992bb19565a5e448540de3b50541` (`v34.7.0`).

The build container uses `node:22-bookworm-slim` and Debian Bookworm's `ttfautohint`. The build script records the source commit timestamp, installs dependencies without lifecycle scripts, and compiles offline with at most two build jobs.

## Build

GitHub Actions is the supported build path. It checks out the pinned commit, builds the TTC inside Docker, verifies font tables and metrics, and uploads a workflow artifact.

Local builds are not supported.

## Versions

Upstream version is `34.7.0`. The published release `34.7.0` provides six faces. The ten-face collection is prepared as `34.7.0-r2` (tag `iosevka-term-slab-ss17-v34.7.0-r2`), pending publication.

Release assets are immutable. The release workflow never overwrites an existing release asset; if the release tag exists, it updates the Homebrew cask using the published asset's SHA-256.

## Outputs

```text
dist/iosevka-term-slab-ss17/
├── IosevkaTermSlabSS17.ttc
└── BUILD-INFO.json

dist/releases/IosevkaTermSlabSS17-34.7.0-r2.zip
```

The verifier checks build and collection plans, validates all ten faces, checks name metadata, weight classes, required OpenType tables, and ASCII and symbol advances, and records SHA-256 provenance in `BUILD-INFO.json`.

## Installation

### Homebrew

The published cask currently provides the six-face `34.7.0` release:

```bash
brew install --cask sidkang/fonts/font-iosevka-term-slab-ss17
```

Once `34.7.0-r2` publishes, the cask updates to the ten-face collection.

### Manual install

Download `IosevkaTermSlabSS17-34.7.0-r2.zip` from a CI artifact or GitHub Release, extract it, and run:

```bash
fonts/iosevka-term-slab-ss17/install.sh IosevkaTermSlabSS17.ttc
```

This installs to:

```text
~/Library/Fonts/IosevkaTermSlabSS17.ttc
```

Restart Kitty after installing or updating the font.

### Kitty configuration

Use the family and let Kitty select linked faces:

```conf
font_family Iosevka Term Slab SS17
bold_font auto
italic_font auto
bold_italic_font auto
```

To use Semibold as the bold weight instead of Bold:

```conf
bold_font Iosevka Term Slab SS17 Semibold
bold_italic_font Iosevka Term Slab SS17 Semibold Italic
```

## License

The font is licensed under the SIL Open Font License 1.1. See [`OFL.txt`](OFL.txt). Build scripts and orchestration use the root MIT license.
