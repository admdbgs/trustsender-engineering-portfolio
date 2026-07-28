#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_FILE="${REPOSITORY_ROOT}/architecture/workspace.dsl"
STYLES_FILE="${REPOSITORY_ROOT}/architecture/styles.dsl"
OUTPUT_DIRECTORY="${REPOSITORY_ROOT}/build/architecture-svg"
RENDER_IMAGE="${STRUCTURIZR_RENDER_IMAGE:-structurizr/structurizr:2026.06.28-playwright}"

prerequisite_error() {
    printf 'Error: local architecture rendering requires GNU/Linux or WSL with Bash 4+, GNU findutils, GNU coreutils, and Docker.\n' >&2
}

if (( BASH_VERSINFO[0] < 4 )); then
    printf 'Error: Bash 4 or newer is required for local architecture rendering.\n' >&2
    prerequisite_error
    exit 1
fi

for required_command in docker find sort realpath sha256sum grep uname; do
    if ! command -v "${required_command}" >/dev/null 2>&1; then
        printf 'Error: required command is unavailable: %s\n' "${required_command}" >&2
        prerequisite_error
        exit 1
    fi
done

if [[ "$(uname -s)" != "Linux" ]]; then
    prerequisite_error
    exit 1
fi

if ! find --version 2>&1 | grep -q 'GNU findutils'; then
    printf 'Error: GNU findutils is required for local architecture rendering.\n' >&2
    prerequisite_error
    exit 1
fi

for coreutils_command in sort realpath sha256sum; do
    if ! "${coreutils_command}" --version 2>&1 | grep -q 'GNU coreutils'; then
        printf 'Error: GNU coreutils command is required: %s\n' "${coreutils_command}" >&2
        prerequisite_error
        exit 1
    fi
done

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

expected_filenames=(
    trustsender-container-view-key.svg
    trustsender-container-view.svg
    trustsender-system-context-key.svg
    trustsender-system-context.svg
)
mapfile -d '' svg_files < <(find "${OUTPUT_DIRECTORY}" -type f -name '*.svg' -print0 | sort -z)
if [[ "${#svg_files[@]}" -ne 4 ]]; then
    printf 'Error: expected exactly four SVG files, found %s.\n' "${#svg_files[@]}" >&2
    exit 1
fi

output_real="$(realpath -- "${OUTPUT_DIRECTORY}")"
for index in "${!expected_filenames[@]}"; do
    svg_file="${svg_files[index]}"
    file_real="$(realpath -- "${svg_file}")"
    if [[ "${file_real}" != "${output_real}/"* ]]; then
        printf 'Error: generated file escaped the output directory: %s\n' "${svg_file}" >&2
        exit 1
    fi
    if [[ "${svg_file##*/}" != "${expected_filenames[index]}" ]]; then
        printf 'Error: expected SVG file %s, found %s.\n' \
            "${expected_filenames[index]}" "${svg_file##*/}" >&2
        exit 1
    fi
    if [[ ! -s "${svg_file}" ]]; then
        printf 'Error: generated SVG is empty: %s\n' "${svg_file}" >&2
        exit 1
    fi
done

printf 'Generated dark-mode SVG previews:\n'
(cd -- "${OUTPUT_DIRECTORY}" && sha256sum -- "${svg_files[@]##*/}")
