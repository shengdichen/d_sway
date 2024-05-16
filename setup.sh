#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

WALLPAPER_PATH="${HOME}/xdg/MDA/Pic/wallpapers"
ADHOC_PATH="${SCRIPT_PATH}/.config/sway/conf/components/adhoc"

__stow() {
    mkdir -p "${WALLPAPER_PATH}"

    (
        cd .. && stow -R "$(basename "${SCRIPT_PATH}")"
    )
}

__wallpaper() {
    local _choice=""
    local _need_update=""
    (
        cd "${WALLPAPER_PATH}" || exit 3
        case "${1}" in
            "select")
                printf "\n"
                printf "select wallpaper: "
                printf "\n"
                _choice="$(find "." -type f | fzf --reverse --height=37%)"
                _need_update="yes"
                ;;
            *)
                _choice="Leopard_Server.jpg"
                ;;
        esac
        _choice="$(realpath "${_choice}")"

        cd "${ADHOC_PATH}" || exit 3
        local _link="wallpaper"
        if [ "${_need_update}" ] || ! [ -e "${_link}" ]; then
            ln -s -f "${_choice}" "${_link}"
        fi
    )
}

__adhoc() {
    local _conf="current.conf"
    (
        cd "${ADHOC_PATH}" || exit 3
        if [ ! -e "${_conf}" ]; then
            touch "${_conf}"
        fi
    )
}

main() {
    __stow
    __wallpaper "${@}"
    __adhoc

    unset SCRIPT_PATH WALLPAPER_PATH ADHOC_PATH
    unset -f __stow __wallpaper
}
main "${@}"
unset -f main
