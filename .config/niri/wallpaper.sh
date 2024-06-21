#!/usr/bin/env dash

SCRIPT_PATH="$(realpath "$(dirname "${0}")")"
cd "${SCRIPT_PATH}" || exit 3

. "../river/util.sh"

__wallpaper() {
    local _path="${HOME}/.config/niri/wallpaper"
    __kill "swaybg -m fill -i ${_path}"
    __nohup swaybg -m fill -i "${_path}"
}
__wallpaper
