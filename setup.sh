#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

make_wallpaper() {
    local _wallpapers_path="${SCRIPT_PATH}/.config/sway/conf/general/components/output/wallpapers"
    local linkname="current"
    local _select=""
    (
        cd "${_wallpapers_path}" || exit 3

        case "${1}" in
            "select")
                printf "\n"
                printf "select wallpaper: "
                printf "\n"
                _current="$(find "." -type f | fzf --reverse --height=37%)"
                _select="yes"
                ;;
            *)
                _current="Leopard_Server.jpg"
                ;;
        esac

        if [ "${_select}" ] || ! [ -e "${linkname}" ]; then
            ln -s -f "${_current}" "current"
        fi
    )
}

__stow() {
    (
        cd .. && stow -R "$(basename "${SCRIPT_PATH}")"
    )
}

main() {
    make_wallpaper "${@}"
    __stow

    unset SCRIPT_PATH
    unset -f make_wallpaper __stow
}
main "${@}"
unset -f main
