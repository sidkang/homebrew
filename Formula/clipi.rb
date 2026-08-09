class Clipi < Formula
  desc "Local-only MCP browser service with a Chrome Extension bridge"
  homepage "https://git.882816.xyz/sid/clipi"
  version "0.5.8"

  depends_on arch: :arm64
  depends_on :macos

  on_macos do
    on_arm do
      url "https://git.882816.xyz/sid/clipi/releases/download/v#{version}/clipi-#{version}-darwin-arm64.tar.gz"
      sha256 "a321f3faa4b9c63bf81d36e2082df844b8b923426700f6232290449760e3cf14"

      v = version
      resource "chrome_extension" do
        url "https://git.882816.xyz/sid/clipi/releases/download/v#{v}/clipi-extension-chrome-mv3-#{v}.zip"
        sha256 "3fe63c4c6b98f0fb6140bccfe157bb76e4c9220201d7d959cb3c85cfa4d9d428"
      end
    end
  end

  def install
    bin.install "clipi", "clipi-admin", "clipi-server"

    resource("chrome_extension").stage do
      pkgshare.install Dir["*"]
    end
  end

  def post_install
    # Chrome Load unpacked realpath()s the selected path. Stage a complete tree
    # into a non-versioned real directory under Homebrew var so upgrades only
    # require Reload. Uninstall intentionally leaves this directory in place.
    source = pkgshare
    odie "clipi: packaged Extension is missing manifest.json" unless (source/"manifest.json").file?

    parent = var/"clipi"
    target = parent/"extension"
    stage = parent/".extension.stage.#{Process.pid}"
    backup = parent/".extension.backup.#{Process.pid}"

    mkdir_p parent
    rm_r stage if stage.exist?
    rm_r backup if backup.exist?
    mkdir stage

    begin
      source.each_child do |child|
        cp_r child, stage
      end
      odie "clipi: staged Extension is incomplete" unless (stage/"manifest.json").file?

      mv target, backup if target.exist? || target.symlink?
      begin
        mv stage, target
      rescue
        rm_r target if target.exist? || target.symlink?
        mv backup, target if backup.exist?
        raise
      end
      rm_r backup if backup.exist?
    ensure
      rm_r stage if stage.exist?
    end
  end

  service do
    run [opt_bin/"clipi-server"]
    keep_alive true
    log_path var/"log/clipi.log"
    error_log_path var/"log/clipi.log"
  end

  def caveats
    <<~EOS
      Load the bundled Chrome Extension once from this fixed real directory
      (not a Cellar or opt path; Chrome realpath()s unpacked Extension roots):

        1. Open chrome://extensions.
        2. Enable Developer mode.
        3. Select "Load unpacked".
        4. Select: #{var}/clipi/extension

      After every `brew upgrade clipi`, click Reload on that same Extension entry.
      Do not re-select a versioned Cellar path.

      Start the local service:
        brew services start clipi

      Then verify that Chrome has connected:
        clipi system.status --input '{}'

      Homebrew manages this installation. Do not use `clipi-admin install`,
      `upgrade`, or `rollback`; upgrade with `brew upgrade clipi` instead.
      Uninstall leaves #{var}/clipi/extension in place.
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/clipi --version")
    assert_match version.to_s, shell_output("#{bin}/clipi-admin --version")
    assert_match version.to_s, shell_output("#{bin}/clipi-server --version")
    assert_path_exists var/"clipi/extension/manifest.json"
  end
end
