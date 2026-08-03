#!/usr/bin/env bash
set -euo pipefail

if (( BASH_VERSINFO[0] < 4 )); then
    printf 'Error: Bash 4 or newer is required for the container layout candidate build.\n' >&2
    exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd -- "${REPOSITORY_ROOT}"

VALIDATE_IMAGE="${STRUCTURIZR_VALIDATE_IMAGE:-structurizr/structurizr:2026.06.28-noble}"
RENDER_IMAGE="${STRUCTURIZR_RENDER_IMAGE:-structurizr/structurizr:2026.06.28-playwright}"
SOURCE_JSON_DIRECTORY="build/container-layout-candidate/source-json"
TRANSFORMED_JSON_DIRECTORY="build/container-layout-candidate/transformed-json"
CANDIDATE_SVG_DIRECTORY="build/container-layout-candidate-svg"
TRANSFORMED_WORKSPACE="${TRANSFORMED_JSON_DIRECTORY}/workspace.json"

prerequisite_error() {
    printf 'Error: the candidate build requires GNU/Linux with Bash 4+, Docker, Python 3, GNU findutils, and GNU coreutils.\n' >&2
}

for required_command in docker python3 find sort realpath sha256sum grep uname git; do
    if ! command -v "${required_command}" >/dev/null 2>&1; then
        printf 'Error: required command is unavailable: %s\n' "${required_command}" >&2
        prerequisite_error
        exit 1
    fi
done

if [[ "$(uname -s)" != "Linux" ]]; then
    printf 'Error: the container layout candidate build supports GNU/Linux only.\n' >&2
    prerequisite_error
    exit 1
fi
if ! find --version 2>&1 | grep -q 'GNU findutils'; then
    printf 'Error: GNU findutils is required for the container layout candidate build.\n' >&2
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

RESOLVED_REPOSITORY_ROOT="$(realpath -- "${REPOSITORY_ROOT}")"
REPOSITORY_ROOT="${RESOLVED_REPOSITORY_ROOT}"
cd -- "${REPOSITORY_ROOT}"
BUILD_DIRECTORY="${REPOSITORY_ROOT}/build"
EXPECTED_BUILD_DIRECTORY="${RESOLVED_REPOSITORY_ROOT}/build"

if [[ -L "${BUILD_DIRECTORY}" ]]; then
    printf 'Error: unsafe build path is a symbolic link: %s\n' "${BUILD_DIRECTORY}" >&2
    exit 1
fi
if [[ -e "${BUILD_DIRECTORY}" && ! -d "${BUILD_DIRECTORY}" ]]; then
    printf 'Error: unsafe build path exists but is not a directory: %s\n' "${BUILD_DIRECTORY}" >&2
    exit 1
fi
if [[ ! -e "${BUILD_DIRECTORY}" ]]; then
    mkdir -- "${BUILD_DIRECTORY}"
fi

RESOLVED_BUILD_DIRECTORY="$(realpath -- "${BUILD_DIRECTORY}")"
if [[ "${RESOLVED_BUILD_DIRECTORY}" != "${EXPECTED_BUILD_DIRECTORY}" ]]; then
    printf 'Error: unsafe build path %s resolves to %s; expected exactly %s.\n' \
        "${BUILD_DIRECTORY}" "${RESOLVED_BUILD_DIRECTORY}" "${EXPECTED_BUILD_DIRECTORY}" >&2
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

for stale_directory in build/container-layout-candidate build/container-layout-candidate-svg; do
    stale_directory_absolute="${REPOSITORY_ROOT}/${stale_directory}"
    stale_parent_resolved="$(realpath -- "$(dirname -- "${stale_directory_absolute}")")"
    if [[ "${stale_parent_resolved}" != "${RESOLVED_BUILD_DIRECTORY}" ]]; then
        printf 'Error: unsafe candidate target parent for %s resolves to %s; expected exactly %s.\n' \
            "${stale_directory_absolute}" "${stale_parent_resolved}" "${RESOLVED_BUILD_DIRECTORY}" >&2
        exit 1
    fi
    if [[ -L "${stale_directory_absolute}" ]]; then
        printf 'Error: candidate output directory must not be a symbolic link: %s\n' \
            "${stale_directory_absolute}" >&2
        exit 1
    fi
    if [[ -e "${stale_directory_absolute}" && ! -d "${stale_directory_absolute}" ]]; then
        printf 'Error: candidate output path exists but is not a directory: %s\n' \
            "${stale_directory_absolute}" >&2
        exit 1
    fi
    if [[ -d "${stale_directory_absolute}" ]] && \
        find "${stale_directory_absolute}" -type l -print -quit | grep -q .; then
        printf 'Error: symbolic links are not allowed under candidate output directory: %s\n' \
            "${stale_directory_absolute}" >&2
        exit 1
    fi
done

initial_repository_status="$(git status --porcelain=v1 -uall -- . ':(exclude)build')"
if [[ -n "${initial_repository_status}" ]]; then
    printf 'Error: tracked or untracked repository content outside build/ is not clean before candidate execution.\n%s\n' \
        "${initial_repository_status}" >&2
    exit 1
fi

rm -rf -- build/container-layout-candidate build/container-layout-candidate-svg
mkdir -p -- "${SOURCE_JSON_DIRECTORY}" "${TRANSFORMED_JSON_DIRECTORY}" "${CANDIDATE_SVG_DIRECTORY}"

docker run --rm \
    --volume "${REPOSITORY_ROOT}:/usr/local/structurizr" \
    --workdir /usr/local/structurizr \
    "${VALIDATE_IMAGE}" \
    export \
    -workspace architecture/workspace.dsl \
    -format json \
    -output "${SOURCE_JSON_DIRECTORY}"

mapfile -d '' source_json_files < <(find "${SOURCE_JSON_DIRECTORY}" -type f -name '*.json' -print0 | sort -z)
if [[ "${#source_json_files[@]}" -ne 1 ]]; then
    printf 'Error: expected exactly one exported JSON file, found %s.\n' "${#source_json_files[@]}" >&2
    exit 1
fi
source_json="${source_json_files[0]}"
source_directory_real="$(realpath -- "${SOURCE_JSON_DIRECTORY}")"
source_json_real="$(realpath -- "${source_json}")"
if [[ -L "${source_json}" || ! -f "${source_json}" || ! -s "${source_json}" ]]; then
    printf 'Error: exported JSON must be a regular, non-symbolic-link, non-empty file: %s\n' "${source_json}" >&2
    exit 1
fi
if [[ "${source_json_real}" != "${source_directory_real}/"* ]]; then
    printf 'Error: exported JSON escaped the expected source directory: %s\n' "${source_json}" >&2
    exit 1
fi

python3 scripts/validate-architecture-json.py "${source_json}"
printf 'Original compiled JSON semantic validation succeeded.\n'

python3 scripts/apply-container-layout.py \
    "${source_json}" \
    "${TRANSFORMED_WORKSPACE}"

transformed_directory_real="$(realpath -- "${TRANSFORMED_JSON_DIRECTORY}")"
transformed_workspace_real="$(realpath -- "${TRANSFORMED_WORKSPACE}")"
if [[ -L "${TRANSFORMED_WORKSPACE}" || ! -f "${TRANSFORMED_WORKSPACE}" || ! -s "${TRANSFORMED_WORKSPACE}" ]]; then
    printf 'Error: transformed workspace must be a regular, non-symbolic-link, non-empty file: %s\n' \
        "${TRANSFORMED_WORKSPACE}" >&2
    exit 1
fi
if [[ "${transformed_workspace_real}" != "${transformed_directory_real}/"* ]]; then
    printf 'Error: transformed workspace escaped the expected output directory: %s\n' \
        "${TRANSFORMED_WORKSPACE}" >&2
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
    -output "${CANDIDATE_SVG_DIRECTORY}" \
    -mode dark

for output_directory in build/container-layout-candidate "${CANDIDATE_SVG_DIRECTORY}"; do
    if [[ -L "${output_directory}" ]] || find "${output_directory}" -type l -print -quit | grep -q .; then
        printf 'Error: symbolic links are not allowed under candidate output directory: %s\n' \
            "${output_directory}" >&2
        exit 1
    fi
done

expected_svg_filenames=(
    trustsender-container-view-key.svg
    trustsender-container-view.svg
    trustsender-system-context-key.svg
    trustsender-system-context.svg
)
mapfile -d '' candidate_svg_files < <(find "${CANDIDATE_SVG_DIRECTORY}" -type f -name '*.svg' -print0 | sort -z)
if [[ "${#candidate_svg_files[@]}" -ne 4 ]]; then
    printf 'Error: expected exactly four candidate SVG files, found %s.\n' "${#candidate_svg_files[@]}" >&2
    exit 1
fi
candidate_svg_directory_real="$(realpath -- "${CANDIDATE_SVG_DIRECTORY}")"
for index in "${!expected_svg_filenames[@]}"; do
    svg_file="${candidate_svg_files[index]}"
    svg_file_real="$(realpath -- "${svg_file}")"
    if [[ "${svg_file##*/}" != "${expected_svg_filenames[index]}" ]]; then
        printf 'Error: expected candidate SVG %s, found %s.\n' \
            "${expected_svg_filenames[index]}" "${svg_file##*/}" >&2
        exit 1
    fi
    if [[ -L "${svg_file}" || ! -f "${svg_file}" || ! -s "${svg_file}" ]]; then
        printf 'Error: candidate SVG must be a regular, non-symbolic-link, non-empty file: %s\n' \
            "${svg_file}" >&2
        exit 1
    fi
    if [[ "${svg_file_real}" != "${candidate_svg_directory_real}/"* ]]; then
        printf 'Error: candidate SVG escaped the expected output directory: %s\n' "${svg_file}" >&2
        exit 1
    fi
done

python3 - "${CANDIDATE_SVG_DIRECTORY}/trustsender-container-view.svg" <<'PY'
import sys
import xml.etree.ElementTree as ET


path = sys.argv[1]
try:
    root = ET.parse(path).getroot()
except (ET.ParseError, OSError) as error:
    raise SystemExit("Error: unable to parse candidate Container View SVG {}: {}".format(
        path, error))

local_name = root.tag.rsplit("}", 1)[-1]
if local_name != "svg":
    raise SystemExit("Error: candidate Container View XML root local name is {!r}; expected 'svg'.".format(
        local_name))

def require_dimension(name, expected):
    observed = root.get(name)
    normalized = observed[:-2] if observed is not None and observed.endswith("px") else observed
    if normalized != str(expected):
        raise SystemExit(
            "Error: candidate Container View SVG {} is {!r}; expected exactly {} or {}px.".format(
                name, observed, expected, expected))

require_dimension("width", 5000)
require_dimension("height", 2200)
observed_view_box = root.get("viewBox")
normalized_view_box = " ".join(observed_view_box.split()) if observed_view_box is not None else None
if normalized_view_box != "0 0 5000 2200":
    raise SystemExit(
        "Error: candidate Container View SVG viewBox is {!r}; expected normalized value "
        "'0 0 5000 2200'.".format(observed_view_box))
PY
printf 'Candidate Container View SVG canvas validation succeeded.\n'

final_repository_status="$(git status --porcelain=v1 -uall -- . ':(exclude)build')"
if [[ -n "${final_repository_status}" ]]; then
    printf 'Error: candidate execution modified or created repository content outside build/.\n%s\n' \
        "${final_repository_status}" >&2
    exit 1
fi
if [[ -n "$(git status --porcelain=v1 -uall -- architecture diagrams)" ]]; then
    printf 'Error: generated JSON or SVG content was written under architecture/ or diagrams/.\n' >&2
    exit 1
fi

printf 'Candidate output SHA-256 hashes:\n'
sha256sum -- "${TRANSFORMED_WORKSPACE}" "${candidate_svg_files[@]}"
printf 'Container layout candidate build succeeded.\n'
