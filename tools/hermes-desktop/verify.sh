#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Hermes Desktop verification must run on macOS." >&2
  exit 1
fi

MODULE_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$MODULE_DIR/../.." && pwd)
VERSION=${VERSION:?VERSION is required (upstream tag without a leading v)}
ZIP=${1:-"$REPO_ROOT/dist/releases/Hermes-mac-arm64-${VERSION}.zip"}
CASK=${2:-"$REPO_ROOT/dist/casks/hermes-desktop-app.rb"}

if [[ ! -f "$ZIP" ]]; then
  echo "Missing release zip: $ZIP" >&2
  exit 1
fi
if [[ ! -f "$CASK" ]]; then
  echo "Missing generated cask: $CASK" >&2
  exit 1
fi

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT
ditto -x -k "$ZIP" "$WORKDIR"

APP="$WORKDIR/Hermes.app"
BIN="$APP/Contents/MacOS/Hermes"
PLIST="$APP/Contents/Info.plist"

test -d "$APP"
test -x "$BIN"
test -f "$WORKDIR/LICENSE"
test -f "$WORKDIR/README.md"
test -f "$WORKDIR/BUILD-INFO.json"

IDENTIFIER=$(plutil -extract CFBundleIdentifier raw "$PLIST")
EXECUTABLE=$(plutil -extract CFBundleExecutable raw "$PLIST")
ARCHS=$(lipo -archs "$BIN")
test "$IDENTIFIER" = "com.nousresearch.hermes"
test "$EXECUTABLE" = "Hermes"
[[ "$ARCHS" == *arm64* ]]

python3 - <<PY
import json
from pathlib import Path

info = json.loads(Path("$WORKDIR/BUILD-INFO.json").read_text())
print("BUILD-INFO.json:", json.dumps(info, indent=2))
assert info["upstream_repository"] == "NousResearch/hermes-agent", info
assert info["version"] == "$VERSION", info
assert info["upstream_tag"] in {"$VERSION", "v$VERSION"}, info
assert info["pack_command"] == "npm run pack", info
assert len(info["upstream_commit"]) == 40, info
PY

SHA256=$(shasum -a 256 "$ZIP" | awk '{print $1}')
python3 - <<PY
from pathlib import Path

text = Path("$CASK").read_text()
print(text)
assert 'cask "hermes-desktop-app"' in text
assert 'version "$VERSION"' in text
assert 'sha256 "$SHA256"' in text
assert "hermes-desktop-v#{version}" in text
assert "Hermes-mac-arm64-#{version}.zip" in text
assert 'app "Hermes.app"' in text
assert Path("$CASK").name == "hermes-desktop-app.rb"
PY

echo "Verified $ZIP"
