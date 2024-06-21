#!/usr/bin/env dash

__nohup() {
    nohup "${@}" 1>/dev/null 2>&1 &
}

__kill() {
    pkill -f "${@}"
}

__cmd_layout() {
    riverctl send-layout-cmd rivertile "${*}"
}
