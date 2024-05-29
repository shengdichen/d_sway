#!/usr/bin/env dash

__run_float() {
    hyprctl dispatch exec "[float]" foot "${@}"
}

__run() {
    hyprctl dispatch exec foot "${@}"
}
