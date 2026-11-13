# Hermes Desktop App

Unpacked macOS Apple Silicon build of [Hermes Desktop](https://github.com/NousResearch/hermes-agent/tree/main/apps/desktop), produced with the official `pnpm run pack` path. This is the Electron app (`Hermes.app`), not the website Setup installer.

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

## Signing

The build has no Developer ID and is not notarized. electron-builder alone is
not enough: with no signing identity it leaves Electron's own linker signature
on the repacked bundle, so `codesign --verify` fails and macOS reports a
quarantined install as "damaged" (offering only Move to Trash). `build.sh`
therefore re-signs the staged app adhoc (`codesign --force --deep --sign -`)
whenever the packed signature does not describe the bundle, and `verify.sh`
asserts `codesign --verify --deep --strict` passes.

The result is a self-consistent adhoc signature: macOS treats it as an
unidentified developer, which the user can approve, instead of as corrupt.

## Build

Required toolchain matches upstream CI: Node 26, Xcode CLT, and the pnpm version
pinned in the upstream `pm/lock.json` (12.15.0 for Hermes 0.23.1). The upstream
root `preinstall` hook refuses every other pnpm, so `build.sh` checks the
installed version against that pin before it touches the checkout.

From a macOS Apple Silicon machine, with the official source checked out:

```bash
export HERMES_SOURCE=/path/to/hermes-agent
export VERSION=0.23.1   # upstream tag without the leading v
npm i -g pnpm@12.15.0   # the version pinned in $HERMES_SOURCE/pm/lock.json
tools/hermes-desktop/build.sh
tools/hermes-desktop/verify.sh
```

The pack command `build.sh` runs inside the checkout is:

```bash
node scripts/build/node-deps.mjs --source . --reuse --workspace apps/desktop
pnpm --filter hermes run pack    # unpacked app, no installer
```

The first command is upstream's own preparation step: it installs the locked
workspace graph and prepares the Electron binary. A bare `pnpm install` leaves
the packager without a runtime and fails at `electron-builder`.
