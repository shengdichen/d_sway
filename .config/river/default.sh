#!/usr/bin/env dash

__base() {
    riverctl map normal Super Return spawn \
        "foot --config ${HOME}/.config/foot/foot_alpha.ini"
    riverctl map normal Super Q close
    riverctl map normal Super+Shift E exit
}
__base

__navigate() {
    # focus
    riverctl map normal Super J focus-view next
    riverctl map normal Super K focus-view previous

    # displace
    riverctl map normal Super+Shift J swap next
    riverctl map normal Super+Shift K swap previous

    # focus, output
    riverctl map normal Super Left focus-output next
    riverctl map normal Super Right focus-output previous

    # Super+Shift+{Period,Comma} to send the focused view to the next/previous output
    riverctl map normal Super+Shift Left send-to-output next
    riverctl map normal Super+Shift Right send-to-output previous
}
__navigate

__layout() {
    # Super+Return to bump the focused view to the top of the layout stack
    riverctl map normal Super+Shift Return zoom

    # +0.05
    riverctl map normal Super+Alt H send-layout-cmd rivertile "main-ratio 0.33"
    riverctl map normal Super+Alt L send-layout-cmd rivertile "main-ratio 0.67"

    riverctl map normal Super+Alt K send-layout-cmd rivertile "main-count -1"
    riverctl map normal Super+Alt J send-layout-cmd rivertile "main-count +1"

    riverctl map normal Super+Alt Up send-layout-cmd rivertile "main-location top"
    riverctl map normal Super+Alt Right send-layout-cmd rivertile "main-location right"
    riverctl map normal Super+Alt Down send-layout-cmd rivertile "main-location bottom"
    riverctl map normal Super+Alt Left send-layout-cmd rivertile "main-location left"
}
__layout

__float() {
    # riverctl map normal Super+Alt H move left 100
    # riverctl map normal Super+Alt J move down 100
    # riverctl map normal Super+Alt K move up 100
    # riverctl map normal Super+Alt L move right 100

    # # snap edge of view to edge of screen
    # riverctl map normal Super+Alt+Control H snap left
    # riverctl map normal Super+Alt+Control J snap down
    # riverctl map normal Super+Alt+Control K snap up
    # riverctl map normal Super+Alt+Control L snap right

    # riverctl map normal Super+Alt+Shift H resize horizontal -100
    # riverctl map normal Super+Alt+Shift J resize vertical 100
    # riverctl map normal Super+Alt+Shift K resize vertical -100
    # riverctl map normal Super+Alt+Shift L resize horizontal 100

    riverctl map-pointer normal Super BTN_LEFT move-view
    riverctl map-pointer normal Super BTN_RIGHT resize-view
    riverctl map-pointer normal Super BTN_MIDDLE toggle-float
}
__float

__tags() {
    local _tag
    for i in $(seq 1 9); do
        _tag="$((1 << (i - 1)))"

        # reset: show this tag only
        riverctl map normal Super "${i}" set-focused-tags "${_tag}"

        # toggle visibility of this tag
        riverctl map normal Super+Control "${i}" toggle-focused-tags "${_tag}"

        # for view: reset to this tag only
        riverctl map normal Super+Shift "${i}" set-view-tags "${_tag}"

        # for view: toggle this tag
        riverctl map normal Super+Shift+Control "${i}" toggle-view-tags "${_tag}"
    done

    local _all_tags="$(((1 << 32) - 1))"
    # show all tags
    riverctl map normal Super 0 set-focused-tags "${_all_tags}"
    # for view: enable all tags
    riverctl map normal Super+Shift 0 set-view-tags "${_all_tags}"

    riverctl map normal Super Tab focus-previous-tags
    riverctl map normal Super+Shift Tab send-to-previous-tags
}
__tags

__passthrough() {
    riverctl declare-mode passthrough
    riverctl map normal Super F12 enter-mode passthrough
    riverctl map passthrough Super F12 enter-mode normal
}
__passthrough

__misc() {
    riverctl map normal Super G toggle-float
    riverctl map normal Super grave toggle-fullscreen

    # local mode
    # # Various media key mapping examples for both normal and locked mode which do
    # # not have a modifier
    # for mode in "normal" "locked"; do
    #     # Eject the optical drive (well if you still have one that is)
    #     riverctl map "${mode}" None XF86Eject spawn 'eject -T'

    #     # Control pulse audio volume with pamixer (https://github.com/cdemoulins/pamixer)
    #     riverctl map "${mode}" None XF86AudioRaiseVolume spawn 'pamixer -i 5'
    #     riverctl map "${mode}" None XF86AudioLowerVolume spawn 'pamixer -d 5'
    #     riverctl map "${mode}" None XF86AudioMute spawn 'pamixer --toggle-mute'

    #     # Control MPRIS aware media players with playerctl (https://github.com/altdesktop/playerctl)
    #     riverctl map "${mode}" None XF86AudioMedia spawn 'playerctl play-pause'
    #     riverctl map "${mode}" None XF86AudioPlay spawn 'playerctl play-pause'
    #     riverctl map "${mode}" None XF86AudioPrev spawn 'playerctl previous'
    #     riverctl map "${mode}" None XF86AudioNext spawn 'playerctl next'

    #     # Control screen backlight brightness with brightnessctl (https://github.com/Hummer12007/brightnessctl)
    #     riverctl map "${mode}" None XF86MonBrightnessUp spawn 'brightnessctl set +5%'
    #     riverctl map "${mode}"None XF86MonBrightnessDown spawn 'brightnessctl set 5%-'
    # done
}
__misc

__visual() {
    local COLOR_BLACK="000000"
    local COLOR_GREY_DARK="2b272f"
    local COLOR_GREY_BRIGHT="97879f"
    local COLOR_WHITE="efe3fb"

    riverctl background-color "0x${COLOR_GREY_DARK}"

    riverctl border-width 3
    riverctl border-color-unfocused "0x${COLOR_BLACK}e7"
    riverctl border-color-focused "0x${COLOR_GREY_BRIGHT}"
    riverctl border-color-urgent "0x${COLOR_WHITE}"

    riverctl xcursor-theme capitaine-cursors 24
    riverctl hide-cursor when-typing enabled
    riverctl hide-cursor timeout 3700
}
__visual

__rule() {
    riverctl rule-add ssd

    # Make all views with an app-id that starts with "float" and title "foo" start floating.
    riverctl rule-add -app-id 'float*' -title 'foo' float
}
__rule

__input() {
    # $ riverctl list-inputs
    # $ riverctl list-input-configs

    riverctl keyboard-layout \
        -options "caps:escape,grp:win_space_toggle,lv2:lsgt_switch" \
        "us,ch(fr),ru(phonetic)"
    # keyboard repeat-rate
    riverctl set-repeat 50 300

    riverctl input "pointer-*" accel-profile flat
    riverctl input "pointer-*" pointer-accel 2.0
    riverctl input "pointer-*" scroll-factor 1.0
    riverctl input "pointer-*" middle-emulation disabled
    riverctl input "pointer-*" disable-while-typing enabled
    riverctl input "pointer-*" disable-while-trackpointing enabled
    riverctl input "pointer-*" tap enabled

    local _touchpad="pointer-1739-0-Synaptics_TM3625-010"
    riverctl input "${_touchpad}" natural-scroll enabled
}
__input
