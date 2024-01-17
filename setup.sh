#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

make_wallpaper() {
    local _wallpapers_path="${SCRIPT_PATH}/.config/sway/conf/general/components/output/wallpapers"
    local _current="Leopard_Server.jpg"

    (
        cd "${_wallpapers_path}" || exit 3
        ln -s -f "${_current}" "current"
    )
}

main() {
    make_wallpaper
    unset -f make_wallpaper
}
main
unset -f main
