#!/usr/bin/env dash

__workspaces() {
    hyprctl -j workspaces | jq --raw-output ".[] | .name" | fzf --reverse
}

__workspace_curr() {
    hyprctl -j activeworkspace | jq --raw-output ".name"
}

__titles() {
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
        fzf --multi --reverse |
        __escape_for_regex |
        __match_exact
}

__main() {
    local _ws
    _ws="$(__workspace_curr)"

    local _title
    __titles | while read -r _title; do
        hyprctl dispatch movetoworkspace "${_ws}",title:"${_title}"
    done
}
__main
