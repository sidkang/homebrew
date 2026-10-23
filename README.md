# Fonts and Tools

Personal font source, verified GitHub releases, and a Homebrew tap for formulae and casks in one repository. The GitHub repository is [`sidkang/homebrew`](https://github.com/sidkang/homebrew). The tap remains available as `sidkang/fonts` because Homebrew clones `homebrew-fonts`, which GitHub redirects here. User-visible release changes are recorded in [`CHANGELOG.md`](CHANGELOG.md).

## Install

Install a published formula:

```bash
brew install sidkang/fonts/<formula>
```

Install a released font cask:

```bash
brew install --cask sidkang/fonts/font-braille-spinner-kitty-term
```

Sarasa SS17 SC Nerd Font bundles two families: `Sarasa Term Slab SS17 SC Nerd Font` and `Sarasa Mono SS17 SC Nerd Font`. The current published cask is `font-sarasa-term-slab-ss17-sc-nerd-font`. Once the bundle release publishes, the cask becomes `font-sarasa-ss17-sc-nerd-font`, and Homebrew migrates existing installs via `cask_renames.json`:

```bash
brew tap sidkang/homebrew https://github.com/sidkang/homebrew
brew install --cask font-sarasa-ss17-sc-nerd-font
```

Restart applications after installing so they detect the new fonts.

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
| `font-iosevka-term-slab-ss17` | Iosevka Term Slab SS17 (10-face release pending) |
| `font-sarasa-term-slab-ss17-sc-nerd-font` | Sarasa Term Slab SC with SS17 Latin and Nerd Font icons (published) |
| `font-sarasa-ss17-sc-nerd-font` (pending release) | Sarasa Term Slab and Mono SC with SS17 Latin and Nerd Font icons (bundles both families) |
| `hermes-desktop-app` | Unpacked Hermes Desktop (`Hermes.app`) |

## Builds and releases

GitHub Actions is the only supported build path. Each font module manages its own build, verification, installer, font license, and documentation.

Pushing a version tag triggers the release workflow for tagged fonts. The workflow builds the font, verifies it, creates a GitHub Release, calculates the SHA-256 digest, and updates the cask:

```text
braille-spinner-kitty-term-v1.0.2
iosevka-term-slab-ss17-v34.7.0-r2
```

Hermes Desktop runs on a schedule: a workflow checks [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) every six hours, packs `Hermes.app` with `npm run pack`, and publishes `hermes-desktop-v<upstream-version>`.

Sarasa SS17 SC Nerd Font rebuilds on a schedule instead of git tags. A weekly workflow checks upstream releases for Sarasa Gothic and Nerd Fonts, plus the local `font-iosevka-term-slab-ss17` cask version. When upstream publishes new releases, the workflow creates `sarasa-ss17-sc-nerd-font-v<version>`. The version string combines all three component versions (for example, `1.0.41-34.7.0-r2-3.5.1`). The official Iosevka SS17 donor matches the base Iosevka version of the Term Slab cask. Releases are immutable; rebuilding against unchanged upstream releases requires running the workflow manually with a `revision` input, which appends `-r<revision>`. The workflow adds the new cask, removes `font-sarasa-term-slab-ss17-sc-nerd-font.rb`, and records the rename in `cask_renames.json` in the same commit.

Pushes to `master` run verification only; they do not publish releases. Casks reference immutable release assets, never temporary CI artifacts. Formulae reference immutable versioned source or release archives with SHA-256 digests.

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
