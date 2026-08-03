#!/usr/bin/env bash
set -euo pipefail

if (( BASH_VERSINFO[0] < 4 )); then
    printf 'Error: Bash 4 or newer is required for official architecture rendering.\n' >&2
    exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd -- "${REPOSITORY_ROOT}"

VALIDATE_IMAGE="${STRUCTURIZR_VALIDATE_IMAGE:-structurizr/structurizr:2026.06.28-noble}"
RENDER_IMAGE="${STRUCTURIZR_RENDER_IMAGE:-structurizr/structurizr:2026.06.28-playwright}"
SOURCE_JSON_DIRECTORY="build/architecture-layout/source-json"
TRANSFORMED_JSON_DIRECTORY="build/architecture-layout/transformed-json"
TRANSFORMED_WORKSPACE="build/architecture-layout/transformed-json/workspace.json"
OUTPUT_DIRECTORY="build/architecture-svg"

prerequisite_error() {
    printf 'Error: official architecture rendering requires GNU/Linux with Bash 4+, Docker, Python 3, GNU findutils, GNU coreutils, and git.\n' >&2
}

for required_command in docker python3 find sort realpath sha256sum grep uname git; do
    if ! command -v "${required_command}" >/dev/null 2>&1; then
        printf 'Error: required command is unavailable: %s\n' "${required_command}" >&2
        prerequisite_error
        exit 1
    fi
done

if [[ "$(uname -s)" != "Linux" ]]; then
    printf 'Error: official architecture rendering supports GNU/Linux only.\n' >&2
    prerequisite_error
    exit 1
fi
if ! find --version 2>&1 | grep -q 'GNU findutils'; then
    printf 'Error: GNU findutils is required for official architecture rendering.\n' >&2
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

REPOSITORY_ROOT="$(realpath -- "${REPOSITORY_ROOT}")"
cd -- "${REPOSITORY_ROOT}"
BUILD_DIRECTORY="${REPOSITORY_ROOT}/build"
if [[ -L "${BUILD_DIRECTORY}" || ( -e "${BUILD_DIRECTORY}" && ! -d "${BUILD_DIRECTORY}" ) ]]; then
    printf 'Error: build path must be a non-symbolic-link directory: %s\n' "${BUILD_DIRECTORY}" >&2
    exit 1
fi
mkdir -p -- "${BUILD_DIRECTORY}"
RESOLVED_BUILD_DIRECTORY="$(realpath -- "${BUILD_DIRECTORY}")"
if [[ "${RESOLVED_BUILD_DIRECTORY}" != "${REPOSITORY_ROOT}/build" ]]; then
    printf 'Error: build path escapes the repository build directory: %s\n' "${RESOLVED_BUILD_DIRECTORY}" >&2
    exit 1
fi

required_files=(
    architecture/workspace.dsl
    architecture/styles.dsl
    scripts/validate-architecture-json.py
    scripts/apply-container-layout.py
    scripts/validate-container-layout.py
)
for required_file in "${required_files[@]}"; do
    if [[ -L "${required_file}" || ! -f "${required_file}" ]]; then
        printf 'Error: required input must be a regular, non-symbolic-link file: %s\n' "${required_file}" >&2
        exit 1
    fi
done

for output_path in build/architecture-layout build/architecture-svg; do
    output_absolute="${REPOSITORY_ROOT}/${output_path}"
    if [[ "$(realpath -- "$(dirname -- "${output_absolute}")")" != "${RESOLVED_BUILD_DIRECTORY}" ]]; then
        printf 'Error: official output path escapes build/: %s\n' "${output_absolute}" >&2
        exit 1
    fi
    if [[ -L "${output_absolute}" || ( -e "${output_absolute}" && ! -d "${output_absolute}" ) ]]; then
        printf 'Error: official output path must be a non-symbolic-link directory: %s\n' "${output_absolute}" >&2
        exit 1
    fi
    if [[ -d "${output_absolute}" ]] && find "${output_absolute}" -type l -print -quit | grep -q .; then
        printf 'Error: symbolic links are not allowed under official output path: %s\n' "${output_absolute}" >&2
        exit 1
    fi
done

initial_repository_status="$(git status --porcelain=v1 -uall -- . ':(exclude)build')"
if [[ -n "${initial_repository_status}" ]]; then
    printf 'Error: repository content outside build/ is not clean before official rendering.\n%s\n' \
        "${initial_repository_status}" >&2
    exit 1
fi

rm -rf -- build/architecture-layout build/architecture-svg
mkdir -p -- "${SOURCE_JSON_DIRECTORY}" "${TRANSFORMED_JSON_DIRECTORY}" "${OUTPUT_DIRECTORY}"

docker run --rm \
    --volume "${REPOSITORY_ROOT}:/usr/local/structurizr" \
    --workdir /usr/local/structurizr \
    "${VALIDATE_IMAGE}" \
    export \
    -workspace architecture/workspace.dsl \
    -format json \
    -output "${SOURCE_JSON_DIRECTORY}"

if find "${SOURCE_JSON_DIRECTORY}" -type l -print -quit | grep -q .; then
    printf 'Error: symbolic links are not allowed in the source JSON output.\n' >&2
    exit 1
fi
mapfile -d '' source_generated_files < <(find "${SOURCE_JSON_DIRECTORY}" -type f -print0 | sort -z)
mapfile -d '' source_json_files < <(find "${SOURCE_JSON_DIRECTORY}" -type f -name '*.json' -print0 | sort -z)
if [[ "${#source_generated_files[@]}" -ne 1 || "${#source_json_files[@]}" -ne 1 ]]; then
    printf 'Error: expected exactly one source JSON export and no unexpected files.\n' >&2
    exit 1
fi
source_json="${source_json_files[0]}"
source_directory_real="$(realpath -- "${SOURCE_JSON_DIRECTORY}")"
source_json_real="$(realpath -- "${source_json}")"
if [[ -L "${source_json}" || ! -f "${source_json}" || ! -s "${source_json}" || "${source_json_real}" != "${source_directory_real}/"* ]]; then
    printf 'Error: source JSON must be a contained, regular, non-symbolic-link, non-empty file: %s\n' "${source_json}" >&2
    exit 1
fi

python3 scripts/validate-architecture-json.py "${source_json}"
printf 'Original compiled JSON semantic validation succeeded.\n'

python3 scripts/apply-container-layout.py \
    "${source_json}" \
    "${TRANSFORMED_WORKSPACE}"

mapfile -d '' transformed_files < <(find "${TRANSFORMED_JSON_DIRECTORY}" -type f -print0 | sort -z)
transformed_directory_real="$(realpath -- "${TRANSFORMED_JSON_DIRECTORY}")"
transformed_workspace_real="$(realpath -- "${TRANSFORMED_WORKSPACE}")"
if [[ "${#transformed_files[@]}" -ne 1 || "${transformed_files[0]:-}" != "${TRANSFORMED_WORKSPACE}" ]]; then
    printf 'Error: expected only the transformed workspace JSON output.\n' >&2
    exit 1
fi
if [[ -L "${TRANSFORMED_WORKSPACE}" || ! -f "${TRANSFORMED_WORKSPACE}" || ! -s "${TRANSFORMED_WORKSPACE}" || \
      "${transformed_workspace_real}" != "${transformed_directory_real}/"* ]]; then
    printf 'Error: transformed workspace must be a contained, regular, non-symbolic-link, non-empty file.\n' >&2
    exit 1
fi
if [[ "${source_json_real}" == "${transformed_workspace_real}" ]]; then
    printf 'Error: source and transformed workspace paths must be different.\n' >&2
    exit 1
fi

python3 scripts/validate-architecture-json.py "${TRANSFORMED_WORKSPACE}"
python3 scripts/validate-container-layout.py "${TRANSFORMED_WORKSPACE}"
docker run --rm \
    --volume "${REPOSITORY_ROOT}:/usr/local/structurizr" \
    --workdir /usr/local/structurizr \
    "${VALIDATE_IMAGE}" \
    validate \
    -workspace "${TRANSFORMED_WORKSPACE}"

docker run --rm \
    --volume "${REPOSITORY_ROOT}:/usr/local/structurizr" \
    --workdir /usr/local/structurizr \
    "${RENDER_IMAGE}" \
    export \
    -workspace "${TRANSFORMED_WORKSPACE}" \
    -format svg \
    -output "${OUTPUT_DIRECTORY}" \
    -mode dark

if [[ -L "${OUTPUT_DIRECTORY}" ]] || find "${OUTPUT_DIRECTORY}" -type l -print -quit | grep -q .; then
    printf 'Error: symbolic links are not allowed in official SVG output.\n' >&2
    exit 1
fi
expected_svg_filenames=(
    trustsender-container-view-key.svg
    trustsender-container-view.svg
    trustsender-system-context-key.svg
    trustsender-system-context.svg
)
mapfile -d '' generated_output_files < <(find "${OUTPUT_DIRECTORY}" -type f -print0 | sort -z)
mapfile -d '' svg_files < <(find "${OUTPUT_DIRECTORY}" -type f -name '*.svg' -print0 | sort -z)
if [[ "${#generated_output_files[@]}" -ne 4 || "${#svg_files[@]}" -ne 4 ]]; then
    printf 'Error: expected exactly four official SVG files and no unexpected files.\n' >&2
    exit 1
fi
output_real="$(realpath -- "${OUTPUT_DIRECTORY}")"
for index in "${!expected_svg_filenames[@]}"; do
    svg_file="${svg_files[index]}"
    svg_file_real="$(realpath -- "${svg_file}")"
    if [[ "${svg_file##*/}" != "${expected_svg_filenames[index]}" ]]; then
        printf 'Error: expected official SVG %s, found %s.\n' "${expected_svg_filenames[index]}" "${svg_file##*/}" >&2
        exit 1
    fi
    if [[ -L "${svg_file}" || ! -f "${svg_file}" || ! -s "${svg_file}" || "${svg_file_real}" != "${output_real}/"* ]]; then
        printf 'Error: official SVG must be a contained, regular, non-symbolic-link, non-empty file: %s\n' "${svg_file}" >&2
        exit 1
    fi
done

python3 - "${OUTPUT_DIRECTORY}/trustsender-container-view.svg" <<'PY'
import sys
import xml.etree.ElementTree as ET

path = sys.argv[1]
try:
    root = ET.parse(path).getroot()
except (ET.ParseError, OSError) as error:
    raise SystemExit(f"Error: unable to parse official Container View SVG {path}: {error}")
if root.tag.rsplit("}", 1)[-1] != "svg":
    raise SystemExit("Error: official Container View XML root is not svg.")

def require_dimension(name, expected):
    observed = root.get(name)
    normalized = observed[:-2] if observed is not None and observed.endswith("px") else observed
    if normalized != str(expected):
        raise SystemExit(
            f"Error: official Container View SVG {name} is {observed!r}; "
            f"expected exactly {expected} or {expected}px.")

require_dimension("width", 5000)
require_dimension("height", 2200)
observed_view_box = root.get("viewBox")
normalized_view_box = " ".join(observed_view_box.split()) if observed_view_box is not None else None
if normalized_view_box != "0 0 5000 2200":
    raise SystemExit(
        f"Error: official Container View SVG viewBox is {observed_view_box!r}; "
        "expected normalized value '0 0 5000 2200'.")
PY
printf 'Official Container View SVG canvas validation succeeded.\n'

final_repository_status="$(git status --porcelain=v1 -uall -- . ':(exclude)build')"
if [[ -n "${final_repository_status}" ]]; then
    printf 'Error: official rendering modified or created repository content outside build/.\n%s\n' \
        "${final_repository_status}" >&2
    exit 1
fi
if [[ -n "$(git status --porcelain=v1 -uall -- architecture diagrams)" ]]; then
    printf 'Error: generated content was written under architecture/ or diagrams/.\n' >&2
    exit 1
fi

printf 'Official architecture output SHA-256 hashes:\n'
sha256sum -- "${TRANSFORMED_WORKSPACE}" "${svg_files[@]}"
printf 'Official dark-mode architecture preview rendering succeeded.\n'
