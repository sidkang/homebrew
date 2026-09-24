# Term Slab SC SS17

One terminal face for the Kitty setup that used three fonts. Sarasa Term Slab SC stays the CJK base. Iosevka Term Slab SS17 replaces the Latin and symbol ranges Kitty mapped to it. IosevkaTerm Nerd Font Mono supplies the private-use icons. The Braille spinner range is removed so the separate spinner font can still own it.

Sarasa is already a composite: Iosevka Term Slab plus Source Han Sans, with Sarasa's own punctuation widths. Rebuilding Sarasa would keep that punctuation policy. This font instead copies only the ranges Kitty overrides.

## Ranges

| Code points | Source |
| --- | --- |
| U+0020–U+024F, U+1E00–U+1EFF, U+2000–U+23FF, U+2500–U+27BF, U+2B00–U+2BFF | Iosevka Term Slab SS17 34.7.0 |
| U+E000–U+F7FF, U+F840–U+F8FF, U+F0000–U+FFFFD | IosevkaTerm Nerd Font Mono 3.5.1 |
| everything else, including CJK | Sarasa Term Slab SC 1.0.41 |
| U+F800–U+F83F | absent; use Braille Spinner Kitty Term |

The six faces are Regular, Semibold, Bold, Italic, Semibold Italic, and Bold Italic. A face is used only when its family, OS/2 weight, and italic bit match. There is no weight fallback.

## Kitty

```text
font_family Term Slab SC SS17
symbol_map U+F800-U+F83F Braille Spinner Kitty Term
narrow_symbols U+F800-U+F83F 1
```

Remove the old Sarasa, Iosevka, and Nerd `symbol_map` lines. Quit and reopen Kitty after installing.

## Install

Download `TermSlabSCSS17-1.0.0.zip` from a GitHub Release, then:

```bash
fonts/term-slab-sc-ss17/install.sh TermSlabSCSS17.ttc
```

The file lands in `~/Library/Fonts/TermSlabSCSS17.ttc`.

## Build

GitHub Actions is the supported build. It downloads the three pinned archives, checks their SHA-256 values, grafts the glyphs, and verifies every codepoint in the mapped ranges.

## License

The result is a modified font. Its family name is `Term Slab SC SS17`, which avoids the reserved name `Source`. Upstream notices are in `licenses/`:

- Iosevka, SIL OFL 1.1
- Sarasa Gothic, SIL OFL 1.1, including the reserved name `Source`
- Nerd Fonts, SIL OFL 1.1 for the patched font
