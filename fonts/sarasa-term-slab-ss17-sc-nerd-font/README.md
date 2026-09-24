# Sarasa Term Slab SS17 SC Nerd Font

Sarasa Term Slab SC, with its Latin and terminal symbols replaced by Iosevka Term Slab SS17, plus the IosevkaTerm Nerd Font Mono private-use icons. The Braille spinner range is left empty.

Sarasa Term Slab is already Iosevka Term Slab plus Source Han Sans. SS17 is the Latin variant Sarasa does not ship. Nerd Font is the icon patch. The name follows that order: Sarasa style, SS17, SC orthography, then the Nerd Font suffix. `Term` stays because this is the terminal-width Sarasa, not Mono or Fixed.

## Ranges

| Code points | Source |
| --- | --- |
| U+0020–U+024F, U+1E00–U+1EFF, U+2000–U+23FF, U+2500–U+27BF, U+2B00–U+2BFF | Iosevka Term Slab SS17 |
| U+E000–U+F7FF, U+F840–U+F8FF, U+F0000–U+FFFFD | IosevkaTerm Nerd Font Mono |
| everything else, including CJK | Sarasa Term Slab SC |
| U+F800–U+F83F | absent; use Braille Spinner Kitty Term |

The six faces are Regular, Semibold, Bold, Italic, Semibold Italic, and Bold Italic.

## Updates

GitHub Actions checks upstream once a week. A new Sarasa Gothic release, a new Iosevka Term Slab SS17 release from this tap, or a new Nerd Fonts release rebuilds the font. The cask version is those three versions joined together, for example `1.0.41,34.7.0,3.5.1`. Nothing is rebuilt when they are unchanged.

## Kitty

```text
font_family Sarasa Term Slab SS17 SC Nerd Font
symbol_map U+F800-U+F83F Braille Spinner Kitty Term
narrow_symbols U+F800-U+F83F 1
```

Remove separate Sarasa, Iosevka, and Nerd Font `symbol_map` lines. Quit and reopen Kitty after installing.

## Install

```bash
brew install --cask sidkang/fonts/font-sarasa-term-slab-ss17-sc-nerd-font
```

## License

`Sarasa` is not a reserved font name. `Source` is, and this family does not use it. Upstream notices are in `licenses/`.
