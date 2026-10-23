#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "usage: install.sh PATH_TO_SarasaTermSlabSS17SCNF.ttc|PATH_TO_SarasaMonoSS17SCNF.ttc..." >&2
  exit 2
fi
FONT_DIR=${FONT_DIR:-"$HOME/Library/Fonts"}

for source in "$@"; do
  case "$(basename "$source")" in
    SarasaTermSlabSS17SCNF.ttc | SarasaMonoSS17SCNF.ttc) ;;
    *)
      echo "unrecognized font file (expected SarasaTermSlabSS17SCNF.ttc or SarasaMonoSS17SCNF.ttc): $source" >&2
      exit 1
      ;;
  esac
  if [[ ! -f "$source" ]]; then
    echo "font file not found: $source" >&2
    exit 1
  fi
done

mkdir -p "$FONT_DIR"
for source in "$@"; do
  name=$(basename "$source")
  install -m 0644 "$source" "$FONT_DIR/$name"
  echo "installed $FONT_DIR/$name"
done
