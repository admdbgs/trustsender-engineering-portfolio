#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
    printf 'Error: this renderer supports GNU/Linux only.\n' >&2
    exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
SOURCE_PATH="${REPOSITORY_ROOT}/visuals/trustsender-engineering-overview.d2"
OUTPUT_DIRECTORY="${REPOSITORY_ROOT}/build/architecture-svg"
OUTPUT_PATH="${OUTPUT_DIRECTORY}/trustsender-engineering-overview.svg"
D2_VERSION="v0.6.9"
D2_MODULE="oss.terrastruct.com/d2@${D2_VERSION}"
LAYOUT_ENGINE="elk"
THEME_ID="200"

cd "${REPOSITORY_ROOT}"

if [[ -L "${SOURCE_PATH}" ]] || [[ -L "${OUTPUT_DIRECTORY}" ]] || [[ -L "${OUTPUT_PATH}" ]]; then
    printf 'Error: symbolic links are not allowed for D2 source or output paths.\n' >&2
    exit 1
fi
if [[ ! -f "${SOURCE_PATH}" ]] || [[ ! -s "${SOURCE_PATH}" ]]; then
    printf 'Error: expected regular, non-empty D2 source: %s\n' "${SOURCE_PATH}" >&2
    exit 1
fi

status_outside_build="$(git status --porcelain --untracked-files=all -- ':!build')"
if [[ -n "${status_outside_build}" ]]; then
    printf 'Error: repository must be clean outside build/ before rendering D2 preview.\n%s\n' "${status_outside_build}" >&2
    exit 1
fi

rm -rf "${OUTPUT_DIRECTORY}"
mkdir -p "${OUTPUT_DIRECTORY}"

d2() {
    go run "${D2_MODULE}" "$@"
}

printf 'D2 version: '
d2 --version

d2 --layout "${LAYOUT_ENGINE}" --theme "${THEME_ID}" --sketch=false "${SOURCE_PATH}" "${OUTPUT_PATH}"

if [[ ! -f "${OUTPUT_PATH}" ]] || [[ -L "${OUTPUT_PATH}" ]] || [[ ! -s "${OUTPUT_PATH}" ]]; then
    printf 'Error: D2 output is not a regular, non-symbolic-link, non-empty file.\n' >&2
    exit 1
fi

python3 - "${OUTPUT_PATH}" <<'PY'
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
path = Path(sys.argv[1])
data = path.read_bytes()
root = ET.fromstring(data)
if root.tag.rsplit('}', 1)[-1] != 'svg':
    raise SystemExit('root element is not svg')
if not root.get('viewBox') or not root.get('viewBox').strip():
    raise SystemExit('missing non-empty viewBox')
text = data.decode('utf-8', errors='replace')
required = [
    'TrustSender.io Engineering Overview', 'ONGOING', 'Edge and Routing',
    'Web Application', 'Application API', 'PostgreSQL Database',
    'Job Control Plane', 'Distributed P1 Worker Plane', 'WordPress Blog',
    'P2 SMTP Execution Plane', 'Google Identity', 'Microsoft Identity',
    'Stripe', 'Brevo', 'GitHub Actions', 'Internet Mail Infrastructure',
]
for item in required:
    if item not in text:
        raise SystemExit(f'missing required SVG text: {item}')
for forbidden in ('admdbgs/trustsender', 'GITHUB_PRIVATE_KEY', 'GITHUB_TOKEN', 'localhost', '127.0.0.1'):
    if forbidden in text:
        raise SystemExit(f'forbidden SVG content: {forbidden}')
if re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text):
    raise SystemExit('forbidden IP-address-like content')
PY

mapfile -d '' svg_files < <(find "${OUTPUT_DIRECTORY}" -type f -name '*.svg' -print0)
if [[ "${#svg_files[@]}" -ne 1 ]]; then
    printf 'Error: expected exactly one D2 SVG output, found %s.\n' "${#svg_files[@]}" >&2
    exit 1
fi

sha256sum "${OUTPUT_PATH}"
status_after="$(git status --porcelain --untracked-files=all -- ':!build')"
if [[ -n "${status_after}" ]]; then
    printf 'Error: repository files outside build/ changed during D2 rendering.\n%s\n' "${status_after}" >&2
    exit 1
fi
printf 'Repository files outside build/ remained unchanged.\n'
