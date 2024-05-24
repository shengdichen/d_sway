#!/usr/bin/env dash

__base() {
    riverctl map normal Super Return spawn foot

    # Super+Q to close the focused view
    riverctl map normal Super Q close

    # Super+Shift+E to exit river
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
    riverctl map normal Super Period focus-output next
    riverctl map normal Super Comma focus-output previous

    # Super+Shift+{Period,Comma} to send the focused view to the next/previous output
    riverctl map normal Super+Shift Period send-to-output next
    riverctl map normal Super+Shift Comma send-to-output previous
}
__navigate

__layout() {
    # Super+Return to bump the focused view to the top of the layout stack
    riverctl map normal Super+Shift Return zoom

    riverctl map normal Super+Shift H send-layout-cmd rivertile "main-ratio -0.05"
    riverctl map normal Super+Shift L send-layout-cmd rivertile "main-ratio +0.05"

    # riverctl map normal Super+Shift H send-layout-cmd rivertile "main-count +1"
    # riverctl map normal Super+Shift L send-layout-cmd rivertile "main-count -1"

    # Super+{Up,Right,Down,Left} to change layout orientation
    riverctl map normal Super Up send-layout-cmd rivertile "main-location top"
    riverctl map normal Super Right send-layout-cmd rivertile "main-location right"
    riverctl map normal Super Down send-layout-cmd rivertile "main-location bottom"
    riverctl map normal Super Left send-layout-cmd rivertile "main-location left"
}
__layout

__view() {
    # Super+Alt+{H,J,K,L} to move views
    riverctl map normal Super+Alt H move left 100
    riverctl map normal Super+Alt J move down 100
    riverctl map normal Super+Alt K move up 100
    riverctl map normal Super+Alt L move right 100

    # Super+Alt+Control+{H,J,K,L} to snap views to screen edges
    riverctl map normal Super+Alt+Control H snap left
    riverctl map normal Super+Alt+Control J snap down
    riverctl map normal Super+Alt+Control K snap up
    riverctl map normal Super+Alt+Control L snap right

    # Super+Alt+Shift+{H,J,K,L} to resize views
    riverctl map normal Super+Alt+Shift H resize horizontal -100
    riverctl map normal Super+Alt+Shift J resize vertical 100
    riverctl map normal Super+Alt+Shift K resize vertical -100
    riverctl map normal Super+Alt+Shift L resize horizontal 100

    # Super + Left Mouse Button to move views
    riverctl map-pointer normal Super BTN_LEFT move-view

    # Super + Right Mouse Button to resize views
    riverctl map-pointer normal Super BTN_RIGHT resize-view

    # Super + Middle Mouse Button to toggle float
    riverctl map-pointer normal Super BTN_MIDDLE toggle-float
}
__view

__tags() {
    local tags
    for i in $(seq 1 9); do
        tags="$((1 << (i - 1)))"

        # tags to show
        riverctl map normal Super "${i}" set-focused-tags "${tags}"

        # Super+Shift+[1-9] to tag focused view with tag [0-8]
        riverctl map normal Super+Shift "${i}" set-view-tags "${tags}"

        # Super+Control+[1-9] to toggle focus of tag [0-8]
        riverctl map normal Super+Control "${i}" toggle-focused-tags "${tags}"

        # Super+Shift+Control+[1-9] to toggle tag [0-8] of focused view
        riverctl map normal Super+Shift+Control "${i}" toggle-view-tags "${tags}"
    done

    # Super+0 to focus all tags
    # Super+Shift+0 to tag focused view with all tags
    local all_tags="$(((1 << 32) - 1))"
    riverctl map normal Super 0 set-focused-tags "${all_tags}"
    riverctl map normal Super+Shift 0 set-view-tags "${all_tags}"
}
__tags

__passthrough() {
    riverctl declare-mode passthrough
    riverctl map normal Super F12 enter-mode passthrough
    riverctl map passthrough Super F12 enter-mode normal
}
__passthrough

__misc() {
    riverctl map normal Super F toggle-float
    riverctl map normal Super grave toggle-fullscreen

    local mode
    # Various media key mapping examples for both normal and locked mode which do
    # not have a modifier
    for mode in "normal" "locked"; do
        # Eject the optical drive (well if you still have one that is)
        riverctl map "${mode}" None XF86Eject spawn 'eject -T'

        # Control pulse audio volume with pamixer (https://github.com/cdemoulins/pamixer)
        riverctl map "${mode}" None XF86AudioRaiseVolume spawn 'pamixer -i 5'
        riverctl map "${mode}" None XF86AudioLowerVolume spawn 'pamixer -d 5'
        riverctl map "${mode}" None XF86AudioMute spawn 'pamixer --toggle-mute'

        # Control MPRIS aware media players with playerctl (https://github.com/altdesktop/playerctl)
        riverctl map "${mode}" None XF86AudioMedia spawn 'playerctl play-pause'
        riverctl map "${mode}" None XF86AudioPlay spawn 'playerctl play-pause'
        riverctl map "${mode}" None XF86AudioPrev spawn 'playerctl previous'
        riverctl map "${mode}" None XF86AudioNext spawn 'playerctl next'

        # Control screen backlight brightness with brightnessctl (https://github.com/Hummer12007/brightnessctl)
        riverctl map "${mode}" None XF86MonBrightnessUp spawn 'brightnessctl set +5%'
        riverctl map "${mode}"None XF86MonBrightnessDown spawn 'brightnessctl set 5%-'
    done
}

__visual() {
    local COLOR_GREY_DARK="2b272f" COLOR_GREY_BRIGHT="97879f" COLOR_WHITE="efe3fb"
    riverctl background-color "0x${COLOR_GREY_DARK}7f"

    riverctl border-width 2
    riverctl border-color-urgent "0x${COLOR_WHITE}7f"
    riverctl border-color-focused "0x${COLOR_GREY_BRIGHT}"
    riverctl border-color-unfocused "0x${COLOR_GREY_DARK}7f"

    riverctl xcursor-theme capitaine-cursors 24
    riverctl hide-cursor when-typing enabled
    riverctl hide-cursor timeout 3700
}
__visual

# Set keyboard repeat rate
riverctl set-repeat 50 300

# Make all views with an app-id that starts with "float" and title "foo" start floating.
riverctl rule-add -app-id 'float*' -title 'foo' float

# Make all views with app-id "bar" and any title use client-side decorations
riverctl rule-add -app-id "bar" csd
