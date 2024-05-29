#!/usr/bin/env dash

__run_float() {
    hyprctl dispatch exec "[float]" footclient "${@}"
}

__run() {
    hyprctl dispatch exec footclient "${@}"
}
