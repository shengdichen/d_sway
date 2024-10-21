#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

DIR_HYPR="${HOME}/.config/hypr"
CURRENT_CONF="current.conf"

__mkdir() {
    mkdir -p "${DIR_HYPR}"
    mkdir -p "${HOME}/.config/river"
    mkdir -p "${HOME}/.config/niri"
}

__adhoc() {
    local _d _conf
    for _d in "${DIR_HYPR}" "${HOME}/.config/sway/conf/components"; do
        _d="${_d}/adhoc"
        mkdir -p "${_d}"
        _conf="${_d}/${CURRENT_CONF}"
        [ ! -h "${_conf}" ] && [ ! -e "${_conf}" ] && touch "${_conf}"
    done
}

__stow() {
    (
        cd .. && stow -R "$(basename "${SCRIPT_PATH}")"
    )
    (
        cd "${DIR_HYPR}" && ln -s -f "${SCRIPT_PATH}/src/py/src" .
    )
}

__wallpaper() {
    "${SCRIPT_PATH}/.local/script/wallpaper.sh"
}

main() {
    __mkdir
    __adhoc
    __stow
    __wallpaper
}
main "${@}"
