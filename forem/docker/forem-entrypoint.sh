#!/usr/bin/env bash
# FoReM container entrypoint (bind-mounted read-only; used via --entrypoint / docker exec).
# Unlike the image's mm-entrypoint it does not add the old modulation_rl paths.
set -e
# exec runs as the host uid (see run.sh) so build/log files stay owned by the host user.
export HOME="${HOME:-/tmp/forem-home}"
[[ -w "$HOME" ]] || export HOME=/tmp/forem-home
mkdir -p "$HOME"
# Sourced setup scripts must not see the command's arguments (catkin's setup.bash forwards "$@").
cmd=("$@")
set --
source /opt/ros/noetic/setup.bash
if [[ -f /root/mm_husky_ws/devel/setup.bash ]]; then
    source /root/mm_husky_ws/devel/setup.bash
fi
# Offline: do not query the online Gazebo model database.
export GAZEBO_MODEL_DATABASE_URI=""
exec "${cmd[@]}"
