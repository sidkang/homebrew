cask "font-sarasa-ss17-sc-nerd-font" do
  version "1.0.42-34.7.0-r2-3.5.1"
  sha256 "0b4b79108d4f81fa9d4463fd2fd3d03b6cd6744b533964c79f12edb102ef13d1"

  url "https://github.com/sidkang/homebrew/releases/download/sarasa-ss17-sc-nerd-font-v#{version}/SarasaSS17SCNF-#{version}.zip"
  name "Sarasa SS17 SC Nerd Font"
  desc "Sarasa Term Slab and Mono SC with SS17 Latin and Nerd Font icons"
  homepage "https://github.com/sidkang/homebrew/tree/master/fonts/sarasa-ss17-sc-nerd-font"

  livecheck do
    skip "Rebuilt weekly from Sarasa, Iosevka Term Slab SS17, Iosevka, and Nerd Fonts"
  end

  font "SarasaTermSlabSS17SCNF.ttc"
  font "SarasaMonoSS17SCNF.ttc"
end
