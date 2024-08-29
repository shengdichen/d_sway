#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

. "${HOME}/.local/lib/util.sh"

__make() {
    local _default="${HOME}/xyz/MDA/Pic/wallpapers/Leopard_Server.jpg" _link="wallpaper"

    local _wm
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
    local _wm
    while [ "${#}" -gt 0 ]; do
        case "${1}" in
        "--wm")
            _wm="${2}"
            shift 2
            ;;
        "--")
            shift && break
            ;;
        esac
    done

    if [ ! "${_wm}" ]; then
        _wm="$(__fzf_opts "hypr" "niri" "river")"
    fi

    local _path="${HOME}/.config/${_wm}/wallpaper"
    __pkill "swaybg -m fill -i ${_path}"
    __nohup swaybg -m fill -i "${_path}"
}

__make
__wallpaper "${@}"
