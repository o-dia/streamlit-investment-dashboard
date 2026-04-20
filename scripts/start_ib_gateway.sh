#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEFAULT_GATEWAY_DIR="${HOME}/Applications/clientportal.gw"
ENV_FILE="${REPO_ROOT}/.env"

read_env_value() {
    local key="$1"
    local file="$2"

    if [[ ! -f "${file}" ]]; then
        return 1
    fi

    awk -F= -v target="${key}" '
        $1 == target {
            sub(/^[[:space:]]+/, "", $2)
            sub(/[[:space:]]+$/, "", $2)
            print $2
            exit
        }
    ' "${file}"
}

expand_home() {
    local value="$1"
    if [[ "${value}" == "~" ]]; then
        printf '%s\n' "${HOME}"
    elif [[ "${value}" == "~/"* ]]; then
        printf '%s/%s\n' "${HOME}" "${value#~/}"
    else
        printf '%s\n' "${value}"
    fi
}

gateway_dir="${IB_GATEWAY_DIR:-}"

if [[ -z "${gateway_dir}" ]]; then
    gateway_dir="$(read_env_value "IB_GATEWAY_DIR" "${ENV_FILE}" || true)"
fi

if [[ -z "${gateway_dir}" ]]; then
    gateway_dir="${DEFAULT_GATEWAY_DIR}"
fi

gateway_dir="${gateway_dir%\"}"
gateway_dir="${gateway_dir#\"}"
gateway_dir="${gateway_dir%\'}"
gateway_dir="${gateway_dir#\'}"
gateway_dir="$(expand_home "${gateway_dir}")"
config_path="${1:-./root/conf.yaml}"

if [[ ! -d "${gateway_dir}" ]]; then
    echo "IB gateway directory not found: ${gateway_dir}" >&2
    echo "Set IB_GATEWAY_DIR in .env or install the gateway at ${DEFAULT_GATEWAY_DIR}" >&2
    exit 1
fi

if [[ ! -x "${gateway_dir}/bin/run.sh" ]]; then
    echo "Gateway launcher not found: ${gateway_dir}/bin/run.sh" >&2
    exit 1
fi

echo "Starting IB Client Portal Gateway from: ${gateway_dir}"
echo "Using config: ${config_path}"

cd "${gateway_dir}"
exec ./bin/run.sh "${config_path}"
