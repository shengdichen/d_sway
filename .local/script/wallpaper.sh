#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

WALLPAPER_DIR="$(realpath "$(xdg-user-dir PICTURES)/wallpapers")"
LINK_NAME="wallpaper"

. "${HOME}/.local/lib/util.sh"

__link() {
    local _force=""
    if [ "${1}" = "--force" ]; then
        _force="yes"
        shift
    fi

    local _wm="${1}" _wp="${2}"
    (
        cd "${HOME}/.config/${_wm}/" || exit 3
        if [ "${_force}" ] || [ ! -e "./${LINK_NAME}" ]; then
            ln -s -f "${_wp}" "${LINK_NAME}"
        fi
    )
}

__show() {
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

__use_default() {
    local _wp="${WALLPAPER_DIR}/Leopard_Server.jpg"

    local _wm
    for _wm in "hypr" "sway/conf/components/adhoc" "niri" "river"; do
        __link "${_wm}" "${_wp}"
    done
}

__select() {
    local _wm _wp
    while [ "${#}" -gt 0 ]; do
        case "${1}" in
            "--wm")
                _wm="${2}"
                shift 2
                ;;
            "--wp")
                _wp="${2}"
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

    if [ "${_wp}" ]; then
        __link --force "${_wm}" "${_wp}"
        __show --wm "${_wm}"
        return
    fi

    while true; do
        printf "wallpaper> select: "
        _wp="${WALLPAPER_DIR}/$(find "${WALLPAPER_DIR}" -mindepth 1 -printf "%P\n" | sort -n | __fzf)"

        imv -- "${_wp}"
        if __yes_or_no "wallpaper> use?"; then
            __link --force "${_wm}" "${_wp}"
            break
        fi
    done
    __show --wm "${_wm}"
}

case "${1}" in
    "select")
        shift
        __select "${@}"
        ;;
    "show")
        shift
        __use_default
        __show "${@}"
        ;;
    *)
        __use_default
        ;;
esac
