cask "hermes-desktop-app" do
  version "0.22.0"
  sha256 "474cd19c83f2efd610011b89e12faf5c707e6ebf24e9851297626cf59da669de"

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
    This is the unpacked Desktop app from `npm run pack`, not the official
    Hermes-Setup installer. The build is unsigned, so install with:

      brew install --cask --no-quarantine hermes-desktop-app

    If Gatekeeper still blocks it:

      xattr -cr #{appdir}/Hermes.app

    The official `hermes-desktop` cask installs Setup and cannot be
    installed at the same time because both provide Hermes.app.
  EOS
end
