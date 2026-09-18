# Hermes Desktop App

Unpacked macOS Apple Silicon build of [Hermes Desktop](https://github.com/NousResearch/hermes-agent/tree/main/apps/desktop), produced with the official `npm run pack` path. This is the Electron app (`Hermes.app`), not the website Setup installer.

GitHub Actions watches [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) releases every six hours, packs the tagged source, and publishes a cask in this tap.

## Install

Uninstall the official Setup cask first if it is present; both install `Hermes.app`:

```bash
brew tap sidkang/homebrew https://github.com/sidkang/homebrew
brew uninstall --cask hermes-desktop
brew install --cask --no-quarantine hermes-desktop-app
```

The build is unsigned. `--no-quarantine` avoids Gatekeeper on install. If macOS still blocks it:

```bash
xattr -cr /Applications/Hermes.app
```

## What you get

The zip contains:

- `Hermes.app` — official unpacked Desktop shell
- `LICENSE` — MIT from Nous Research
- `README.md` — this file
- `BUILD-INFO.json` — upstream tag and commit used for the pack

On first launch the app can connect to an existing Hermes gateway or install a local runtime into `~/.hermes`. That is Desktop onboarding, not `Hermes-Setup.dmg`.

## Build

From a macOS Apple Silicon machine, with the official source checked out:

```bash
export HERMES_SOURCE=/path/to/hermes-agent
export VERSION=2026.9.14   # upstream tag without the leading v
tools/hermes-desktop/build.sh
tools/hermes-desktop/verify.sh
```

Required toolchain matches upstream CI: Node 26, npm 12, Xcode CLT. The pack command is:

```bash
npm ci                 # repository root
cd apps/desktop
npm run pack           # unpacked app, no installer
```
