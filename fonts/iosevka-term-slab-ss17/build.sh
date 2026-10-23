#!/usr/bin/env bash
set -euo pipefail

MODULE_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$MODULE_DIR/../.." && pwd)
UPSTREAM_REVISION="6828cb0bd569992bb19565a5e448540de3b50541"
VERSION="34.7.0"
# Releases are immutable. Rebuilding an upstream version with a changed font
# set requires an incremented revision: "$VERSION-r$RELEASE_REVISION".
RELEASE_REVISION=2
RELEASE_VERSION="$VERSION-r$RELEASE_REVISION"
PLAN="IosevkaTermSlabSS17"
SOURCE_DIR=${IOSEVKA_SOURCE:-"$HOME/.cache/checkouts/github.com/be5invis/Iosevka"}
JOBS=${IOSEVKA_JOBS:-2}
OUTPUT_DIR="$REPO_ROOT/dist/iosevka-term-slab-ss17"
ARCHIVE="$REPO_ROOT/dist/releases/IosevkaTermSlabSS17-$RELEASE_VERSION.zip"
IMAGE="sidkang/fonts-iosevka-builder:34.7.0"

if ! [[ "$JOBS" =~ ^[1-9][0-9]*$ ]]; then
  echo "IOSEVKA_JOBS must be a positive integer." >&2
  exit 2
fi
if ! command -v docker >/dev/null; then
  echo "Docker is required to build $PLAN." >&2
  exit 1
fi
if ! command -v git >/dev/null; then
  echo "Git is required to read the pinned Iosevka source revision." >&2
  exit 1
fi
if ! git -C "$SOURCE_DIR" cat-file -e "$UPSTREAM_REVISION^{tree}" 2>/dev/null; then
  cat >&2 <<EOF
Iosevka source $UPSTREAM_REVISION is unavailable in: $SOURCE_DIR
Provide a checkout containing this revision, for example:
  git clone --filter=blob:none https://github.com/be5invis/Iosevka.git /tmp/iosevka
  git -C /tmp/iosevka fetch --depth=1 origin $UPSTREAM_REVISION
  IOSEVKA_SOURCE=/tmp/iosevka fonts/iosevka-term-slab-ss17/build.sh
EOF
  exit 1
fi

source_date_epoch=$(git -C "$SOURCE_DIR" show -s --format=%ct "$UPSTREAM_REVISION")
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/iosevka-term-slab-ss17.XXXXXX")
trap 'rm -rf "$work_dir"' EXIT
source_copy="$work_dir/iosevka"

mkdir -p "$source_copy"
git -C "$SOURCE_DIR" archive "$UPSTREAM_REVISION" | tar -x -C "$source_copy"
cp "$MODULE_DIR/private-build-plans.toml" "$source_copy/private-build-plans.toml"

docker build --tag "$IMAGE" "$MODULE_DIR/toolchain"

# Install dependencies. Build step below runs with network disabled.
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --env HOME=/tmp \
  --env npm_config_cache=/tmp/npm-cache \
  --volume "$work_dir:/work" \
  "$IMAGE" \
  bash -lc "npm ci --ignore-scripts"

docker run --rm \
  --network none \
  --user "$(id -u):$(id -g)" \
  --env HOME=/tmp \
  --env SOURCE_DATE_EPOCH="$source_date_epoch" \
  --env TZ=UTC \
  --env LC_ALL=C \
  --volume "$work_dir:/work" \
  "$IMAGE" \
  bash -lc "npm run build -- super-ttc::$PLAN --jCmd=$JOBS"

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
source_font="$source_copy/dist/.super-ttc/$PLAN.ttc"
if [[ ! -f "$source_font" ]]; then
  echo "Build output not found: $source_font" >&2
  exit 1
fi
output_font="$OUTPUT_DIR/$PLAN.ttc"
cp "$source_font" "$output_font"

uv run "$MODULE_DIR/verify.py" \
  --font "$output_font" \
  --module-dir "$MODULE_DIR" \
  --upstream-build-plans "$source_copy/build-plans.toml" \
  --archive "$ARCHIVE" \
  --release-version "$RELEASE_VERSION" \
  --source-date-epoch "$source_date_epoch"

echo "built $OUTPUT_DIR"
echo "packaged $ARCHIVE"
