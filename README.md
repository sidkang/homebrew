# Fonts and Tools

Personal font source, verified GitHub releases, and a Homebrew tap for formulae and casks in one repository. The GitHub repository is [`sidkang/homebrew`](https://github.com/sidkang/homebrew). The tap remains available as `sidkang/fonts` because Homebrew clones `homebrew-fonts`, which GitHub redirects here. User-visible release changes are recorded in [`CHANGELOG.md`](CHANGELOG.md).

## Install

Formulae will be installed directly once published:

```bash
brew install sidkang/fonts/<formula>
```

Install a released font cask directly:

```bash
brew install --cask sidkang/fonts/font-braille-spinner-kitty-term
```

Install the unpacked Hermes Desktop app cask (not a font, and not the official Setup cask):

```bash
brew tap sidkang/homebrew https://github.com/sidkang/homebrew
brew uninstall --cask hermes-desktop
brew install --cask --no-quarantine hermes-desktop-app
```

Or add the fonts tap first:

```bash
brew tap sidkang/fonts
brew install --cask font-braille-spinner-kitty-term
```

## Available formulae

| Formula | Tool |
| --- | --- |
| `clipi` | Local-only MCP browser service with a Chrome Extension bridge |

## Available casks

| Cask | Package |
| --- | --- |
| `font-braille-spinner-kitty-term` | Braille Spinner Kitty Term |
| `font-iosevka-term-slab-ss17` | Iosevka Term Slab SS17 |
| `hermes-desktop-app` | Unpacked Hermes Desktop (`Hermes.app`) |

## Builds and releases

GitHub Actions is the only supported build path. Each font module owns its build implementation, verifier, installer for downloaded artifacts, font license, and documentation.

A version tag is the release signal for fonts. Pushing one automatically builds, verifies, creates the GitHub Release, computes the asset SHA-256, and updates the matching cask:

```text
braille-spinner-kitty-term-v1.0.2
iosevka-term-slab-ss17-v34.7.1
```

Hermes Desktop is different: a scheduled workflow checks [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) every six hours, packs `Hermes.app` with official `npm run pack`, and publishes `hermes-desktop-v<upstream-version>`.

Normal pushes to `master` only verify; they do not release. A cask always points at an immutable release asset, never an ephemeral CI artifact. Formulae use immutable, versioned source or release archives with a SHA-256.

## Repository layout

```text
Formula/                # Homebrew formulae for non-font command-line tools
Casks/                  # Homebrew casks
fonts/<module>/         # font source, verifier, installer, and license
tools/hermes-desktop/   # unpacked Hermes Desktop pack and cask generator

.github/workflows/      # module-specific verification and release workflows
LICENSE                 # MIT for repository code and configuration
```

## Licenses

Repository code and configuration are licensed under the [MIT License](LICENSE). Each font is licensed separately under the SIL Open Font License 1.1; see its module's `OFL.txt`.
