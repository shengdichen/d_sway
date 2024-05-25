#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

. "./util.sh"

__wallpaper() {
    local _path="${HOME}/.config/river/wallpaper"
    __nohup swaybg -m fill -i "${_path}"
}
__wallpaper
