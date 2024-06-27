#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

. "${HOME}/.local/lib/util.sh"

__make() {
    local _default="${HOME}/xyz/MDA/Pic/wallpapers/Leopard_Server.jpg" _link="wallpaper"

    for _wm in "hypr" "niri" "river"; do
        (
            cd "${HOME}/.config/${_wm}/" || exit 3
            if [ ! -e "./${_link}" ]; then
                ln -s "${_default}" "${_link}"
            fi
        )
    done
}

__wallpaper() {
    local _choice
    _choice="$(
        for _wm in "hypr" "niri" "river"; do
            printf "%s\n" "${_wm}"
        done | __fzf
    )"

    if [ "${_choice}" ]; then
        local _path="${HOME}/.config/${_choice}/wallpaper"
        __pkill "swaybg -m fill -i ${_path}"
        __nohup swaybg -m fill -i "${_path}"
    fi
}

__make
__wallpaper
