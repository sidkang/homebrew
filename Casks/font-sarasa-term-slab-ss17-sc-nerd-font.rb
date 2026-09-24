cask "font-sarasa-term-slab-ss17-sc-nerd-font" do
  version "1.0.41-34.7.0-3.5.1"
  sha256 "d47bd1992e2e5eaa632dfaebc58e915497be86a197b489353ac67e77a81111f8"

  url "https://github.com/sidkang/homebrew/releases/download/sarasa-term-slab-ss17-sc-nerd-font-v#{version}/SarasaTermSlabSS17SCNF-#{version}.zip"
  name "Sarasa Term Slab SS17 SC Nerd Font"
  desc "Sarasa Term Slab SC with SS17 Latin and Nerd Font icons"
  homepage "https://github.com/sidkang/homebrew/tree/master/fonts/sarasa-term-slab-ss17-sc-nerd-font"

  livecheck do
    skip "Rebuilt weekly from Sarasa, Iosevka Term Slab SS17, and Nerd Fonts"
  end

  font "SarasaTermSlabSS17SCNF.ttc"
end
