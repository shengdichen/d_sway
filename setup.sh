#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

DIR_HYPR="${HOME}/.config/hypr"
DIR_SWAY="${HOME}/.config/sway"
CURRENT_CONF="current.conf"

__mkdir() {
    mkdir -p "${DIR_HYPR}"
    mkdir -p "${HOME}/.local/state/hypr"
    mkdir -p "${DIR_SWAY}"
    mkdir -p "${HOME}/.local/state/sway"

    mkdir -p "${HOME}/.config/river"
    mkdir -p "${HOME}/.config/niri"
}

__adhoc() {
    local _d _conf
    for _d in "${DIR_HYPR}" "${DIR_SWAY}/conf"; do
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

    find "./src/py/src" -type d | grep "__pycache__$" | while read -r _d; do
        rm -r -- "${_d}" # will otherwise cause stow-conflict
    done
    (
        cd "./src/py/src" || exit 3
        mkdir -p "${DIR_HYPR}/src/common"
        stow -R --target "${DIR_HYPR}/src/common" "common"
        mkdir -p "${DIR_HYPR}/src/hyprland"
        stow -R --target "${DIR_HYPR}/src/hyprland" "hyprland"
        ln -srf "$(realpath "./hyprland.py")" "${DIR_HYPR}/src/."
    )
    (
        cd "./src/py/src" || exit 3
        mkdir -p "${DIR_SWAY}/src/common"
        stow -R --target "${DIR_SWAY}/src/common" "common"
        mkdir -p "${DIR_SWAY}/src/sway"
        stow -R --target "${DIR_SWAY}/src/sway" "sway"
        ln -srf "$(realpath "./sway.py")" "${DIR_SWAY}/src/."
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
