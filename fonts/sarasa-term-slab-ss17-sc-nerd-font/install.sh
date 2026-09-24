#!/usr/bin/env bash
set -euo pipefail

SOURCE=${1:?usage: install.sh PATH_TO_SarasaTermSlabSS17SCNF.ttc}
FONT_DIR=${FONT_DIR:-"$HOME/Library/Fonts"}

if [[ ! -f "$SOURCE" ]]; then
  echo "font file not found: $SOURCE" >&2
  exit 1
fi

mkdir -p "$FONT_DIR"
install -m 0644 "$SOURCE" "$FONT_DIR/SarasaTermSlabSS17SCNF.ttc"
echo "installed $FONT_DIR/SarasaTermSlabSS17SCNF.ttc"
