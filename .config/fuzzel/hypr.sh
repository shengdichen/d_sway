#!/usr/bin/env dash

WORKSPACE_HOLD="special:HOLD"

__workspaces() {
    hyprctl -j workspaces | jq --raw-output ".[] | .name" | fzf --reverse
}

__workspace_curr() {
    hyprctl -j activeworkspace | jq --raw-output ".name"
}

__is_workspace_hold() {
    # NOTE:
    #   must use |activewindow|, since |activeworkspace| returns non-special workspaces only
    [ "$(hyprctl -j activewindow | jq --raw-output ".workspace.name")" = "${WORKSPACE_HOLD}" ]
}

__window_active() {
    # NOTE:
    #   focusHistoryID == 0
    # NOTE:
    # alternative implementation:
    #   hyprctl -j activeworkspace | jq --raw-output ".lastwindow"

    hyprctl -j activewindow | jq --raw-output ".address"
}

__window_previous() {
    # NOTE:
    #   focusHistoryID == 1

    hyprctl -j clients | jq --raw-output ".[] | select (.focusHistoryID == 1) | .address"
}

__is_empty_workspace() {
    # NOTE:
    #   highly finicky: returns 0 or 1

    [ "$(hyprctl -j activeworkspace | jq --raw-output ".windows")" -lt 2 ]
}

__fzf() {
    local _multi="${1}"
    if [ "${_multi}" ]; then
        fzf --reverse --multi
    else
        fzf --reverse
    fi
}

__windows_by_title() {
    local _multi=""
    if [ "${1}" = "--multi" ]; then
        shift
        _multi="yes"
    fi

    __escape_for_regex() {
        # escape:
        #   [ ] ( ) . * ^ $
        # with (prepended) \ since hyprland ONLY accepts regex for title

        # REF:
        #   https://www.gnu.org/software/sed/manual/html_node/Character-Classes-and-Bracket-Expressions.html
        local _char_class_to_escape="][().?+*^$" # ] must be first in char-class
        sed "s/\([${_char_class_to_escape}]\)/\\\\\1/g"
    }

    __match_exact() {
        sed "s/\(.*\)/^\1$/"
    }

    hyprctl -j clients |
        jq --raw-output ".[] | .title" |
        grep --invert-match "throwaway" |
        __fzf "${_multi}" |
        __escape_for_regex |
        __match_exact |
        while read -r _line; do
            printf "title:%s\n" "${_line}"
        done
}

__windows_by_addr() {
    local _multi=""
    if [ "${1}" = "--multi" ]; then
        shift
        _multi="yes"
    fi

    hyprctl -j clients |
        jq --raw-output ".[] | select (.workspace.name == \"${WORKSPACE_HOLD}\") | [.title, .address] | \"\(.[0])  [__ADDR__: \(.[1])]\"" |
        grep --invert-match "throwaway" |
        __fzf "${_multi}" |
        sed "s/^.*\[__ADDR__: \(.*\)\]$/\1/"
}

__is_grouped() {
    [ "$(hyprctl -j clients | jq --raw-output ".[] | select (.address == \"${1}\") | .grouped")" != "[]" ]
}

__windows_grouped() {
    hyprctl -j clients | jq --raw-output ".[] | select (.grouped != []) | .address"
}

__engroup() {
    if __is_grouped "${1}"; then
        return
    fi

    hyprctl dispatch focuswindow "address:${1}"
    local _dir
    for _dir in "l" "r" "u" "d"; do
        hyprctl dispatch moveintogroup "${_dir}"
        if __is_grouped "${1}"; then
            break
        fi
    done
    if ! __is_grouped "${1}"; then
        printf "hypr> still NOT grouped [%s]\n" "${1}"
        read -r _
    fi
    hyprctl dispatch focuscurrentorlast
}

__degroup() {
    if ! __is_grouped "${1}"; then
        return
    fi
    hyprctl dispatch moveoutofgroup "address:${1}"
    hyprctl dispatch focuscurrentorlast # |moveoutofgroup| will auto-focus the workspace
}

__move_window_to_workspace() {
    # NOTE:
    #   not suitable for (batch-) moving multiple windows

    __degroup "${1}"
    hyprctl dispatch movetoworkspace "${2},address:${1}"
}

__move_window_to_workspace_no_switch() {
    __degroup "${1}"
    hyprctl dispatch movetoworkspacesilent "${2},address:${1}"
}

__move_window_to_hold() {
    __degroup "${1}"
    __move_window_to_workspace_no_switch "${1}" "${WORKSPACE_HOLD}"
    __engroup "${1}"
}

__main() {
    if [ "${1}" = "--to-hold" ]; then
        shift
        if __is_workspace_hold; then
            return
        fi
        __move_window_to_hold "$(__window_active)"
        return
    fi

    local _mode="append"
    if ! __is_empty_workspace; then
        while true; do
            printf "hypr> mode? [r]eplace (default); [a]ppend "
            read -r _mode
            case "${_mode}" in
                "r" | "R" | "")
                    _mode="replace"
                    break
                    ;;
                "a" | "A")
                    _mode="append"
                    break
                    ;;
                *)
                    printf "hypr> huh? aka, what is [%s]?\n\n" "${_mode}"
                    ;;
            esac
        done
    fi

    local _ws
    _ws="$(__workspace_curr)"
    case "${_mode}" in
        "append")
            local _win
            __windows_by_addr --multi | while read -r _win; do
                __move_window_to_workspace_no_switch "${_win}" "${_ws}"
            done
            ;;
        "replace")
            local _w_curr
            _w_curr="$(__window_previous)"

            local _win
            _win="$(__windows_by_addr)"
            if [ ! "${_win}" ]; then
                exit 3
            fi
            __move_window_to_workspace "${_win}" "${_ws}"
            __move_window_to_hold "${_w_curr}"
            ;;
    esac
}
__main "${@}"
