cask "hermes-desktop-app" do
  version "0.23.1"
  sha256 "dca2ddbede828d8fde73e132fe72fa644a71f25dee82bae2fff5eb5f4d995a35"

  url "https://github.com/sidkang/homebrew/releases/download/hermes-desktop-v#{version}/Hermes-mac-arm64-#{version}.zip"
  name "Hermes Desktop App"
  desc "Unpacked Hermes Agent desktop app without the Setup installer"
  homepage "https://github.com/NousResearch/hermes-agent"

  livecheck do
    url "https://github.com/sidkang/homebrew/releases?q=hermes-desktop"
    regex(/hermes-desktop-v?(\d+(?:\.\d+)+)/i)
  end

  conflicts_with cask: "hermes-desktop"
  depends_on arch: :arm64
  depends_on :macos

  app "Hermes.app"

  uninstall quit: "com.nousresearch.hermes"

  zap trash: [
    "~/Library/Application Support/Hermes",
    "~/Library/Caches/com.nousresearch.hermes",
    "~/Library/Logs/Hermes",
    "~/Library/Preferences/com.nousresearch.hermes.plist",
    "~/Library/Saved Application State/com.nousresearch.hermes.savedState",
  ]

  caveats <<~EOS
    This is the unpacked Desktop app from `pnpm run pack`, not the official
    Hermes-Setup installer. It is signed adhoc, not with a Developer ID, so
    macOS blocks the first launch as an unidentified developer. Install with:

      brew install --cask --no-quarantine hermes-desktop-app

    Upgrading a cask takes no `--no-quarantine` flag, so after an upgrade
    approve the app in System Settings → Privacy & Security, or clear the
    quarantine flag directly:

      xattr -cr #{appdir}/Hermes.app

    The official `hermes-desktop` cask installs Setup and cannot be
    installed at the same time because both provide Hermes.app.
  EOS
end
