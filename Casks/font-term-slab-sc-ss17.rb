cask "font-term-slab-sc-ss17" do
  version "1.0.0"
  sha256 "325b0faa8a72bf794a303f45e87efb754dde9358f378b4217ff6100a3ba0dc29"

  url "https://github.com/sidkang/homebrew/releases/download/term-slab-sc-ss17-v#{version}/TermSlabSCSS17-#{version}.zip"
  name "Term Slab SC SS17"
  desc "Sarasa Term Slab SC with Iosevka SS17 Latin and Nerd Font icons"
  homepage "https://github.com/sidkang/homebrew/tree/master/fonts/term-slab-sc-ss17"

  livecheck do
    url "https://github.com/sidkang/homebrew/releases?q=term-slab-sc-ss17"
    regex(/term-slab-sc-ss17[._-]v?(\d+(?:\.\d+)+)/i)
  end

  font "TermSlabSCSS17.ttc"
end
