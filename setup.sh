#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

WALLPAPER_PATH="${HOME}/xdg/MDA/Pic/wallpapers"

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

        cd "${SCRIPT_PATH}/.config/sway/conf/components/adhoc/" || exit 3
        local _link="wallpaper"
        if [ "${_need_update}" ] || ! [ -e "${_link}" ]; then
            ln -s -f "${_choice}" "${_link}"
        fi
    )
}

main() {
    __stow
    __wallpaper "${@}"

    unset SCRIPT_PATH WALLPAPER_PATH
    unset -f __stow __wallpaper
}
main "${@}"
unset -f main
