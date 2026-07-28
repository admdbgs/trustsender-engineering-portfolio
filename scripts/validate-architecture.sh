#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_FILE="${REPOSITORY_ROOT}/architecture/workspace.dsl"
STYLES_FILE="${REPOSITORY_ROOT}/architecture/styles.dsl"
JSON_OUTPUT_DIRECTORY="${REPOSITORY_ROOT}/build/architecture-json"
VALIDATE_IMAGE="${STRUCTURIZR_VALIDATE_IMAGE:-structurizr/structurizr:2026.06.28-noble}"

cleanup() {
    rm -rf -- "${JSON_OUTPUT_DIRECTORY}"
}
trap cleanup EXIT

for required_file in "${WORKSPACE_FILE}" "${STYLES_FILE}"; do
    if [[ ! -f "${required_file}" ]]; then
        printf 'Error: required architecture file is missing: %s\n' "${required_file}" >&2
        exit 1
    fi
done

for required_command in docker python3; do
    if ! command -v "${required_command}" >/dev/null 2>&1; then
        printf 'Error: required architecture validation command is unavailable: %s\n' \
            "${required_command}" >&2
        exit 1
    fi
done

docker run --rm \
    --volume "${REPOSITORY_ROOT}:/usr/local/structurizr" \
    --workdir /usr/local/structurizr \
    "${VALIDATE_IMAGE}" \
    validate -workspace architecture/workspace.dsl

printf 'Official Structurizr DSL validation succeeded.\n'

rm -rf -- "${JSON_OUTPUT_DIRECTORY}"
mkdir -p -- "${JSON_OUTPUT_DIRECTORY}"

docker run --rm \
    --volume "${REPOSITORY_ROOT}:/usr/local/structurizr" \
    --workdir /usr/local/structurizr \
    "${VALIDATE_IMAGE}" \
    export \
    -workspace architecture/workspace.dsl \
    -format json \
    -output build/architecture-json

mapfile -t json_files < <(
    python3 - "${JSON_OUTPUT_DIRECTORY}" <<'PY'
import pathlib
import sys

for path in sorted(pathlib.Path(sys.argv[1]).rglob("*.json")):
    print(path)
PY
)

if [[ "${#json_files[@]}" -ne 1 ]]; then
    printf 'Error: expected exactly one compiled JSON file, found %s.\n' \
        "${#json_files[@]}" >&2
    exit 1
fi

compiled_json="${json_files[0]}"
if [[ -L "${compiled_json}" || ! -f "${compiled_json}" || ! -s "${compiled_json}" ]]; then
    printf 'Error: compiled JSON must be a regular, non-symbolic-link, non-empty file: %s\n' \
        "${compiled_json}" >&2
    exit 1
fi

resolved_output="$(python3 -c 'import pathlib, sys; print(pathlib.Path(sys.argv[1]).resolve())' "${JSON_OUTPUT_DIRECTORY}")"
resolved_json="$(python3 -c 'import pathlib, sys; print(pathlib.Path(sys.argv[1]).resolve())' "${compiled_json}")"
if [[ "${resolved_json}" != "${resolved_output}/"* ]]; then
    printf 'Error: compiled JSON escaped the architecture JSON output directory: %s\n' \
        "${compiled_json}" >&2
    exit 1
fi

printf 'Compiled Structurizr JSON export succeeded.\n'
python3 "${REPOSITORY_ROOT}/scripts/validate-architecture-json.py" "${compiled_json}"
printf 'Compiled JSON semantic invariants succeeded.\n'
