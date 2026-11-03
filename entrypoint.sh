#!/bin/sh
set -e

# Start a virtual display so headed mode works with no physical monitor.
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset >/dev/null 2>&1 &
XVFB_PID=$!

# Wait for the X socket to actually appear.
i=0
while [ ! -e /tmp/.X11-unix/X99 ]; do
    i=$((i + 1))
    if [ "$i" -gt 20 ]; then
        echo "Xvfb failed to start" >&2
        exit 1
    fi
    sleep 0.5
done

export DISPLAY=:99
trap 'kill "$XVFB_PID" 2>/dev/null || true' EXIT INT TERM

exec python3 main.py --headed "$@"
