#!/bin/bash
# Download Montserrat fonts into ./fonts

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FONT_DIR="${PROJECT_DIR}/fonts"
BASE_URL="https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/static"
FILES=(
  "Montserrat-Light.ttf"
  "Montserrat-Regular.ttf"
  "Montserrat-Medium.ttf"
  "Montserrat-SemiBold.ttf"
  "Montserrat-LightItalic.ttf"
  "Montserrat-Italic.ttf"
)

mkdir -p "${FONT_DIR}"

fetch_file() {
  local file="$1"
  local url="${BASE_URL}/${file}"
  local out="${FONT_DIR}/${file}"

  if command -v wget >/dev/null 2>&1; then
    wget -q -O "${out}" "${url}"
    return
  fi

  if command -v curl >/dev/null 2>&1; then
    curl -sSfL -o "${out}" "${url}"
    return
  fi

  echo "Need wget or curl installed to download fonts." >&2
  exit 1
}

for file in "${FILES[@]}"; do
  echo "Downloading ${file}..."
  fetch_file "${file}"
done

echo "Montserrat fonts installed to ${FONT_DIR}"
