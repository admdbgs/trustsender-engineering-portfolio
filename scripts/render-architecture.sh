#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_FILE="${REPOSITORY_ROOT}/architecture/workspace.dsl"
STYLES_FILE="${REPOSITORY_ROOT}/architecture/styles.dsl"
OUTPUT_DIRECTORY="${REPOSITORY_ROOT}/build/architecture-svg"
RENDER_IMAGE="${STRUCTURIZR_RENDER_IMAGE:-structurizr/structurizr:2026.06.28-playwright}"

if ! command -v docker >/dev/null 2>&1; then
    printf 'Error: Docker is required to render the architecture.\n' >&2
    exit 1
fi

for required_file in "${WORKSPACE_FILE}" "${STYLES_FILE}"; do
    if [[ ! -f "${required_file}" ]]; then
        printf 'Error: required architecture file is missing: %s\n' "${required_file}" >&2
        exit 1
    fi
done

rm -rf -- "${OUTPUT_DIRECTORY}"
mkdir -p -- "${OUTPUT_DIRECTORY}"

docker run --rm \
    --volume "${REPOSITORY_ROOT}:/usr/local/structurizr" \
    --workdir /usr/local/structurizr \
    "${RENDER_IMAGE}" \
    export \
    -workspace architecture/workspace.dsl \
    -format svg \
    -output build/architecture-svg \
    -mode dark

if [[ -L "${OUTPUT_DIRECTORY}" ]] || find "${OUTPUT_DIRECTORY}" -type l -print -quit | grep -q .; then
    printf 'Error: symbolic links are not allowed in the SVG preview output.\n' >&2
    exit 1
fi

mapfile -d '' svg_files < <(find "${OUTPUT_DIRECTORY}" -type f -name '*.svg' -print0 | sort -z)
if [[ "${#svg_files[@]}" -ne 2 ]]; then
    printf 'Error: expected exactly two SVG files, found %s.\n' "${#svg_files[@]}" >&2
    exit 1
fi

output_real="$(realpath -- "${OUTPUT_DIRECTORY}")"
for svg_file in "${svg_files[@]}"; do
    file_real="$(realpath -- "${svg_file}")"
    if [[ "${file_real}" != "${output_real}/"* ]]; then
        printf 'Error: generated file escaped the output directory: %s\n' "${svg_file}" >&2
        exit 1
    fi
    if [[ ! -s "${svg_file}" ]]; then
        printf 'Error: generated SVG is empty: %s\n' "${svg_file}" >&2
        exit 1
    fi
done

printf 'Generated dark-mode SVG previews:\n'
(cd -- "${OUTPUT_DIRECTORY}" && sha256sum -- "${svg_files[@]##*/}")
