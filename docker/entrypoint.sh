#!/usr/bin/env bash
set -e
source /opt/ros/noetic/setup.bash
if [[ -f /root/mm_husky_ws/devel/setup.bash ]]; then
    source /root/mm_husky_ws/devel/setup.bash
fi
export PYTHONPATH="/root/mm_husky_ws/src/modulation_rl/scripts${PYTHONPATH:+:$PYTHONPATH}"
export GAZEBO_MODEL_PATH="/root/mm_husky_ws/src/modulation_rl/gazebo_models:/usr/share/gazebo-11/models${GAZEBO_MODEL_PATH:+:$GAZEBO_MODEL_PATH}"
export GAZEBO_RESOURCE_PATH="/root/mm_husky_ws/src/modulation_rl/gazebo_world/worlds:/usr/share/gazebo-11${GAZEBO_RESOURCE_PATH:+:$GAZEBO_RESOURCE_PATH}"
exec "$@"
