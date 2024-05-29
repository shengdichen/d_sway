#!/usr/bin/env dash

__workspaces() {
    hyprctl -j workspaces | jq --raw-output ".[] | .name" | fzf --reverse
}

__workspace_curr() {
    hyprctl -j activeworkspace | jq --raw-output ".name"
}

__window_active() {
    # NOTE:
    #   focusHistoryID == 0
    # NOTE:
    # alternative implementation:
    #   printf "address:%s\n" "$(hyprctl -j activeworkspace | jq --raw-output ".lastwindow")"

    printf "address:%s\n" "$(hyprctl -j activewindow | jq --raw-output ".address")"
}

__window_previous() {
    # NOTE:
    #   focusHistoryID == 1

    printf "address:%s\n" "$(
        hyprctl -j clients |
            jq --raw-output ".[] | select (.focusHistoryID == 1) | .address"
    )"
}

__titles() {
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

    __fzf() {
        if [ "${_multi}" ]; then
            fzf --reverse --multi
        else
            fzf --reverse
        fi
    }

    hyprctl -j clients |
        jq --raw-output ".[] | .title" |
        grep --invert-match "throwaway" |
        __fzf |
        __escape_for_regex |
        __match_exact |
        while read -r _line; do
            printf "title:%s\n" "${_line}"
        done
}

__move_window_to_workspace() {
    hyprctl dispatch movetoworkspace "${2}","${1}"
}

__move_window_to_workspace_no_switch() {
    hyprctl dispatch movetoworkspacesilent "${2}","${1}"
}

__move_window_to_hold() {
    __move_window_to_workspace_no_switch "${1}" "special:HOLD"
}

__main() {
    local _mode=""
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

    local _ws
    _ws="$(__workspace_curr)"
    case "${_mode}" in
        "append")
            local _title
            __titles --multi | while read -r _title; do
                __move_window_to_workspace "${_title}" "${_ws}"
            done
            ;;
        "replace")
            local _w_curr
            _w_curr="$(__window_previous)"

            local _title
            _title="$(__titles)"
            __move_window_to_workspace "${_title}" "${_ws}"
            __move_window_to_hold "${_w_curr}"
            ;;
    esac
}
__main "${@}"
