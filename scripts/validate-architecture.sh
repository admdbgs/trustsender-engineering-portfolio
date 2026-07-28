#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_FILE="${REPOSITORY_ROOT}/architecture/workspace.dsl"
STYLES_FILE="${REPOSITORY_ROOT}/architecture/styles.dsl"
VALIDATE_IMAGE="${STRUCTURIZR_VALIDATE_IMAGE:-structurizr/structurizr:2026.06.28-noble}"

if ! command -v docker >/dev/null 2>&1; then
    printf 'Error: Docker is required to validate the architecture.\n' >&2
    exit 1
fi

for required_file in "${WORKSPACE_FILE}" "${STYLES_FILE}"; do
    if [[ ! -f "${required_file}" ]]; then
        printf 'Error: required architecture file is missing: %s\n' "${required_file}" >&2
        exit 1
    fi
done

docker run --rm \
    --volume "${REPOSITORY_ROOT}:/usr/local/structurizr" \
    --workdir /usr/local/structurizr \
    "${VALIDATE_IMAGE}" \
    validate -workspace architecture/workspace.dsl

printf 'Structurizr validation succeeded.\n'

assert_count() {
    local expected="$1"
    local pattern="$2"
    local file="$3"
    local description="$4"
    local actual

    actual="$(awk -v pattern="${pattern}" '$0 ~ pattern { count++ } END { print count + 0 }' "${file}")"
    if [[ "${actual}" -ne "${expected}" ]]; then
        printf 'Error: expected %s occurrence(s) of %s, found %s.\n' \
            "${expected}" "${description}" "${actual}" >&2
        exit 1
    fi
}

assert_count 1 '^[[:space:]]*systemContext[[:space:]]' "${WORKSPACE_FILE}" 'a systemContext view'
assert_count 1 '^[[:space:]]*container[[:space:]]+trustSender[[:space:]]' "${WORKSPACE_FILE}" 'a container view'
assert_count 1 'systemContext trustSender "trustsender-system-context"' "${WORKSPACE_FILE}" 'the system-context key'
assert_count 1 'container trustSender "trustsender-container-view"' "${WORKSPACE_FILE}" 'the container-view key'

if ! awk '
    function active_code(text,    result, index_in_line, character, next_character, in_quote, escaped) {
        result = ""
        in_quote = 0
        escaped = 0

        for (index_in_line = 1; index_in_line <= length(text); index_in_line++) {
            character = substr(text, index_in_line, 1)
            next_character = substr(text, index_in_line + 1, 1)

            if (in_quote) {
                result = result character
                if (escaped) {
                    escaped = 0
                } else if (character == "\\") {
                    escaped = 1
                } else if (character == "\"") {
                    in_quote = 0
                }
                continue
            }

            if (character == "\"") {
                in_quote = 1
                result = result character
            } else if (character == "#" || (character == "/" && next_character == "/")) {
                break
            } else {
                result = result character
            }
        }

        return result
    }

    {
        line = $0
        while (1) {
            if (in_block_comment) {
                block_end = index(line, "*/")
                if (!block_end) {
                    line = ""
                    break
                }
                line = substr(line, block_end + 2)
                in_block_comment = 0
            }

            block_start = index(line, "/*")
            if (!block_start) break

            block_tail = substr(line, block_start + 2)
            block_end = index(block_tail, "*/")
            if (block_end) {
                line = substr(line, 1, block_start - 1) substr(block_tail, block_end + 2)
            } else {
                line = substr(line, 1, block_start - 1)
                in_block_comment = 1
                break
            }
        }

        line = active_code(line)

        if (line ~ /^[[:space:]]*p2Smtp[[:space:]]*=[[:space:]]*container[[:space:]]/) {
            declarations++
            if (line ~ /"Status: ONGOING[.]/) ongoing_status++
            if (line ~ /"Ongoing"[[:space:]]*$/) ongoing_tag++
        }
    }
    END { exit(declarations != 1 || ongoing_status != 1 || ongoing_tag != 1) }
' "${WORKSPACE_FILE}"; then
    printf 'Error: expected exactly one active P2 container declaration with Status: ONGOING. and the Ongoing tag.\n' >&2
    exit 1
fi

if awk '
    /^[[:space:]]*([^[:space:]=]+[[:space:]]*=[[:space:]]*)?(p2Smtp[[:space:]]*->[[:space:]]*[^[:space:]]+|[^[:space:]=]+[[:space:]]*->[[:space:]]*p2Smtp)([[:space:]]|$)/ {
        found = 1
        if ($0 !~ /"Ongoing"[[:space:]]*$/) invalid = 1
    }
    END { exit(!found || invalid) }
' "${WORKSPACE_FILE}"; then
    :
else
    printf 'Error: every P2 relationship must have the Ongoing tag.\n' >&2
    exit 1
fi

if ! awk '
    /^relationship "Operational"[[:space:]]*\{/ { block = 1; next }
    block && /^[[:space:]]*}/ { exit(found ? 0 : 1) }
    block && /^[[:space:]]*style solid[[:space:]]*$/ { found = 1 }
    END { if (!block || !found) exit 1 }
' "${STYLES_FILE}"; then
    printf 'Error: relationship "Operational" must contain "style solid".\n' >&2
    exit 1
fi

if ! awk '
    /^relationship "Ongoing"[[:space:]]*\{/ { block = 1; next }
    block && /^[[:space:]]*}/ { exit(found ? 0 : 1) }
    block && /^[[:space:]]*style dashed[[:space:]]*$/ { found = 1 }
    END { if (!block || !found) exit 1 }
' "${STYLES_FILE}"; then
    printf 'Error: relationship "Ongoing" must contain "style dashed".\n' >&2
    exit 1
fi

if grep -Fq 'dashed true' "${WORKSPACE_FILE}" "${STYLES_FILE}"; then
    printf 'Error: deprecated "dashed true" styling is not allowed.\n' >&2
    exit 1
fi

printf 'Architecture repository invariants succeeded.\n'
