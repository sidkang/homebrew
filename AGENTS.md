# Repository scope

This repository is the source, release, and Homebrew tap for personal fonts and tools.

## Layout

- Font modules live in `fonts/<font-slug>/` and own their build implementation, verification, installer, public documentation, and font license.
- Non-font app modules live in `tools/<slug>/` and own their build implementation, verification, public documentation, and release workflow.
- Homebrew formulae live in `Formula/`, package non-font command-line tools, and own their build, release, and verification.
- Homebrew casks live in `Casks/`. Font cask names MUST start with `font-`. The unpacked Hermes Desktop cask is `hermes-desktop-app`.
- Formulae MUST NOT reuse a cask name or shadow a formula in `homebrew/core`. Casks MUST NOT reuse a `homebrew/cask` name.
- Root documentation and workflows apply across modules. Do not add root build/install dispatchers or a central module registry.

## Build and release

- GitHub Actions is the supported build path. Generated files belong under `dist/` and MUST NOT be committed.
- Use `uv` and inline Python script metadata; do not add a repository-wide virtual environment.
- Font builds MUST verify family names, codepoints, advances, and font validity before packaging.
- Hermes Desktop builds MUST pack the official unpacked app (`npm run pack`), then verify the app identity, architecture, license, and generated cask.
- Release archives MUST include the product file, its module README, and its license.
- Formulae MUST reference immutable, versioned source or release archives and include their SHA-256.
- Casks MUST reference immutable versioned GitHub release assets in this repository. Generate their SHA-256 from the published asset.
- Test formula and cask changes with `brew style` and the corresponding `brew audit` mode before publishing.

## Licenses

- Repository code and configuration use the root MIT `LICENSE`.
- Each font module must include its applicable font license, normally `OFL.txt`.

## Version control

- This is a Jujutsu repository. Use `jj`, not raw Git commands.
- Publish through the `master` bookmark.
