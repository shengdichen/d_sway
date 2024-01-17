#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

make_wallpaper() {
    local _wallpapers_path="${SCRIPT_PATH}/.config/sway/conf/general/components/output/wallpapers"
    (
        cd "${_wallpapers_path}" || exit 3

        case "${1}" in
            "select")
                printf "\n"
                printf "select wallpaper: "
                printf "\n"
                _current="$(find "." -type f | fzf --reverse --height=37%)"
                ;;
            *)
                _current="Leopard_Server.jpg"
                ;;
        esac

        ln -s -f "${_current}" "current"
    )
}

main() {
    make_wallpaper "${@}"
    unset -f make_wallpaper
}
main "${@}"
unset -f main
