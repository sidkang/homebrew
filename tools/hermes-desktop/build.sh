#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Hermes Desktop pack must run on macOS." >&2
  exit 1
fi

MODULE_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$MODULE_DIR/../.." && pwd)
HERMES_SOURCE=${HERMES_SOURCE:-"$REPO_ROOT/.upstream/hermes-agent"}
VERSION=${VERSION:?VERSION is required (upstream tag without a leading v)}
UPSTREAM_TAG=${UPSTREAM_TAG:-"v${VERSION}"}

if [[ ! -f "$HERMES_SOURCE/package.json" || ! -f "$HERMES_SOURCE/apps/desktop/package.json" ]]; then
  echo "HERMES_SOURCE is not a hermes-agent checkout: $HERMES_SOURCE" >&2
  exit 1
fi

DIST_ROOT="$REPO_ROOT/dist"
RELEASE_DIR="$DIST_ROOT/releases"
CASK_DIR="$DIST_ROOT/casks"
STAGE_DIR="$DIST_ROOT/hermes-desktop"
APP_NAME="Hermes.app"
ZIP_NAME="Hermes-mac-arm64-${VERSION}.zip"

rm -rf "$STAGE_DIR"
mkdir -p "$RELEASE_DIR" "$CASK_DIR" "$STAGE_DIR"

UPSTREAM_COMMIT=$(git -C "$HERMES_SOURCE" rev-parse HEAD)
export GITHUB_SHA="$UPSTREAM_COMMIT"
export GITHUB_REF_NAME="$UPSTREAM_TAG"
export CI=1

(
  cd "$HERMES_SOURCE"
  npm ci
  npm --prefix apps/desktop run pack
)

RELEASE_ROOT="$HERMES_SOURCE/apps/desktop/release"
APP_PATH=""
if [[ -d "$RELEASE_ROOT/mac-arm64/$APP_NAME" ]]; then
  APP_PATH="$RELEASE_ROOT/mac-arm64/$APP_NAME"
elif [[ -d "$RELEASE_ROOT/mac/$APP_NAME" ]]; then
  APP_PATH="$RELEASE_ROOT/mac/$APP_NAME"
else
  echo "Pack did not produce $APP_NAME under $RELEASE_ROOT" >&2
  find "$RELEASE_ROOT" -name "$APP_NAME" -prune 2>/dev/null || true
  exit 1
fi

ditto "$APP_PATH" "$STAGE_DIR/$APP_NAME"
cp "$HERMES_SOURCE/LICENSE" "$STAGE_DIR/LICENSE"
cp "$MODULE_DIR/README.md" "$STAGE_DIR/README.md"

python3 - <<PY
import json
from pathlib import Path

Path("$STAGE_DIR/BUILD-INFO.json").write_text(
    json.dumps(
        {
            "upstream_repository": "NousResearch/hermes-agent",
            "upstream_tag": "$UPSTREAM_TAG",
            "upstream_commit": "$UPSTREAM_COMMIT",
            "version": "$VERSION",
            "pack_command": "npm run pack",
            "app": "Hermes.app",
        },
        indent=2,
    )
    + "\n"
)
PY

(
  cd "$STAGE_DIR"
  ditto -c -k . "$RELEASE_DIR/$ZIP_NAME"
)

SHA256=$(shasum -a 256 "$RELEASE_DIR/$ZIP_NAME" | awk '{print $1}')
python3 - <<PY
from pathlib import Path

template = Path("$MODULE_DIR/cask.rb.in").read_text()
Path("$CASK_DIR/hermes-desktop-app.rb").write_text(
    template.replace("__VERSION__", "$VERSION").replace("__SHA256__", "$SHA256")
)
PY

echo "Built $RELEASE_DIR/$ZIP_NAME"
echo "sha256=$SHA256"
echo "upstream_commit=$UPSTREAM_COMMIT"
