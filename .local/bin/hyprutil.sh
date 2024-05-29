#!/usr/bin/env dash

__run_float() {
    hyprctl dispatch -- exec "[float]" footclient --title "throwaway" -- "${@}"
}

__run() {
    hyprctl dispatch -- exec footclient --title "throwaway" -- "${@}"
}
