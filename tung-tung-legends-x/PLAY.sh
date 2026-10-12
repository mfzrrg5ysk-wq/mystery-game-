#!/bin/sh
set -eu
task_game_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$(uname -m)" != "x86_64" ]; then
    echo "This portable executable requires an Intel/AMD x86-64 Linux Chromebook."
    echo "For ARM Linux, follow the source instructions in README.md."
    exit 1
fi
exec "$task_game_dir/TungTungLegendsX/TungTungLegendsX" "$@"
